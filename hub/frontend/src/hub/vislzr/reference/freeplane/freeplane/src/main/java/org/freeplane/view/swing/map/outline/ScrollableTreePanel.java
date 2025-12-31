package org.freeplane.view.swing.map.outline;

import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.KeyboardFocusManager;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.Collection;
import java.util.List;
import java.util.function.Supplier;

import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.SwingUtilities;

import org.freeplane.core.resources.IFreeplanePropertyListener;
import org.freeplane.core.resources.ResourceController;
import org.freeplane.main.application.AuxillaryEditorSplitPane;

class ScrollableTreePanel extends JPanel implements OutlineActionTarget {

	enum ScrollMode {
		SINGLE_ITEM,
		SIBLINGS
	}

	private static final long serialVersionUID = 1;
    private static final int BLOCK_SIZE = 50;

    private  final NavigationButtons navButtons;
    private final BreadcrumbPanel breadcrumbPanel;
    private final ExpansionControls expansionControls;
    private OutlineViewport viewport;
    private final JPanel blockPanel;

    private TreeNode root;
    private final OutlineSelection outlineSelection;
    private final VisibleOutlineNodes visibleNodes;
    private final OutlineGeometry.GeometryListener geometryListener;
    private boolean geometryListenerRegistered;
    private final IFreeplanePropertyListener outlinePropertyListener;
    private boolean outlinePropertyListenerRegistered;
    private final OutlineBlockViewCache blockCache = new OutlineBlockViewCache();
    private OutlineBlockLayout blockLayout;
    private OutlineSelectionBridge selectionBridge;
    private OutlineFocusManager focusManager;
    private final OutlineSelectionHistory selectionHistory = new OutlineSelectionHistory();
    private Supplier<Color> backgroundColorSupplier;

    private VisibleBlockRenderer visibleBlockRenderer;
    private BreadcrumbLayout breadcrumbLayout;
	private OutlineDisplayMode displayMode;
	private final int blockSize;
	private BreadcrumbMode breadcrumbMode;

    ScrollableTreePanel(OutlineDisplayMode displayMode, TreeNode root,  BreadcrumbPanel breadcrumbPanel) {
        this(displayMode, root, BLOCK_SIZE,breadcrumbPanel);
        addMouseListener(new FocusSelectedButtonClickAdapter(focusManager));
        addMouseListener(new MouseAdapter() {
			@Override
			public void mouseEntered(MouseEvent e) {
				TimeDelayedOutlineSelection.outlineSelector.handleMouseEvent(e);
			}
		});
        setOpaque(true);
	}

    private ScrollableTreePanel(OutlineDisplayMode displayMode, TreeNode root, int blockSize, BreadcrumbPanel breadcrumbPanel) {
        super(null);
		this.setDisplayMode(displayMode);
        this.root = root;
		this.blockSize = blockSize;
        this.breadcrumbPanel = breadcrumbPanel;
        this.breadcrumbMode = ResourceController.getResourceController().getEnumProperty("outlineBreadcrumbMode", BreadcrumbMode.DEFAULT);
        this.outlineSelection = new OutlineSelection(root);
        this.visibleNodes = new VisibleOutlineNodes(root);
        this.expansionControls = new ExpansionControls(this, outlineSelection);
        OutlineGeometry geometry = OutlineGeometry.getInstance();
        this.navButtons = new NavigationButtons(geometry, displayMode, expansionControls);
        this.blockPanel = new JPanel(null);
        blockPanel.setOpaque(false);
        add(blockPanel);
        this.blockLayout = new OutlineBlockLayout(blockCache, visibleNodes, geometry, blockSize, this);
        this.focusManager = new OutlineFocusManager(this, breadcrumbPanel, outlineSelection);
        this.geometryListener = this::handleGeometryChange;
        this.outlinePropertyListener = this::handleOutlinePropertyChange;
        setFocusable(true);
        setupKeyBindings();

        this.visibleBlockRenderer = new VisibleBlockRenderer(blockLayout, blockCache, blockPanel, visibleNodes,
                navButtons, focusManager, this::getWidth,
                this::updatePreferredSize, this::refreshUI, this::updateFirstVisibleNodeId,
                this::isNodeInBreadcrumbArea);

        this.breadcrumbLayout = new BreadcrumbLayout(breadcrumbPanel, visibleNodes, navButtons,
                outlineSelection, this::isSelectionDrivenBreadcrumbMode, this::isNodeInBreadcrumbArea,
                this::setBreadcrumbHeight, blockPanel);
    }

	@Override
	public void doLayout() {
		super.doLayout();
		int blockPanelY = visibleNodes.getBlockPanelY();
		int width = getWidth();
		int height = Math.max(0, getHeight() - blockPanelY);
		blockPanel.setBounds(0, blockPanelY, width, height);
		blockCache.setBlockWidhts(width);
	}

	private int calculateBlockPanelY() {
		if (!isSelectionDrivenBreadcrumbMode())
			return BreadcrumbPanel.BREADCRUMB_BOTTOM_MARGIN;
		return calculateBreadcrumbHeight();
	}

	private int calculateBreadcrumbHeight() {
		return BreadcrumbPanel.BREADCRUMB_BOTTOM_MARGIN +
				OutlineGeometry.getInstance().rowHeight * breadcrumbPanel.getCurrentBreadcrumbNodeCount();
	}

	@Override
    public void addNotify() {
        super.addNotify();
        if (!geometryListenerRegistered) {
            OutlineGeometry.registerListener(geometryListener);
            geometryListenerRegistered = true;
        }
        if (!outlinePropertyListenerRegistered) {
            ResourceController.getResourceController().addPropertyChangeListener(outlinePropertyListener);
            outlinePropertyListenerRegistered = true;
        }
    }

    @Override
    public void removeNotify() {
        if (geometryListenerRegistered) {
            OutlineGeometry.unregisterListener(geometryListener);
            geometryListenerRegistered = false;
        }
        if (outlinePropertyListenerRegistered) {
            ResourceController.getResourceController().removePropertyChangeListener(outlinePropertyListener);
            outlinePropertyListenerRegistered = false;
        }
        super.removeNotify();
    }

    private void handleGeometryChange(OutlineGeometry geometry) {
        if (geometry == null) {
            return;
        }

        blockLayout.updateGeometry(geometry);
        navButtons.updateGeometry(geometry);

        TreeNode hoveredNode = visibleNodes.getHoveredNode();
        String firstVisibleNodeId = visibleNodes.getFirstVisibleNodeId();
        int firstVisibleIndex = visibleNodes.findNodeIndexById(firstVisibleNodeId);
        if (firstVisibleIndex < 0) {
            firstVisibleIndex = 0;
        }
        List<TreeNode> breadcrumbNodes = breadcrumbPanel.getCurrentBreadcrumbNodes();

        blockPanel.removeAll();
        blockPanel.setComponentOrientation(geometry.outlineTextOrientation);
        blockCache.clear();
        blockLayout.resetCachedMaxWidth();
        resetBlockCache();

        visibleNodes.setHoveredNode(hoveredNode);

        breadcrumbPanel.setComponentOrientation(geometry.outlineTextOrientation);
        breadcrumbPanel.update(breadcrumbNodes, true);

        int visibleCount = visibleNodes.getVisibleNodeCount();
        if (viewport != null && visibleCount > 0) {
            int clampedIndex = Math.min(firstVisibleIndex, visibleCount - 1);
            updateVisibleBlocks(clampedIndex);
        } else {
            revalidate();
            repaint();
        }

        AuxillaryEditorSplitPane pane = (AuxillaryEditorSplitPane) SwingUtilities.getAncestorOfClass(AuxillaryEditorSplitPane.class, this);
        if(pane != null)
        	pane.changeAuxComponentSide(OutlineGeometry.getInstance().isRightToLeft() ? "right" : "left");
    }

    @SuppressWarnings("unused")
	private void handleOutlinePropertyChange(String propertyName, String newValue, String oldValue) {
        if ("useColoredOutlineItems".equals(propertyName)) {
        	refreshColoredOutlineItems();
        }
        else if ("outlineBreadcrumbMode".equals(propertyName)) {
        	setBreadcrumbMode(BreadcrumbMode.valueOf(newValue));
        }
    }

    private void refreshColoredOutlineItems() {
        for (BlockPanel panel : blockCache.blockPanels()) {
            panel.rebuildNodeButtons();
        }
        breadcrumbPanel.updateNodeButtons();

        breadcrumbLayout.reattachNavigationButtons();

        revalidate();
        repaint();
    }

    @SuppressWarnings("serial")
    private void setupKeyBindings() {
        new OutlineActions(() -> this).installOn(this, JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT);
    }

	void setBackgroundColorSupplier(Supplier<Color> backgroundColorSupplier) {
		this.backgroundColorSupplier = backgroundColorSupplier;
	}

    @Override
	public Color getBackground() {
		 if (backgroundColorSupplier != null) {
			final Color suppliedColor = backgroundColorSupplier.get();
			if(suppliedColor != null)
				return suppliedColor;
		 }
		 return super.getBackground();
	}

	BreadcrumbMode getBreadcrumbMode() {
		return breadcrumbMode;
	}

	void setBreadcrumbMode(BreadcrumbMode newMode) {
		BreadcrumbMode resolvedMode = newMode;
		if (breadcrumbMode == resolvedMode) {
			return;
		}
		breadcrumbMode = resolvedMode;
        visibleNodes.setBlockPanelY(calculateBlockPanelY());
		if (isSelectionDrivenBreadcrumbMode()) {
			updateBreadcrumbForSelection();
		}
		else {
			updateBreadcrumbForCurrentFirstVisibleNode();
		}
		updateVisibleNodes(displayMode == OutlineDisplayMode.MAP_VIEW_SYNC ? ScrollMode.SIBLINGS : ScrollMode.SINGLE_ITEM);
	}

	boolean isSelectionDrivenBreadcrumbMode() {
		return breadcrumbMode == BreadcrumbMode.FOLLOW_SELECTED_ITEM;
	}


    void synchronizeSelectionButton(boolean requestFocusInWindow) {
    	selectionBridge.synchronizeOutlineSelection(SelectionSynchronizationTrigger.OUTLINE, requestFocusInWindow);
    	focusManager.focusSelectionButtonLater(requestFocusInWindow);
    }

    void setScrollPane(JScrollPane scroll) {
        this.viewport = new OutlineViewport(scroll, visibleNodes, blockSize);
        if (visibleBlockRenderer != null) {
            visibleBlockRenderer.setViewport(viewport);
        }
        resetBlockCache();
    }

    void setBreadcrumbHeight(int height) {
        visibleNodes.setBreadcrumbHeight(height);
        visibleNodes.setBlockPanelY(calculateBlockPanelY());
    }

    void updateVisibleBlocks() {
        if (visibleBlockRenderer == null) return;
        visibleBlockRenderer.render();
    }

    void updateVisibleBlocks(int startFromNodeIndex) {
        if (visibleBlockRenderer == null) return;
        visibleBlockRenderer.renderFromIndex(startFromNodeIndex);
    }

    private void resetBlockCache() {
        if (visibleBlockRenderer != null) {
            visibleBlockRenderer.resetCachedRange();
        }
    }

    boolean isNodeFullyVisibleInViewport(TreeNode node) {
        if (viewport == null || node == null) return false;
        int index = visibleNodes.findNodeIndexInVisibleList(node);
        if (index < 0) return false;
        int first = calculateFirstVisibleNodeIndex();
        int currentBreadcrumbRows = getBreadcrumbRowsForIndex(first);
        int contentRows = getContentRowsForBreadcrumbRows(currentBreadcrumbRows);
        int last = Math.max(first, first + contentRows - 1);
        return index >= first && index <= last;
    }

    private void updatePreferredSize() {
        blockLayout.updateBlockPreferredSize(blockPanel);
        Dimension blockPreferredSize = blockPanel.getPreferredSize();
        int contentOffset = visibleNodes.getBlockPanelY();
        int breadcrumbHeight = visibleNodes.getBreadcrumbHeight();
        int preferredHeight = Math.max(blockPreferredSize.height + contentOffset + getParent().getHeight() - OutlineGeometry.getInstance().rowHeight, breadcrumbHeight);
		Dimension panelPreferredSize = new Dimension(blockPreferredSize.width,
        		preferredHeight);
        setPreferredSize(panelPreferredSize);
    }

    private void refreshUI() {
        viewport.refreshViewport();
        repaint();
    }

    private void updateFirstVisibleNodeId() {
        if (viewport == null) return;
        int index = calculateFirstVisibleNodeIndex();
        int count = visibleNodes.getVisibleNodeCount();
        if (count == 0) {
            visibleNodes.setFirstVisibleNodeId(null);
            return;
        }
        index = Math.max(0, Math.min(index, count - 1));
        visibleNodes.setFirstVisibleNodeId(visibleNodes.getNodeIdAtVisibleIndex(index));
    }

	void setSelectedNode(TreeNode node, boolean requestFocus) {
		setSelectedNode(node, requestFocus, ScrollMode.SINGLE_ITEM);
	}

	private void setSelectedNode(TreeNode node, boolean requestFocus, ScrollMode scrollMode) {
		if(node != outlineSelection.getSelectedNode()) {
			final TreeNode hoveredNode = visibleNodes.getHoveredNode();
			if(hoveredNode != node && hoveredNode != null) {
				onContentButtonHovered(node);
			}
			selectionHistory.record(node);
			outlineSelection.selectNode(node);
			if (isSelectionDrivenBreadcrumbMode()) {
				updateBreadcrumbForSelection();
			}
			repaint();
			if (visibleNodes.findNodeIndexInVisibleList(node) < 0) {
				TreeNode preservedHoveredNode = visibleNodes.getHoveredNode();
				hardResetBlocksPreservingHovered(preservedHoveredNode);
			}

			if(scrollMode == ScrollMode.SINGLE_ITEM) {
				boolean visible = isNodeFullyVisibleInViewport(node);
				if (!isSelectionDrivenBreadcrumbMode() && isNodeInBreadcrumbArea(node)) {
					visible = true;
				}
				if (!visible) {
					ensureSelectionVisible(scrollMode);
				}
			}
			else if (scrollMode == ScrollMode.SIBLINGS)
				ensureSelectionVisible(scrollMode);
		}
		else if (isSelectionDrivenBreadcrumbMode()) {
			updateBreadcrumbForSelection();
		}
		focusSelectionButtonLater(requestFocus);

    }

    void toggleBreadcrumbNodeExpansion(TreeNode node, boolean requestFocus) {
        setSelectedNode(node, requestFocus);
        toggleExpandSelected();
    }

	OutlineSelection getOutlineSelection() {
        return outlineSelection;
    }

    int getRowHeight() {
        return OutlineGeometry.getInstance().rowHeight;
    }

    int calcTextButtonX(int level) {
        return OutlineGeometry.getInstance().calculateNodeButtonX(displayMode.showsNavigationButtons(), level);
    }

    int getViewportWidth() {
        return viewport != null ? viewport.getViewportWidth() : getWidth();
    }

    VisibleOutlineNodes getVisibleNodes() {
        return visibleNodes;
    }

    TreeNode getRoot() {
        return root;
    }

    void hardResetBlocksPreservingHovered(TreeNode preservedHoveredNode) {
        blockPanel.removeAll();
        blockCache.clear();
        visibleNodes.setHoveredNode(preservedHoveredNode);
        updateVisibleBlocks();
    }

    boolean isNodeButtonFocused() { return focusManager.isNodeButtonFocused(); }

    void selectMapNodeById(String nodeId) {
    	if (selectionBridge != null) {
			selectionBridge.selectMapNodeById(nodeId);
		}
    }

    @Override
	public void selectSelectedInMap() {
        TreeNode selected = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        if (selected != null) {
            selectMapNodeById(selected.getId());
        }
    }

    void setSelectionBridge(OutlineSelectionBridge bridge) {
        this.selectionBridge = bridge;
        breadcrumbPanel.setSelectionBridge(bridge);
        breadcrumbLayout.setSelectionBridge(bridge);
    }

    void updateNodeTitle(TreeNode node) {
        for (Component comp : breadcrumbPanel.getComponents()) {
            if (comp instanceof NodeButton) {
                NodeButton btn = (NodeButton) comp;
                if (btn.getNode() == node) {
                    btn.updateLabel();
                    int level = node.getLevel();
                    if (level >= 0) {
                        int x = OutlineGeometry.getInstance().calculateNodeButtonX(displayMode.showsNavigationButtons(), level);
                        int rightEdge = x + btn.getWidth();
                        blockLayout.recordButtonRightEdge(rightEdge);
                        btn.setBounds(x, btn.getY(), btn.getPreferredSize().width, OutlineGeometry.getInstance().rowHeight);
                        RightToLeftLayout.applyToSingleComponent(btn);
                    }
                    breadcrumbPanel.revalidate();
                    breadcrumbPanel.repaint();
                    break;
                }
            }
        }

        for (int blockIndex : blockCache.keySet()) {
            BlockPanel panel = blockCache.get(blockIndex);
            if (panel == null) continue;
            for (Component comp : panel.getComponents()) {
                if (comp instanceof NodeButton) {
                    NodeButton btn = (NodeButton) comp;
                    if (btn.getNode() == node) {
                        btn.updateLabel();
                        int level = node.getLevel();
                        if (level >= 0) {
                            int x = OutlineGeometry.getInstance().calculateNodeButtonX(displayMode.showsNavigationButtons(), level);
                            int rightEdge = x + btn.getWidth();
                            blockLayout.recordButtonRightEdge(rightEdge);
                            btn.setBounds(x, btn.getY(), btn.getPreferredSize().width, OutlineGeometry.getInstance().rowHeight);
                            RightToLeftLayout.applyToSingleComponent(btn);
                        }
                        panel.revalidate();
                        panel.repaint();

                        break;
                    }
                }
            }
        }

        updatePreferredSize();
        refreshUI();
    }


    void rebuildFromNode(String anchorNodeId) {
        if (viewport == null) return;

        Component prevFocus = KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner();
        boolean prevInOutline = focusManager.isWithinOutline(prevFocus);

        updateVisibleNodes();
		int firstFullyVisibleNodeIndex = calculateFirstVisibleNodeIndex();


		List<TreeNode> state = breadcrumbLayout.calculateState(firstFullyVisibleNodeIndex);

        TreeNode preservedHovered = visibleNodes.getHoveredNode();
        blockPanel.removeAll();
        blockCache.clear();
        blockLayout.resetCachedMaxWidth();
        final boolean wasHoveredNodeContainedInBreadcrumb = visibleNodes.isHoveredNodeContainedInBreadcrumb();
		visibleNodes.setHoveredNode(preservedHovered);

		if (state != null) {
			breadcrumbLayout.applyState(state);
			updateVisibleBlocks(firstFullyVisibleNodeIndex);

            TreeNode hovered = visibleNodes.getHoveredNode();
			if (hovered != null && ! wasHoveredNodeContainedInBreadcrumb && visibleNodes.findNodeIndexInVisibleList(hovered) < 0) {
                visibleNodes.setHoveredNode(null);
            }

            ensureValidSelectionOrSyncFromMap();
            focusManager.restoreFocusIfNeeded(prevInOutline);
            return;
        }

        int anchorIndex = visibleNodes.findNodeIndexById(anchorNodeId);
        if (anchorIndex < 0) {
            updateVisibleBlocksAndBreadcrumb();
            ensureValidSelectionOrSyncFromMap();
            focusManager.restoreFocusIfNeeded(prevInOutline);
            return;
        }

        blockPanel.removeAll();
        blockCache.clear();
        blockLayout.resetCachedMaxWidth();
        navButtons.hideNavigationButtons();
        visibleNodes.setHoveredNode(preservedHovered);
        updateVisibleBlocks();

        TreeNode hovered = visibleNodes.getHoveredNode();
        if (hovered != null && visibleNodes.findNodeIndexInVisibleList(hovered) < 0) {
            visibleNodes.setHoveredNode(null);
        }

        ensureValidSelectionOrSyncFromMap();
        focusManager.restoreFocusIfNeeded(prevInOutline);
    }

    private void ensureValidSelectionOrSyncFromMap() {
        TreeNode selected = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        if (selected == null) return;
        if (!isNodeAttachedToRoot(selected)) {
            if (selectionBridge != null) {
                selectionBridge.synchronizeOutlineSelection(SelectionSynchronizationTrigger.MAP, false);
            }
        }
    }

    private boolean isNodeAttachedToRoot(TreeNode node) {
        for (TreeNode n = node; n != null; n = n.getParent()) {
            if (n == root) return true;
        }
        return false;
    }

    void onContentButtonHovered(TreeNode node) {
        if (node != null && !node.getChildren().isEmpty()
        		&& (visibleNodes.isHoveredNodeContainedInBreadcrumb() || node != visibleNodes.getHoveredNode())) {

            if (! isNodeFullyVisibleInViewport(node)) {
                return;
            }

            visibleNodes.setHoveredNode(node, false);
            int nodeIndex = visibleNodes.findNodeIndexInVisibleList(node);
			navButtons.attachToNode(node, blockPanel, nodeIndex, node.getLevel());
            repaint();
        }
    }

	void showNavigationButtonsForBreadcrumb(TreeNode node, int rowIndex) {
		visibleNodes.setHoveredNode(node, true);
		navButtons.attachToNode(node, breadcrumbPanel, rowIndex, rowIndex);
	}


    @Override
    public void navigateUp() {
        TreeNode currentSelected = outlineSelection.getSelectedNode();
        if (currentSelected != null) {
            int currentIndex = visibleNodes.findNodeIndexInVisibleList(currentSelected);
            if (currentIndex > 0) {
                TreeNode prev = visibleNodes.getNodeAtVisibleIndex(currentIndex - 1);
                if (prev != null) setSelectedNode(prev, true);
            }
        }
    }

	void focusSelectionButtonLater(boolean requestFocus) { focusManager.focusSelectionButtonLater(requestFocus); }

    @Override
    public void navigateDown() {
        TreeNode currentSelected = outlineSelection.getSelectedNode();
        if (currentSelected == null || viewport == null) return;

        int currentIndex = visibleNodes.findNodeIndexInVisibleList(currentSelected);
        int size = visibleNodes.getVisibleNodeCount();
        if (currentIndex < 0 || currentIndex >= size - 1) return;

        int nextIndex = currentIndex + 1;
        TreeNode nextNode = visibleNodes.getNodeAtVisibleIndex(nextIndex);
        if (nextNode == null) return;
        if (isNodeInBreadcrumbArea(nextNode) || isNodeFullyVisibleInViewport(nextNode)) {
            setSelectedNode(nextNode, true);
            return;
        }
        int currentFirstVisibleIndex = calculateFirstVisibleNodeIndex();
		int currentBreadcrumbRowCount = getBreadcrumbRowsForIndex(currentFirstVisibleIndex);
		int nextBreadcrumbRowCount = getBreadcrumbRowsForIndex(Math.min(currentFirstVisibleIndex + 1, size - 1));
        int breadcrumbRowDelta = nextBreadcrumbRowCount - currentBreadcrumbRowCount;
        int minimalScrollRows = Math.max(0, 1 + breadcrumbRowDelta);

        int tentativeFirstIndex = Math.min(currentFirstVisibleIndex + minimalScrollRows, size - 1);
		int breadcrumbRowsAtTentative = getBreadcrumbRowsForIndex(tentativeFirstIndex);
        int contentRowCountAfterTentative = getContentRowsForBreadcrumbRows(breadcrumbRowsAtTentative);
        int maxFeasibleFirstIndex = Math.max(0, size - contentRowCountAfterTentative);
        int targetFirstIndex = Math.min(tentativeFirstIndex, maxFeasibleFirstIndex);
		List<TreeNode> plannedBreadcrumbState = breadcrumbLayout.calculateState(targetFirstIndex);
		if (plannedBreadcrumbState != null) {
			breadcrumbLayout.applyState(plannedBreadcrumbState);
			updateVisibleBlocks(targetFirstIndex);
		}

        setSelectedNode(nextNode, true);
    }

	private void updateBreadcrumbForSelection() {
		int firstVisibleNodeIndex = calculateFirstVisibleNodeIndex();
		int breadcrumbNodeCountBefore = breadcrumbPanel.getCurrentBreadcrumbNodeCount();
		breadcrumbLayout.updateForSelection();
		int breadcrumbNodeCountAfter = breadcrumbPanel.getCurrentBreadcrumbNodeCount();
		if(breadcrumbNodeCountBefore != breadcrumbNodeCountAfter) {
			int newFirstVisibleNodeIndex = Math.max(0, firstVisibleNodeIndex + breadcrumbNodeCountAfter - breadcrumbNodeCountBefore);
			viewport.setViewPosition(newFirstVisibleNodeIndex, 0);
		}
		revalidate();
	}

	private void updateBreadcrumbForCurrentFirstVisibleNode() {
		int firstVisibleIndex = 0;
		if (viewport != null) {
			firstVisibleIndex = calculateFirstVisibleNodeIndex();
		}
		breadcrumbLayout.updateForFirstVisibleIndex(firstVisibleIndex);
	}

	private int getCurrentBreadcrumbRowCount() {
		int rowHeight = OutlineGeometry.getInstance().rowHeight;
		if (rowHeight <= 0) {
			return 0;
		}
		int height = visibleNodes.getBreadcrumbHeight();
		if (height <= 0) {
			return 0;
		}
		return Math.max(0, height / rowHeight);
	}

	private int getBreadcrumbRowsForIndex(int visibleIndex) {
		if (isSelectionDrivenBreadcrumbMode()) {
			return getCurrentBreadcrumbRowCount();
		}
		return getNodeLevelAtVisibleIndex(visibleIndex);
	}


    @Override
    public void navigatePageUp() {
        TreeNode currentSelected = outlineSelection.getSelectedNode();
        if (currentSelected != null) {
            int currentIndex = visibleNodes.findNodeIndexInVisibleList(currentSelected);
            int pageSize = getContentRows();
            int size = visibleNodes.getVisibleNodeCount();
            int currentFirstVisibleIndex = viewport != null ? calculateFirstVisibleNodeIndex() : 0;
            if (currentIndex > currentFirstVisibleIndex) {
                TreeNode firstVisibleNode = visibleNodes.getNodeAtVisibleIndex(currentFirstVisibleIndex);
                if (firstVisibleNode != null) setSelectedNode(firstVisibleNode, true);
                updateVisibleBlocksAndBreadcrumb();
                return;
            }
            int tentativeFirstIndex = Math.max(0, currentFirstVisibleIndex - pageSize + 1); // overlap = 1
			int breadcrumbRowsAtTentative = getBreadcrumbRowsForIndex(tentativeFirstIndex);
            int contentRowCountAfterTentative = getContentRowsForBreadcrumbRows(breadcrumbRowsAtTentative);
            int maxFeasibleFirstIndex = Math.max(0, size - contentRowCountAfterTentative);
            int targetFirstIndex = Math.min(tentativeFirstIndex, maxFeasibleFirstIndex);
			List<TreeNode> plannedBreadcrumbState = breadcrumbLayout.calculateState(targetFirstIndex);
			if (plannedBreadcrumbState != null) {
				breadcrumbLayout.applyState(plannedBreadcrumbState);
				updateVisibleBlocks(targetFirstIndex);
			}
            TreeNode newFirstNode = visibleNodes.getNodeAtVisibleIndex(targetFirstIndex);
            if (newFirstNode != null) setSelectedNode(newFirstNode, true);
        }
    }

    @Override
    public void navigatePageDown() {
        TreeNode currentSelected = outlineSelection.getSelectedNode();
        if (currentSelected != null) {
            int currentIndex = visibleNodes.findNodeIndexInVisibleList(currentSelected);
            int pageSize = getContentRows();
            int size = visibleNodes.getVisibleNodeCount();

            int currentFirstVisibleIndex = viewport != null ? calculateFirstVisibleNodeIndex() : 0;
            int lastVisibleIndex = Math.min(size - 1, currentFirstVisibleIndex + pageSize - 1);
            if (currentIndex < lastVisibleIndex) {
                TreeNode lastVisibleNode = visibleNodes.getNodeAtVisibleIndex(lastVisibleIndex);
                if (lastVisibleNode != null) setSelectedNode(lastVisibleNode, true);
                updateVisibleBlocksAndBreadcrumb();
                return;
            }
            int tentativeFirstIndex = Math.min(size - 1, currentFirstVisibleIndex + pageSize - 1); // overlap = 1
			int breadcrumbRowsAtTentative = getBreadcrumbRowsForIndex(tentativeFirstIndex);
            int contentRowCountAfterTentative = getContentRowsForBreadcrumbRows(breadcrumbRowsAtTentative);
            int maxFeasibleFirstIndex = Math.max(0, size - contentRowCountAfterTentative);
            int targetFirstIndex = Math.min(tentativeFirstIndex, maxFeasibleFirstIndex);
			List<TreeNode> plannedBreadcrumbState = breadcrumbLayout.calculateState(targetFirstIndex);
			if (plannedBreadcrumbState != null) {
				breadcrumbLayout.applyState(plannedBreadcrumbState);
				updateVisibleBlocks(targetFirstIndex);
			}

            int newLastVisibleIndex = Math.min(size - 1, targetFirstIndex + contentRowCountAfterTentative - 1);
            TreeNode newLastVisibleNode = visibleNodes.getNodeAtVisibleIndex(newLastVisibleIndex);
            if (newLastVisibleNode != null) setSelectedNode(newLastVisibleNode, true);
        }
    }

    @Override
    public void toggleExpandSelected() {
        TreeNode node = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        toggleNodeExpansion(node);
    }

    public void toggleNodeExpansion(TreeNode node) {
        if(node == null || node.childCount() == 0 || node.getLevel() == 0) {
            return;
        }
        if (node.isExpanded()) {
    		final int minimalLevel = getDisplayMode().getMinimalOutlineLevel();
    		if (node.getLevel() >= minimalLevel) {
    			if(! isSelectionDrivenBreadcrumbMode() && isNodeInBreadcrumbArea(node))
    				updateVisibleBlocksAndBreadcrumb(visibleNodes.findNodeIndexById(node.getId()));
				expansionControls.collapseNode(node);
			}
        } else {
            expansionControls.expandNode(node);
        }
    }

    @Override
    public void expandSelectedMore() {
        TreeNode node = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        if (node == null) return;
        expansionControls.expandNodeMore(node);
    }

    @Override
    public void reduceSelectedExpansion() {
        TreeNode node = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        if (node == null) return;
        expansionControls.reduceNodeExpansion(node);
    }

    @Override
    public void collapseOrGoToParent() {
        TreeNode node = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        if (node == null)
        	return;
		if (node.isExpanded() && (isSelectionDrivenBreadcrumbMode() || ! isNodeInBreadcrumbArea(node))) {
			expansionControls.collapseNode(node);
		}
		else {
			final TreeNode parent = node.getParent();
			setSelectedNode(parent, true);
		}
    }

    @Override
    public void expandOrGoToChild() {
        TreeNode node = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        if (node == null || node.getChildren().isEmpty()) return;
        if (!node.isExpanded()) {
            expansionControls.expandNode(node);
        }
        else {
        	TreeNode targetChild = selectionHistory.preferredChild(node);
        	setSelectedNode(targetChild, true);
        }
    }

    private int getContentRows() {
        if (viewport != null) {
            int breadcrumbHeight = visibleNodes.getBreadcrumbHeight();
            int viewportHeight = viewport.getViewportHeight() - breadcrumbHeight;
            return Math.max(1, viewportHeight / OutlineGeometry.getInstance().rowHeight - 1);
        }
        return 10;
    }

    private int getContentRowsForBreadcrumbRows(int breadcrumbRowCount) {
        if (viewport != null) {
            int viewportHeight = viewport.getViewportHeight() - breadcrumbPanel.preferredBreadCrumbHeight(breadcrumbRowCount);
            return Math.max(1, viewportHeight / OutlineGeometry.getInstance().rowHeight - 1);
        }
        return 10;
    }

    private int getNodeLevelAtVisibleIndex(int visibleIndex) {
        TreeNode node = visibleNodes.getNodeAtVisibleIndex(visibleIndex);
        return node != null ? node.getLevel() : 0;
    }

    void updateVisibleNodes(ScrollMode scrollMode) {
        updateVisibleNodes();
        blockPanel.removeAll();
        blockCache.clear();
        ensureSelectionVisible(scrollMode);
    }

	private void updateVisibleNodes() {
		visibleNodes.updateVisibleNodes();
		TreeNode selectedNode = outlineSelection.getSelectedNode();
		if(selectedNode != null) {
			TreeNode node = visibleNodes.findNodeById(selectedNode.getId());
			if(node != selectedNode)
				outlineSelection.selectNode(node);
		}
	}

    void updateVisibleBlocksAndBreadcrumb() {
    	int firstFullyVisibleNodeIndex = calculateFirstVisibleNodeIndex();
        updateVisibleBlocksAndBreadcrumb(firstFullyVisibleNodeIndex);
    }

	private void updateVisibleBlocksAndBreadcrumb(int firstFullyVisibleNodeIndex) {
		Component prevFocus = KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner();
        boolean prevInOutline = focusManager.isWithinOutline(prevFocus);
		List<TreeNode> state = breadcrumbLayout.calculateState(firstFullyVisibleNodeIndex);
		if (state != null) {
			int oldBreadcrumbHeight = visibleNodes.getBreadcrumbHeight();
			breadcrumbLayout.applyState(state);
            int newBreadcrumbHeight = visibleNodes.getBreadcrumbHeight();
            if (newBreadcrumbHeight != oldBreadcrumbHeight) {
                TreeNode preservedHovered = visibleNodes.getHoveredNode();
                hardResetBlocksPreservingHovered(preservedHovered);
            }
            updateVisibleBlocks(firstFullyVisibleNodeIndex);
        }
        else {
            updateVisibleBlocks();
        }
        focusManager.restoreFocusIfNeeded(prevInOutline);
	}

    void ensureSelectionVisible(ScrollMode scrollMode) {
        if (viewport == null) return;
        TreeNode selected = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        int selectedIndex = selected != null ? visibleNodes.findNodeIndexInVisibleList(selected) : -1;

        int first = calculateFirstVisibleNodeIndex();
		int currentBreadcrumbRows = getBreadcrumbRowsForIndex(first);
        int contentRows = getContentRowsForBreadcrumbRows(currentBreadcrumbRows);
        int last = Math.max(first, first + contentRows - 1);
        boolean haveButtons = blockPanel.getComponentCount() > 0 || !blockCache.isEmpty();
        if (!haveButtons && contentRows <= 1) {
            updateVisibleBlocks();
            return;
        }

        int visibleCount = visibleNodes.getVisibleNodeCount();
		if (haveButtons && (selected == null || selectedIndex < 0
				|| scrollMode == ScrollMode.SINGLE_ITEM
				&& (!isSelectionDrivenBreadcrumbMode() && isNodeInBreadcrumbArea(selected)
						|| selectedIndex >= first && selectedIndex <= last)))
			return;
        int targetFirst;
        if (selected == null || selectedIndex < 0) {
            targetFirst = first;
        }
        else if(scrollMode == ScrollMode.SIBLINGS && selected.getParent() != null) {
        	List<TreeNode> siblings = selected.getParent().getChildren();
			TreeNode firstSibling = siblings.get(0);
        	int blockStartIndex = visibleNodes.findNodeIndexInVisibleList(firstSibling);
			int availableBreadcrumbRows = getBreadcrumbRowsForIndex(blockStartIndex);
            int availableContentRows = getContentRowsForBreadcrumbRows(availableBreadcrumbRows);
			int selectedChildCount = selected.childCount();
			int requiredVisibleRows = 1 + selectedChildCount;
			int blockEndExclusiveIndex = blockStartIndex + siblings.size() + selectedChildCount;
			int maxStartIndex = blockEndExclusiveIndex - availableContentRows;
			if (maxStartIndex < blockStartIndex) {
				maxStartIndex = blockStartIndex;
			}
			if (availableContentRows <= 0) {
				targetFirst = blockStartIndex;
			}
			else if (availableContentRows < requiredVisibleRows) {
				targetFirst = Math.max(blockStartIndex, Math.min(selectedIndex, maxStartIndex));
			}
			else {
				int extraRowCapacity = availableContentRows - requiredVisibleRows;
				int balancedStartIndex = selectedIndex - extraRowCapacity / 2;
				targetFirst = Math.max(blockStartIndex, Math.min(balancedStartIndex, maxStartIndex));
			}
			visibleNodes.setBlockPanelY(calculateBlockPanelY());
        }
		else if (!isSelectionDrivenBreadcrumbMode() && isNodeInBreadcrumbArea(selected)) {
			targetFirst = first;
		}
        else if (selectedIndex < first) {
            int desiredFirst = Math.max(0, selectedIndex);
			int br = getBreadcrumbRowsForIndex(desiredFirst);
            int cr = getContentRowsForBreadcrumbRows(br);
            int maxFeasibleFirst = Math.max(0, visibleCount - cr);
            targetFirst = Math.min(desiredFirst, maxFeasibleFirst);
        }
        else if (selectedIndex > last) {
            int desiredFirst = Math.max(0, selectedIndex - (contentRows - 1));
			int br = getBreadcrumbRowsForIndex(desiredFirst);
            int cr = getContentRowsForBreadcrumbRows(br);
            int maxFeasibleFirst = Math.max(0, visibleCount - cr);
            targetFirst = Math.min(desiredFirst, maxFeasibleFirst);
        }
        else {
            targetFirst = first;
        }
		List<TreeNode> planned = breadcrumbLayout.calculateState(targetFirst);
		if (planned != null) {
			int oldBreadcrumbHeight = visibleNodes.getBreadcrumbHeight();
			breadcrumbLayout.applyState(planned);
            int newBreadcrumbHeight = visibleNodes.getBreadcrumbHeight();
            if (newBreadcrumbHeight != oldBreadcrumbHeight) {
                TreeNode preservedHovered = visibleNodes.getHoveredNode();
                hardResetBlocksPreservingHovered(preservedHovered);
            }
            updateVisibleBlocks(targetFirst);
        }
        else {
            updateVisibleBlocks();
        }
    }

    private int calculateFirstVisibleNodeIndex() {
    	int viewY = viewport.getViewY();
        int effectiveViewY = viewY + visibleNodes.getBreadcrumbHeight() - visibleNodes.getBlockPanelY();
        if (effectiveViewY < 0) {
            effectiveViewY = 0;
        }
        int rowHeight = OutlineGeometry.getInstance().rowHeight;
        final int firstVisibleIndex = (effectiveViewY + rowHeight - 1) / rowHeight;
        if(firstVisibleIndex >= 1)
        	return firstVisibleIndex;
        else if(isSelectionDrivenBreadcrumbMode() || visibleNodes.getVisibleNodeCount() < 2)
        	return 0;
        else
        	return 1;
	}

    boolean isNodeInBreadcrumbArea(TreeNode node) {
        List<TreeNode> crumbs = breadcrumbPanel.getCurrentBreadcrumbNodes();
        return crumbs != null && crumbs.contains(node);
    }

    Collection<BlockPanel> getBlockPanels() { return blockCache.blockPanels(); }

	OutlineDisplayMode getDisplayMode() {
		return displayMode;
	}

	void performInitialSetup() {
		if(isSelectionDrivenBreadcrumbMode())
			updateBreadcrumbForSelection();
		updateVisibleBlocks();
	}

	void synchronizeOutlineSelection(TreeNode target, SelectionSynchronizationTrigger synchronizationTrigger, boolean requestFocus) {
		ScrollMode scrollMode;
		if(displayMode == OutlineDisplayMode.MAP_VIEW_SYNC && synchronizationTrigger == SelectionSynchronizationTrigger.MAP) {
			adjustExpansionLevels(target);
			scrollMode = ScrollMode.SIBLINGS;
			updateVisibleNodes(scrollMode);
		} else {
			target = target.findVisibleAncestorOrSelf();
			scrollMode = ScrollMode.SINGLE_ITEM;
		}

		int index = findVisibleIndex(target);
		boolean visible = isNodeVisible(target);
		if (!visible) {
			if (index < 0) index = 0;
			updateVisibleBlocks(index);
		}
		setSelectedNode(target, requestFocus, scrollMode);
	}

	private void adjustExpansionLevels(TreeNode node) {
		final TreeNode parent = node.getParent();
		if(parent != null) {
			adjustExpansionLevels(parent);
		}
		node.applyExpansionLevel(1);
	}

    private int findVisibleIndex(TreeNode node) {
        TreeNode n = node;
        while (n != null) {
            int idx = visibleNodes.findNodeIndexInVisibleList(n);
            if (idx >= 0) return idx;
            n = n.getParent();
        }
        return 0;
    }

    private boolean isNodeVisible(TreeNode node) {
    	return !isSelectionDrivenBreadcrumbMode() && isNodeInBreadcrumbArea(node)
			|| isNodeFullyVisibleInViewport(node);
	}

	void setDisplayMode(OutlineDisplayMode displayMode) {
		this.displayMode = displayMode;
	}

	@Override
	public void invalidate() {
		 super.invalidate();
	}
}

package org.freeplane.view.swing.map.outline;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Stroke;
import java.awt.event.ActionEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

import javax.swing.AbstractAction;
import javax.swing.ActionMap;
import javax.swing.InputMap;
import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.KeyStroke;

import org.freeplane.core.resources.ResourceController;
import org.freeplane.core.ui.components.UITools;

@SuppressWarnings("serial")
class BreadcrumbPanel extends JPanel {
    public static final int BREADCRUMB_BOTTOM_MARGIN = (int) (UITools.FONT_SCALE_FACTOR * 4);
    private static final BasicStroke BOTTOM_LINE_STROKE = new BasicStroke(BREADCRUMB_BOTTOM_MARGIN, BasicStroke.CAP_ROUND, BasicStroke.JOIN_BEVEL, 1f, new float[] {BREADCRUMB_BOTTOM_MARGIN, 2*BREADCRUMB_BOTTOM_MARGIN}, 0f);
	private OutlineController controller;
    private OutlineSelection selection;
    private int preferredBreadcrumbHeight = 0;
    private List<TreeNode> currentBreadcrumbNodes = new ArrayList<>();
	private OutlineSelectionBridge selectionBridge;
	private Supplier<Color> backgroundColorSupplier;

    BreadcrumbPanel() {
        setLayout(null);
        setOpaque(true);
        addMouseListener(new MouseAdapter() {
			@Override
			public void mouseEntered(MouseEvent e) {
				TimeDelayedOutlineSelection.outlineSelector.handleMouseEvent(e);
			}
		});
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

	@Override
	public void setBounds(int x, int y, int width, int height) {
		int oldWidth = getWidth();
		RightToLeftLayout.onContainerWidthChange(this, oldWidth, width);
		super.setBounds(x, y, width, height);
	}

	void setBackgroundColorSupplier(Supplier<Color> backgroundColorSupplier) {
		this.backgroundColorSupplier = backgroundColorSupplier;
	}

	void initialize(OutlineController controller, OutlineSelection selection) {
        this.controller = controller;
        this.selection = selection;
        setupKeyBindings();
    }

    @SuppressWarnings("serial")
    private void setupKeyBindings() {
        new OutlineActions(() -> controller).installOn(this, JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT);
    }

    void update(List<TreeNode> breadcrumbNodes, boolean wasGeometryUpdated) {
    	final int breadcrumbNodeCount = breadcrumbNodes.size();
		final int lastIndex = breadcrumbNodeCount - 1;
		if(wasGeometryUpdated || currentBreadcrumbNodes.size() != breadcrumbNodeCount
				|| ! (breadcrumbNodes.isEmpty()
						|| breadcrumbNodes.get(lastIndex) == currentBreadcrumbNodes.get(lastIndex))) {
			preferredBreadcrumbHeight = preferredBreadCrumbHeight(breadcrumbNodeCount);
			this.currentBreadcrumbNodes = breadcrumbNodes;

			controller.setBreadcrumbHeight(preferredBreadcrumbHeight);
			updateNodeButtons();
		}
    }



	int preferredBreadCrumbHeight(final int breadcrumbNodeCount) {
		return OutlineGeometry.getInstance().rowHeight * breadcrumbNodeCount + BREADCRUMB_BOTTOM_MARGIN;
	}

    void updateNodeButtons() {
        removeAll();
        ResourceController resourceController = ResourceController.getResourceController();
		final boolean useColoredOutlineItems = resourceController.getBooleanProperty("useColoredOutlineItems", false);
        final int rowHeight = controller.getRowHeight();
        for (int i = 0; i < currentBreadcrumbNodes.size(); i++) {
            TreeNode node = currentBreadcrumbNodes.get(i);
			int y = i * rowHeight;

            int x = controller.calcTextButtonX(i);

			NodeButton breadcrumbButton = new NodeButton(node, useColoredOutlineItems, false, Font.BOLD | Font.ITALIC, OutlineGeometry.getInstance().outlineTextOrientation);
            breadcrumbButton.setBounds(x, y, breadcrumbButton.getPreferredSize().width, rowHeight);

            final TreeNode nodeToSelect = node;
            final int rowIndex = i;
            final AbstractAction selectAction = new AbstractAction() {
                @Override
                public void actionPerformed(ActionEvent e) {
                	if(nodeToSelect.getParent()  != null || nodeToSelect.getLevel() == 0)
                		controller.selectNode(nodeToSelect, true);
                	if(selectionBridge != null)
                		selectionBridge.selectMapNodeById(nodeToSelect.getId());
                }
            };
            breadcrumbButton.addActionListener(selectAction);

            InputMap im = breadcrumbButton.getInputMap(JComponent.WHEN_FOCUSED);
            ActionMap am = breadcrumbButton.getActionMap();
            im.put(KeyStroke.getKeyStroke("ENTER"), "selectMapNode");
            am.put("selectMapNode", selectAction);
            im.put(KeyStroke.getKeyStroke("SPACE"), "toggleExpand");
            am.put("toggleExpand", new AbstractAction() {
                @Override
                public void actionPerformed(ActionEvent e) {
                    controller.toggleBreadcrumbNodeExpansion(nodeToSelect);
                }
            });

            breadcrumbButton.addMouseListener(new MouseAdapter() {
                @Override
                public void mouseEntered(MouseEvent e) {
                    showNavigationButtonsForBreadcrumb(nodeToSelect, rowIndex);
					if(node.getLevel() != TreeNode.UNKNOWN_LEVEL)
						TimeDelayedOutlineSelection.outlineSelector.handleMouseEvent(e);
                }
            });

            add(breadcrumbButton);

        }
        RightToLeftLayout.applyToContainer(this);
        revalidate();
        repaint();
	}

    int getPreferredBreadcrumbHeight() {
        return preferredBreadcrumbHeight;
    }

    List<TreeNode> getCurrentBreadcrumbNodes() {
        return new ArrayList<>(currentBreadcrumbNodes);
    }

    int getCurrentBreadcrumbNodeCount() {
        return currentBreadcrumbNodes.size();
    }

    void setSelectionBridge(OutlineSelectionBridge bridge) {
        this.selectionBridge = bridge;
    }

    private void showNavigationButtonsForBreadcrumb(TreeNode node, int rowIndex) {
        if (node.getChildren().isEmpty()) {
            return;
        }

        controller.showNavigationButtonsForBreadcrumb(node, rowIndex);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        if (preferredBreadcrumbHeight > 0) {
            g.setColor(UITools.getDisabledTextColorForBackground(getBackground()));
            int y = preferredBreadcrumbHeight - BREADCRUMB_BOTTOM_MARGIN/2;
            Graphics2D g2 = (Graphics2D)g;
            Stroke stroke = g2.getStroke();
			g2.setStroke(BOTTOM_LINE_STROKE);
			g.drawLine(0, y, getWidth(), y);
			g2.setStroke(stroke);
        }
    }

	@Override
	protected void paintChildren(Graphics g) {
		 super.paintChildren(g);
		 SelectionPainter.paintForBreadcrumbPanel(this, controller, selection, g);
	}


}

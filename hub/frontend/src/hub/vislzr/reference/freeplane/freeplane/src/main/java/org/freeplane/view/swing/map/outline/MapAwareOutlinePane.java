package org.freeplane.view.swing.map.outline;

import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Insets;
import java.awt.Window;
import java.beans.PropertyChangeListener;
import java.lang.ref.WeakReference;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import javax.swing.DefaultComboBoxModel;
import javax.swing.FocusManager;
import javax.swing.Icon;
import javax.swing.JMenu;
import javax.swing.JMenuItem;
import javax.swing.JPopupMenu;
import javax.swing.JToggleButton;
import javax.swing.JToolTip;
import javax.swing.SwingUtilities;
import javax.swing.plaf.basic.BasicMenuItemUI;

import org.freeplane.core.resources.ResourceController;
import org.freeplane.core.ui.components.FreeplaneToolBar;
import org.freeplane.core.ui.textchanger.TranslatedElementFactory;
import org.freeplane.core.util.TextUtils;
import org.freeplane.features.bookmarks.mindmapmode.MapBookmarks;
import org.freeplane.features.filter.Filter;
import org.freeplane.features.filter.FilterController;
import org.freeplane.features.filter.FilterUpdateListener;
import org.freeplane.features.filter.condition.ASelectableCondition;
import org.freeplane.features.icon.factory.IconStoreFactory;
import org.freeplane.features.map.IMapChangeListener;
import org.freeplane.features.map.IMapSelection;
import org.freeplane.features.map.INodeChangeListener;
import org.freeplane.features.map.MapChangeEvent;
import org.freeplane.features.map.MapController;
import org.freeplane.features.map.MapModel;
import org.freeplane.features.map.NodeChangeEvent;
import org.freeplane.features.map.NodeDeletionEvent;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.map.NodeMoveEvent;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.ui.FocusOutlineAction;
import org.freeplane.features.ui.IMapViewChangeListener;
import org.freeplane.features.ui.IMapViewManager;
import org.freeplane.main.application.AuxillaryEditorSplitPane;
import org.freeplane.view.swing.map.MapView;
import org.freeplane.view.swing.map.outline.ScrollableTreePanel.ScrollMode;

public class MapAwareOutlinePane extends OutlinePane implements IMapViewChangeListener, IMapChangeListener, INodeChangeListener {
    private static final String FILTER_ICON = "filter_icon";
	private static final long serialVersionUID = 1L;
    private static final Icon BOOKMARK_ICON = IconStoreFactory.ICON_STORE.getUIIcon("node-bookmark.svg").getIcon();
    private static final Icon SYNC_ICON = ResourceController.getResourceController().getIcon("/images/sync.svg?useAccentColor=true");
    private static final Icon JUMPIN_ICON = ResourceController.getResourceController().getIcon("/images/syncJumpIn.svg?useAccentColor=true");
    private static final Icon QUICK_FILTER_ICON = ResourceController.getResourceController().getIcon("/images/apply_quick_filter.svg?useAccentColor=true");
    private static final Icon FILTER_BUTTON_ICON = ResourceController.getResourceController().getIcon("filterIcon");
    private static final Icon REMOVE_FILTER_ICON = ResourceController.getResourceController().getIcon("ApplyNoFilteringAction.icon");
    private static final TreeNode NO_MAP_AVAILABLE = new TreeNode("empty", () -> TextUtils.getText("no_open_map"));

    private static final String OUTLINE_STATE_KEY = "freeplane.outline.state";

    private TreeNode currentRoot;
    private MapView currentMapView;
    private final OutlineTreeViewStates displayState;
    private final FilterCache bookmarkFilterCache;
    private JToggleButton bookmarkModeToggleButton;
    private JToggleButton syncModeToggleButton;
    private JToggleButton jumpInToggleButton;
    private static final String QUICK_FILTER_HISTORY_SIZE_KEY = "outlineFilterHistorySize";
    private final LinkedList<FilterEntry> quickFilterHistory = new LinkedList<>();
    private final JPopupMenu quickFilterPopupMenu = new JPopupMenu();
    private JToggleButton quickFilterButton;

    MapView getCurrentMapView() {
        return currentMapView;
    }

    private final OutlineSelectedNodeUpdater selectedNodeUpdater;
    private PropertyChangeListener focusListener;


    void handleMapSelectionChanged(NodeModel node) {
        if(node != null && isCurrentMapViewSelected())
			SwingUtilities.invokeLater(this::syncronizeSelectionFollowingMap);
    }

	private boolean isCurrentMapViewSelected() {
		return currentMapView != null && currentMapView.isSelected() && getTreePanel() != null;
	}

	private void syncronizeSelectionFollowingMap() {
		if(isCurrentMapViewSelected()) {
			getTreePanel().getOutlineSelection().setShowsExtendedBreadcrumb(true);
			synchronizeOutlineSelection(SelectionSynchronizationTrigger.MAP, false);
		}
	}

    void synchronizeOutlineSelection(SelectionSynchronizationTrigger synchronizationTrigger, boolean requestFocus) {
        final NodeModel node = currentMapView.getSelected().getNode();
        final ScrollableTreePanel panel = getTreePanel();
        TreeNode target = findOutlineNode(node);
        if(target != null)
            panel.synchronizeOutlineSelection(target, synchronizationTrigger, requestFocus);
    }

    private TreeNode findOutlineNode(NodeModel node) {
        if(node == null)
            return null;

        TreeNode outlineNode = node.getViewers().stream()
                .filter(MapTreeNode.class::isInstance)
                .map(MapTreeNode.class::cast)
                .filter(mapNode -> mapNode.isContainedIn(this))
                .findAny()
                .orElse(null);

        if(outlineNode == null)
            return findOutlineNode(node.getParentNode());
        return outlineNode;
    }

    public MapAwareOutlinePane(AuxillaryEditorSplitPane pane) {
        super(OutlineDisplayMode.DEFAULT, NO_MAP_AVAILABLE);
        this.filterUpdateListener = this::onFilterResultUpdate;
        selectedNodeUpdater = new OutlineSelectedNodeUpdater(this);
        displayState = new OutlineTreeViewStates();
        bookmarkFilterCache = new FilterCache();
        configureToolbar(toolbar);
        pane.changeAuxComponentSide(OutlineGeometry.getInstance().isRightToLeft() ? "right" : "left");
    }



    @Override
    public void addNotify() {
        super.addNotify();
        Controller.getCurrentController().getMapViewManager().addMapViewChangeListener(this);
        try {
            Window w = SwingUtilities.getWindowAncestor(this);
            if (w != null) {
                IMapViewManager mvm = Controller.getCurrentController().getMapViewManager();
                Component mv = mvm.getLastSelectedMapViewContainedIn(w);
                if (mv instanceof MapView) {
                    updateTreeFromMap((MapView) mv);
                    synchronizeOutlineSelection(SelectionSynchronizationTrigger.MAP, false);
                } else {
                    showNoMapState();
                }
            }
        } catch (Exception ignore) {}
    }

    @Override
    public void removeNotify() {
        super.removeNotify();
        Controller.getCurrentController().getMapViewManager().removeMapViewChangeListener(this);
        removeMapListeners();
        cleanupCurrentTree();
    }


    @Override
    public void afterFilterChange(Component view, Filter newFilter) {
        if (displayState.getCurrentMode() == OutlineDisplayMode.BOOKMARK) {
            return;
        }
        if (view instanceof MapView) {
            Window myWindow = SwingUtilities.getWindowAncestor(this);
            if (SwingUtilities.getWindowAncestor(view) == myWindow && displayState.getFilter() == null && displayState.getCurrentMode() != OutlineDisplayMode.BOOKMARK) {
                final Component focusOwner = FocusManager.getCurrentManager().getFocusOwner();
                final boolean requestFocus = focusOwner != null && SwingUtilities.isDescendingFrom(focusOwner, this);
                updateTreeFromMap((MapView) view);
                synchronizeOutlineSelection(SelectionSynchronizationTrigger.MAP, requestFocus);
            }
        }
    }

    private boolean refreshScheduled;
    private final FilterUpdateListener filterUpdateListener;
    private boolean isFilterResultUpdateScheduled;

    private void refreshOutlineLater() {
        if (refreshScheduled) {
            return;
        }
        refreshScheduled = true;
        SwingUtilities.invokeLater(this::refreshOutline);
    }

    private void refreshOutline() {
        if (currentMapView == null) {
            showNoMapState();
        }
        else {
            updateTreeFromMap(currentMapView);
        }
        refreshScheduled = false;
    }


    private void updateTreeFromMap(MapView mapView) {
        updateTreeFromMap(mapView, true);
    }
    private void updateTreeFromMap(MapView mapView, boolean captureState) {
        try {
            removeMapListeners();
            ScrollableTreePanel oldPanel = getTreePanel();
            boolean showsExtendedBreadcrumb;
            if (oldPanel != null) {
				if (captureState) {
				    storeCurrentDisplayState(oldPanel);
				}
				showsExtendedBreadcrumb = oldPanel.getOutlineSelection().showsExtendedBreadcrumb();
			}
            else
            	showsExtendedBreadcrumb = false;

            cleanupCurrentTree();

            if(currentMapView != mapView) {
                detachCurrentMapView();
                currentMapView = mapView;
                mapView.setFilterUpdateListener(filterUpdateListener);
            }
            OutlineTreeViewState saved = loadSavedViewState(currentMapView);
            NodeTreeBuilder builder = new NodeTreeBuilder(mapView, this, saved);
            final OutlineDisplayMode displayMode = displayState.getCurrentMode();
            final MapModel map = mapView.getMap();
            if (displayMode == OutlineDisplayMode.BOOKMARK || !displayState.followsJumpIn()) {
                builder.withRootModel(map.getRootNode());
            }
            Filter effectiveFilter = resolveEffectiveFilter(mapView);
            if (effectiveFilter != null) {
                builder.withFilter(effectiveFilter);
            }
            builder.build();
            currentRoot = builder.getRoot();

            if(displayMode != OutlineDisplayMode.BOOKMARK) {
                final int minimalLevel = displayMode.getMinimalOutlineLevel();
                if (builder.getApplicableState() == null || currentRoot.getExpansionLevel() < minimalLevel) {
                    final int initialLevel = displayMode.getInitialOutlineLevel();
                    currentRoot.applyExpansionLevel(Math.max(initialLevel, minimalLevel));
                }
            }
            else if(currentRoot.getExpansionLevel() < 10000) {
                currentRoot.applyExpansionLevel(10000);
            }
            setRootNode(displayMode, currentRoot);
            ScrollableTreePanel panel = getTreePanel();
            panel.setBackgroundColorSupplier(this::getBackgroundColor);
            panel.setSelectionBridge(new OutlineSelectionBridge(this));
            panel.getOutlineSelection().setShowsExtendedBreadcrumb(showsExtendedBreadcrumb);
            try {
                addMapChangeListeners();
            } catch (Exception ignore) {}
            if (builder.getApplicableState() != null) {
                panel = getTreePanel();
                builder.getApplicableState().applyTo(panel.getRoot());
                panel.updateVisibleNodes(displayMode == OutlineDisplayMode.MAP_VIEW_SYNC ? ScrollMode.SIBLINGS : ScrollMode.SINGLE_ITEM);
            }

            try {
                synchronizeOutlineSelection(SelectionSynchronizationTrigger.MAP, false);
            } catch (Exception ignore) {}

        } catch (Exception e) {
            System.err.println("Failed to update tree from map: " + e.getMessage());
            e.printStackTrace();
            showNoMapState();
        }
    }



    private void addMapChangeListeners() {
        currentMapView.getMap().addMapChangeListener(this);
        MapController mapController = currentMapView.getModeController().getMapController();
		mapController.addNodeSelectionListener(selectedNodeUpdater);
		mapController.addNodeChangeListener(this);
        installFocusListener();
    }

    private void showNoMapState() {
        cleanupCurrentTree();
        removeMapListeners();
        detachCurrentMapView();
        currentRoot = NO_MAP_AVAILABLE;
        bookmarkFilterCache.reset();
        displayState.putViewState(null);
        setRootNode(OutlineDisplayMode.DEFAULT, currentRoot);
        getTreePanel().setBackgroundColorSupplier(null);
    }



    private void removeMapListeners() {
        if (currentMapView != null) {
            try {
                currentMapView.getMap().removeMapChangeListener(this);
                MapController mapController = currentMapView.getModeController().getMapController();
				mapController.removeNodeSelectionListener(selectedNodeUpdater);
				mapController.removeNodeChangeListener(this);
                uninstallFocusListener();
            } catch (Exception ignore) {}
        }
    }

    private void installFocusListener() {
        uninstallFocusListener();
        focusListener = ev -> {
            Object nv = ev.getNewValue();
            if (nv == null) return;
            String action = String.valueOf(nv);
            currentMapView.putClientProperty(FocusOutlineAction.OUTLINE_FOCUS_PROPERTY, null);
            if ("back".equals(action)) {
                currentMapView.getSelected().getMainView().requestFocusInWindow();
                return;
            }
            ScrollableTreePanel panel = getTreePanel();
            if (panel != null) {
                SwingUtilities.invokeLater(() -> {
                    try {
                        IMapSelection sel = Controller.getCurrentController().getSelection();
                        NodeModel selectedNode = sel != null ? sel.getSelected() : null;
                        if (selectedNode != null) {
                            synchronizeOutlineSelection(SelectionSynchronizationTrigger.MAP, true);
                        }
                        panel.synchronizeSelectionButton(true);

                    } catch (Exception ignore) {}
                });
            }
        };
        try {
            currentMapView.addPropertyChangeListener(FocusOutlineAction.OUTLINE_FOCUS_PROPERTY, focusListener);
        } catch (Exception ignore) {}
    }

    private void uninstallFocusListener() {
        if (currentMapView != null && focusListener != null) {
            try {
                currentMapView.removePropertyChangeListener(FocusOutlineAction.OUTLINE_FOCUS_PROPERTY, focusListener);
            } catch (Exception ignore) {}
        }
        focusListener = null;
    }

    @Override
    public void mapChanged(MapChangeEvent event) {
        if (currentMapView == null)
            return;
        final Object property = event.getProperty();
        if(MapView.class.equals(property) && event.getSource() == currentMapView) {
        	event.getMap().removeMapChangeListener(this);
        	updateTreeFromMap(currentMapView);
        	return;
        }
        if (event.getMap() != currentMapView.getMap())
            return;
        if (MapBookmarks.class.equals(property)) {
            if (displayState.getCurrentMode() == OutlineDisplayMode.BOOKMARK) {
                bookmarkFilterCache.refresh(currentMapView);
                refreshOutlineLater();
            }
            return;
        }
        if ((property == IMapViewManager.MapChangeEventProperty.MAP_VIEW_ROOT
                || IMapViewManager.MapChangeEventProperty.MAP_VIEW_ROOT.equals(property))
                && displayState.getCurrentMode() == OutlineDisplayMode.MAP_VIEW) {
            refreshOutlineLater();
            return;
        }
    }


    @Override
    public void afterWindowLastSelectedMapViewChanged(Window window, Component newView) {
        Window myWindow = SwingUtilities.getWindowAncestor(this);
        if (myWindow == window && newView != currentMapView && newView instanceof MapView) {
            updateTreeFromMap((MapView) newView);
            synchronizeOutlineSelection(SelectionSynchronizationTrigger.MAP, false);
        }
    }

    @Override
    public void afterWindowLastSelectedMapViewRemoved(Window window) {
        Window myWindow = SwingUtilities.getWindowAncestor(this);
        if (myWindow == window) {
            detachCurrentMapView();
            showNoMapState();
        }
    }

    private void detachCurrentMapView() {
        if(currentMapView != null) {
            currentMapView.removeFilterUpdateListener(filterUpdateListener);
            currentMapView = null;
        }
    }

    private void cleanupCurrentTree() {
        if (currentRoot != null && currentRoot instanceof MapTreeNode) {
            OutlinePane.cleanupTree(currentRoot);
        }
    }

    private OutlineTreeViewState captureCurrentState(ScrollableTreePanel panel) {
        String firstId = panel.getVisibleNodes().getFirstVisibleNodeId();
        TreeNode root = panel.getRoot();
        Map<String, Integer> levels = new HashMap<>();
        collectExpanded(root, levels);
        String rootId = null;
        try {
            if (currentMapView != null && currentMapView.getRoot() != null && currentMapView.getRoot().getNode() != null) {
                rootId = currentMapView.getRoot().getNode().getID();
            }
        } catch (Exception ignore) {}
        Filter stateFilter = displayState.getCurrentMode() == OutlineDisplayMode.BOOKMARK
                ? bookmarkFilterCache.current()
                : currentMapView != null ? currentMapView.getFilter() : null;
        WeakReference<Filter> ref = new WeakReference<>(stateFilter);
        return new OutlineTreeViewState(firstId, levels, rootId, ref);
    }

    private void collectExpanded(TreeNode node, Map<String, Integer> out) {
        int lvl = node.getExpansionLevel();
        if (lvl > 0) out.put(node.getId(), lvl);
        for (TreeNode c : node.getChildren()) collectExpanded(c, out);
    }




    private void configureToolbar(FreeplaneToolBar toolbar) {
        bookmarkModeToggleButton = new JToggleButton(BOOKMARK_ICON);
        TranslatedElementFactory.createTooltip(bookmarkModeToggleButton, "outline.showBookmarks");
        configureModeToggleButton(bookmarkModeToggleButton, OutlineDisplayMode.BOOKMARK);
        toolbar.add(bookmarkModeToggleButton, 0);
        syncModeToggleButton = new JToggleButton(SYNC_ICON);
        syncModeToggleButton.setSelected(displayState.getCurrentMode() == OutlineDisplayMode.MAP_VIEW_SYNC);
        TranslatedElementFactory.createTooltip(syncModeToggleButton, "outline.followSelection");
        configureModeToggleButton(syncModeToggleButton, OutlineDisplayMode.MAP_VIEW_SYNC);
        toolbar.add(syncModeToggleButton, 1);
        jumpInToggleButton = new JToggleButton(JUMPIN_ICON);
        TranslatedElementFactory.createTooltip(jumpInToggleButton, "outline.followRoot");
        configureJumpinToggleButton(jumpInToggleButton);
        toolbar.add(jumpInToggleButton, 2);

        quickFilterButton = new JToggleButton(FILTER_BUTTON_ICON) {
            @Override
            public JToolTip createToolTip() {
                JToolTip quickFilterToolTip = new QuickFilterToolTip(this);
                quickFilterToolTip.setComponent(this);
                return quickFilterToolTip;
            }
        };
        TranslatedElementFactory.createTooltip(quickFilterButton, "outline.filter");
        configureQuickFilterToggleButton(quickFilterButton);
        toolbar.add(quickFilterButton, 3);
    }

    private void configureModeToggleButton(JToggleButton toggleButton, OutlineDisplayMode mode) {
        toggleButton.setFocusable(false);
        toggleButton.addActionListener(e -> {
            boolean isSelected = toggleButton.isSelected();
            OutlineDisplayMode targetMode = isSelected
                    ? mode
                    : OutlineDisplayMode.MAP_VIEW;
            setOutlineDisplayMode(targetMode, displayState.getFilter(), displayState.followsJumpIn());
            if(mode == OutlineDisplayMode.MAP_VIEW_SYNC) {
                ResourceController.getResourceController().setProperty(OutlineTreeViewStates.OUTLINE_DISPLAY_MODE_SYNC_PROPERTY, isSelected);
            }
        });
    }
    private void configureJumpinToggleButton(JToggleButton toggleButton) {
        toggleButton.setFocusable(false);
        toggleButton.setSelected(displayState.followsJumpIn());
        toggleButton.addActionListener(e -> setFollowsJumpIn(toggleButton.isSelected()));
    }

    private void configureQuickFilterToggleButton(JToggleButton toggleButton) {
        toggleButton.setFocusable(false);
        toggleButton.setSelected(displayState.getFilter() != null);
        toggleButton.addActionListener(e -> {
            toggleButton.setSelected(displayState.getFilter() != null);
            showQuickFilterMenu(toggleButton);
        });
    }

    private void showQuickFilterMenu(JToggleButton invoker) {
        quickFilterPopupMenu.removeAll();
        if (displayState.getFilter() != null) {
            JMenuItem removeFilter = TranslatedElementFactory.createMenuItem("outline.filter.remove");
            removeFilter.addActionListener(e -> setQuickFilter(false));
            removeFilter.setIcon(REMOVE_FILTER_ICON);
            TranslatedElementFactory.createTooltip(removeFilter, "outline.filter");
            quickFilterPopupMenu.add(removeFilter);
        }
        JMenuItem addFilter = TranslatedElementFactory.createMenuItem("outline.filter");
        addFilter.addActionListener(e -> setQuickFilter(true));
        addFilter.setIcon(QUICK_FILTER_ICON);
        quickFilterPopupMenu.add(addFilter);
        if (!quickFilterHistory.isEmpty()) {
            JMenu recentFiltersMenu = TranslatedElementFactory.createMenu("outline.recentFilters");
            quickFilterPopupMenu.add(recentFiltersMenu);
            addHistoryMenuItems(recentFiltersMenu);
        }
        FilterController filterController = FilterController.getCurrentFilterController();
        DefaultComboBoxModel filterConditions = filterController.getFilterConditions();
        if(filterConditions.getSize() > FilterController.USER_DEFINED_CONDITION_START_INDEX) {
                JMenu predefinedConditionsMenu = TranslatedElementFactory.createMenu("outline.predefinedFilters");
                quickFilterPopupMenu.add(predefinedConditionsMenu);
                for(int conditionIndex = FilterController.USER_DEFINED_CONDITION_START_INDEX;
                    conditionIndex < filterConditions.getSize();
                    conditionIndex++) {
                ASelectableCondition condition = (ASelectableCondition) filterConditions.getElementAt(conditionIndex);
                Filter filter = filterController.createFilter(condition, null);
                Icon icon = filter.createIcon(quickFilterButton.getFontMetrics(quickFilterButton.getFont()));
                JMenuItem menuItem = new FilterEntry(filter, icon).createMenuItem(this);
                predefinedConditionsMenu.add(menuItem);
            }
        }
        if (quickFilterPopupMenu.getComponentCount() > 0) {
            quickFilterPopupMenu.show(invoker, 0, invoker.getHeight());
        }
    }

    private void addHistoryMenuItems(JMenu menu) {
        for (FilterEntry entry : quickFilterHistory) {
            JMenuItem historyItem = entry.createMenuItem(this);
			menu.add(historyItem);
        }
    }

	private void setQuickFilter(boolean enable) {
        final Filter filter;
        if(enable) {
            FilterController filterController = FilterController.getCurrentFilterController();
            filter = filterController.createQuickFilter(null);
            if(filter == null) {
                quickFilterButton.setSelected(false);
                clearQuickFilterIcon();
            } else {
                Icon icon = filter.createIcon(quickFilterButton.getFontMetrics(quickFilterButton.getFont()));
                registerQuickFilterHistory(filter, icon);
            }
        }
        else {
            clearQuickFilterIcon();
            filter = null;
        }
        if(displayState.getFilter() != filter)
            setOutlineDisplayMode(displayState.getCurrentMode(), filter, displayState.followsJumpIn());
    }

    private void clearQuickFilterIcon() {
        quickFilterButton.putClientProperty(FILTER_ICON, null);
        quickFilterButton.repaint();
    }

    private void registerQuickFilterHistory(Filter filter, Icon icon) {
        if(filter == null || icon == null) {
            return;
        }
        quickFilterButton.putClientProperty(FILTER_ICON, icon);
        quickFilterButton.repaint();
        quickFilterHistory.removeIf(entry -> entry.filter == filter);
        quickFilterHistory.addFirst(new FilterEntry(filter, icon));
        while(quickFilterHistory.size() > ResourceController.getResourceController().getIntProperty(QUICK_FILTER_HISTORY_SIZE_KEY, 10)) {
            quickFilterHistory.removeLast();
        }
    }

    private void applyQuickFilter(FilterEntry entry) {
        if(entry == null) {
            return;
        }
        quickFilterButton.setSelected(true);
        registerQuickFilterHistory(entry.filter, entry.icon);
        setOutlineDisplayMode(displayState.getCurrentMode(), entry.filter, displayState.followsJumpIn());
    }

    private void setFollowsJumpIn(final boolean followsJumpIn) {
        setOutlineDisplayMode(displayState.getCurrentMode(), displayState.getFilter(), followsJumpIn);
    }

    public void setOutlineDisplayMode(OutlineDisplayMode displayMode, final Filter filter, final boolean followsJumpIn) {
        final OutlineDisplayMode lastMode = displayState.getCurrentMode();
        final boolean lastFollowsJumpIn = displayState.followsJumpIn();
        final Filter lastFilter = displayState.getFilter();
        if (displayMode == null || displayMode == lastMode && followsJumpIn == lastFollowsJumpIn && filter == lastFilter) {
            syncToggleWithMode();
            return;
        }
        displayState.setCurrentMode(displayMode);
        displayState.setFollowsJumpIn(followsJumpIn);
        displayState.setFilter(filter);
        ScrollableTreePanel panel = getTreePanel();
        if (currentMapView != null) {
            if (lastMode.baseMode() != displayMode.baseMode() || followsJumpIn != lastFollowsJumpIn || filter != lastFilter) {
                storeCurrentDisplayState(panel);
                updateTreeFromMap(currentMapView, false);
            }
            else
                panel.setDisplayMode(displayMode);

            synchronizeOutlineSelection(SelectionSynchronizationTrigger.MAP, false);
        }
        syncToggleWithMode();
    }

    private void syncToggleWithMode() {
        boolean bookmarkSelected = displayState.getCurrentMode() == OutlineDisplayMode.BOOKMARK;
        if (bookmarkModeToggleButton.isSelected() != bookmarkSelected) {
            bookmarkModeToggleButton.setSelected(bookmarkSelected);
        }
        boolean syncSelected = displayState.getCurrentMode() == OutlineDisplayMode.MAP_VIEW_SYNC;
        if (syncModeToggleButton.isSelected() != syncSelected) {
            syncModeToggleButton.setSelected(syncSelected);
        }
        final boolean followsJumpIn = displayState.followsJumpIn();
        if (jumpInToggleButton.isSelected() != followsJumpIn) {
            bookmarkModeToggleButton.setSelected(followsJumpIn);
        }
        final boolean filters = displayState.getFilter() != null;
        if (quickFilterButton.isSelected() != filters) {
            quickFilterButton.setSelected(filters);
        }
    }

    private void storeCurrentDisplayState(ScrollableTreePanel panel) {
        OutlineTreeViewState state = captureCurrentState(panel);
        if (state != null) {
            displayState.putViewState(state);
            storeDisplayStatesOnMapView();
        }
    }

    private void storeDisplayStatesOnMapView() {
        if (currentMapView == null) {
            return;
        }
        currentMapView.putClientProperty(OUTLINE_STATE_KEY, displayState.copy());
    }

    private OutlineTreeViewState loadSavedViewState(MapView mapView) {
        if (mapView == null) {
            return null;
        }
        try {
            OutlineTreeViewStates property = (OutlineTreeViewStates) mapView.getClientProperty(OUTLINE_STATE_KEY);
            displayState.loadFrom(property);
        } catch (Exception ignore) {}
        syncToggleWithMode();
        return displayState.getViewState();
    }

    private boolean containsBookmark(NodeModel node) {
        if (node == null) {
            return false;
        }
        MapModel mapModel = node.getMap();
        return mapModel != null && MapBookmarks.of(mapModel).contains(node.getID());
    }

    private Color getBackgroundColor() {
        if(currentMapView == null)
            return null;
        boolean useColoredOutlineItems = ResourceController.getResourceController().getBooleanProperty("useColoredOutlineItems", false);
        if(useColoredOutlineItems)
            return currentMapView.getBackground();
        else
            return null;
    }

    @Override
    OutlineDisplayMode getDisplayMode() {
        return displayState.getCurrentMode();
    }

    private Filter resolveEffectiveFilter(MapView mapView) {
        if (mapView == null) {
            return null;
        }
        OutlineDisplayMode mode = displayState.getCurrentMode();
        if (mode == OutlineDisplayMode.BOOKMARK) {
            return bookmarkFilterCache.prepare(mapView,
                    () -> Filter.createFilter(this::containsBookmark, true, false, false, null));
        }
        Filter filter = displayState.getFilter();
        if (filter != null) {
            filter.calculateFilterResults(mapView.getMap());
        }
        return filter;
    }

    private void onFilterResultUpdate(Filter filter, @SuppressWarnings("unused") NodeModel node) {
        if(! isFilterResultUpdateScheduled && (displayState.getFilter() == null || displayState.getFilter() == filter)) {
            isFilterResultUpdateScheduled = true;
            MapView updatedView = currentMapView;
            SwingUtilities.invokeLater(() -> {
                isFilterResultUpdateScheduled = false;
                if(updatedView == currentMapView)
                    updateTreeFromMap(currentMapView, false);
            });
        }
    }

    @Override
    void updateNodeTitle(TreeNode node) {
        if(! isFilterResultUpdateScheduled)
            super.updateNodeTitle(node);
    }

    @Override
    void rebuildFromNode(TreeNode node) {
        if(! isFilterResultUpdateScheduled && node instanceof MapTreeNode) {
            MapTreeNode existingSubtreeRoot = (MapTreeNode) node;
            MapView mapView = getCurrentMapView();
            if (mapView != null && existingSubtreeRoot.isContainedIn(this)) {
                OutlineTreeViewState state = displayState.getViewState();
                NodeTreeBuilder builder = new NodeTreeBuilder(mapView, this, state);
                Filter effectiveFilter = resolveEffectiveFilter(mapView);
                if (effectiveFilter != null) {
                    builder.withFilter(effectiveFilter);
                }
                builder.rebuildSubtree(existingSubtreeRoot);
            }
        }
        if(! isFilterResultUpdateScheduled && node != null) {
			super.rebuildFromNode(node);
		}
    }

    @Override
    public void nodeChanged(NodeChangeEvent event) {
        NodeModel node = event.getNode();
        updateFilterResults(node);
    }

    @Override
    public void onNodeDeleted(NodeDeletionEvent nodeDeletionEvent) {
        updateFilterResults(nodeDeletionEvent.parent);
        if(! isFilterResultUpdateScheduled) {
        	TreeNode outlineNode = findOutlineNode(nodeDeletionEvent.parent);
        	rebuildFromNode(outlineNode);
        }
    }



    @Override
	public void onNodeMoved(NodeMoveEvent nodeMoveEvent) {
        NodeModel oldParent = nodeMoveEvent.oldParent;
        NodeModel newParent = nodeMoveEvent.newParent;

        boolean rebuildsOldParentSubtree = ! oldParent.isDescendantOf(newParent);
        boolean rebuildsNewParentSubtree = newParent != oldParent && ! newParent.isDescendantOf(oldParent);
		if(rebuildsOldParentSubtree)
        	updateFilterResults(oldParent);
		if(rebuildsNewParentSubtree)
			updateFilterResults(newParent);
        if(! isFilterResultUpdateScheduled) {
    		if(rebuildsOldParentSubtree)
            	rebuildFromNode(findOutlineNode(oldParent));
    		if(rebuildsNewParentSubtree)
            	rebuildFromNode(findOutlineNode(newParent));
        }

	}

	@Override
    public void onNodeInserted(NodeModel parent, NodeModel child, int newIndex) {
    	updateFilterResults(child);
        if(! isFilterResultUpdateScheduled) {
        	TreeNode outlineNode = findOutlineNode(parent);
        	rebuildFromNode(outlineNode);
        }
    }

    private void updateFilterResults(NodeModel node) {
        if (currentMapView == null)
            return;
        Filter filter = displayState.getFilter();
        if (filter == null)
            return;
        if (node.getMap() != currentMapView.getMap())
            return;
        filter.updateFilterResults(node, filterUpdateListener);
    }

    List<TreeNode> collectNodesToSelection(TreeNode ancestor) {
        if(! (ancestor instanceof MapTreeNode))
            return Collections.emptyList();
        final MapView mv = getCurrentMapView();
        if (mv == null)
            return Collections.emptyList();
        final NodeModel selected = mv.getSelected().getNode();
        final NodeModel ancestorNode = ((MapTreeNode) ancestor).getNodeModel();
        if (! selected.isDescendantOf(ancestorNode))
            return Collections.emptyList();
        final LinkedList<TreeNode> nodes = new LinkedList<>();
        for(NodeModel node = selected; node != ancestorNode; node = node.getParentNode()) {
        	nodes.addFirst(((MapTreeNode) ancestor).createNode(node));
        }
        for(TreeNode node : nodes)
            node.setLevel(TreeNode.UNKNOWN_LEVEL);
        return nodes;
    }

    static final class FilterEntry {
        private final Filter filter;
        private final Icon icon;

        private FilterEntry(Filter filter, Icon icon) {
            this.filter = filter;
            this.icon = icon;
        }

		private JMenuItem createMenuItem(MapAwareOutlinePane mapAwareOutlinePane) {
			JMenuItem filterActionItem = new JMenuItem() {
				private static final long serialVersionUID = 1L;

				@Override
				public void updateUI() {
					setUI(new BasicMenuItemUI());
				}

			};
			filterActionItem.setIcon(icon);
			filterActionItem.setText(null);
			TranslatedElementFactory.createTooltip(filterActionItem, "outline.filter");
			filterActionItem.addActionListener(e -> mapAwareOutlinePane.applyQuickFilter(this));
			filterActionItem.setMaximumSize(filterActionItem.getPreferredSize());
			filterActionItem.setAlignmentX(LEFT_ALIGNMENT);
			return filterActionItem;
		}
    }

    private static final class QuickFilterToolTip extends JToolTip {
        private static final long serialVersionUID = 1L;
        private final JToggleButton sourceButton;
        private boolean suppressDefaultText;

        private QuickFilterToolTip(JToggleButton sourceButton) {
            this.sourceButton = sourceButton;
        }

        @Override
        public Dimension getPreferredSize() {
            Icon filterIcon = getFilterIcon();
            String tooltipText = super.getTipText();
            if (filterIcon == null || tooltipText == null || tooltipText.isEmpty()) {
                return super.getPreferredSize();
            }
            Insets insets = getInsets();
            FontMetrics fontMetrics = getFontMetrics(getFont());
            int textHeight = fontMetrics != null ? fontMetrics.getHeight() : filterIcon.getIconHeight();
            int requiredHeight = Math.max(textHeight, filterIcon.getIconHeight()) + insets.top + insets.bottom;
            int requiredWidth = filterIcon.getIconWidth() + insets.left + insets.right;
            return new Dimension(requiredWidth, requiredHeight);
        }

        @Override
        protected void paintComponent(Graphics graphics) {
            Icon filterIcon = getFilterIcon();
            String tooltipText = super.getTipText();
            if (filterIcon == null || tooltipText == null || tooltipText.isEmpty()) {
                suppressDefaultText = false;
                super.paintComponent(graphics);
                return;
            }
            suppressDefaultText = true;
            super.paintComponent(graphics);
            suppressDefaultText = false;

            Insets insets = getInsets();
            int iconYPosition = insets.top + (getHeight() - insets.top - insets.bottom - filterIcon.getIconHeight()) / 2;
            int iconXPosition = insets.left;
            filterIcon.paintIcon(this, graphics, iconXPosition, iconYPosition);
        }

        @Override
        public String getTipText() {
            if (suppressDefaultText) {
                return "";
            }
            return super.getTipText();
        }

        private Icon getFilterIcon() {
            Object clientProperty = sourceButton.getClientProperty(FILTER_ICON);
            return clientProperty instanceof Icon ? (Icon) clientProperty : null;
        }
    }
}

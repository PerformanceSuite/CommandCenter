package org.freeplane.view.swing.map.outline;

import javax.swing.JScrollPane;

class OutlineController implements OutlineActionTarget {
    private final ScrollableTreePanel treePanel;
    @SuppressWarnings("unused")
    private final JScrollPane scrollPane;

    OutlineController(ScrollableTreePanel treePanel,  JScrollPane scrollPane) {
        this.treePanel = treePanel;
        this.scrollPane = scrollPane;
    }

    int getRowHeight() {
        return treePanel.getRowHeight();
    }

    int getViewportWidth() {
        return treePanel.getViewportWidth();
    }

    int calcTextButtonX(int level) {
        return treePanel.calcTextButtonX(level);
    }

	BreadcrumbMode getBreadcrumbMode() {
		return treePanel.getBreadcrumbMode();
	}

    void toggleBreadcrumbNodeExpansion(TreeNode node) {
        treePanel.toggleBreadcrumbNodeExpansion(node, true);
    }

    @Override
    public void toggleExpandSelected() { treePanel.toggleExpandSelected(); }

    @Override
    public void selectSelectedInMap() { treePanel.selectSelectedInMap(); }

    void selectNode(TreeNode node, boolean requestFocus) {
        if (node == null) return;
        treePanel.setSelectedNode(node, requestFocus);
    }

    @Override public void navigateUp() { treePanel.navigateUp(); }
    @Override public void navigateDown() { treePanel.navigateDown(); }
    @Override public void navigatePageUp() { treePanel.navigatePageUp(); }
    @Override public void navigatePageDown() { treePanel.navigatePageDown(); }
    @Override public void collapseOrGoToParent() { treePanel.collapseOrGoToParent(); }
    @Override public void expandOrGoToChild() { treePanel.expandOrGoToChild(); }
    @Override public void expandSelectedMore() { treePanel.expandSelectedMore(); }
    @Override public void reduceSelectedExpansion() { treePanel.reduceSelectedExpansion(); }

    void showNavigationButtonsForBreadcrumb(TreeNode node, int rowIndex) {
        treePanel.showNavigationButtonsForBreadcrumb(node, rowIndex);
    }

    void setBreadcrumbHeight(int height) {
        treePanel.setBreadcrumbHeight(height);
    }

    TreeNode getHoveredNode() {
        return treePanel.getVisibleNodes().getHoveredNode();
    }

    void resetHoveredNode() {
        treePanel.getVisibleNodes().setHoveredNode(null);
    }

    boolean isHoveredNodeContainedInBreadcrumb() {
        return treePanel.getVisibleNodes().isHoveredNodeContainedInBreadcrumb();
    }
}

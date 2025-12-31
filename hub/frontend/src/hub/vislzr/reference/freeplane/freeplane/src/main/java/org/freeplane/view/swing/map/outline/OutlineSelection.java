package org.freeplane.view.swing.map.outline;

class OutlineSelection {
    private TreeNode selectedNode;
    private boolean showsExtendedBreadcrumb;

    OutlineSelection(TreeNode root) {
        this.selectedNode = root;
    }

    void selectNode(TreeNode node) {
        if (node != null) {
        	selectedNode = node;
        }
    }

    TreeNode getSelectedNode() {
        return selectedNode;
    }

    private boolean isSelected(String nodeId) {
        return selectedNode != null && selectedNode.getId().equals(nodeId);
    }

    boolean isSelected(TreeNode node) {
        return node != null && isSelected(node.getId());
    }

    public boolean showsExtendedBreadcrumb() {
		return showsExtendedBreadcrumb;
	}

	public void setShowsExtendedBreadcrumb(boolean showsExtendedBreadcrumb) {
		this.showsExtendedBreadcrumb = showsExtendedBreadcrumb;
	}


}

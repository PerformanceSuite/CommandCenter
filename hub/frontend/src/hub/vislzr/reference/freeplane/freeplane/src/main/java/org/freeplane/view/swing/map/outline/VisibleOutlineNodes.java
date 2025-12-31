package org.freeplane.view.swing.map.outline;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

class VisibleOutlineNodes {
    private final TreeNode root;
    private List<TreeNode> visibleNodes = new ArrayList<>();
    private final Map<String, Integer> indexById = new HashMap<>();
    private int breadcrumbHeight = 0;
    private int blockPanelY = 0;
    private TreeNode hoveredNode;
    private String firstVisibleNodeId;
	private boolean isHoveredNodeContainedInBreadcrumb;

    VisibleOutlineNodes(TreeNode root) {
        this.root = root;
        this.hoveredNode = null;
        updateVisibleNodes();
    }

    void updateVisibleNodes() {
        visibleNodes.clear();
        indexById.clear();
        buildVisibleList(root);
        for (int i = 0; i < visibleNodes.size(); i++) {
            TreeNode n = visibleNodes.get(i);
            if (n != null) indexById.put(n.getId(), i);
        }
    }

    private void buildVisibleList(TreeNode node) {
        visibleNodes.add(node);
        if (node.isExpanded()) {
            for (TreeNode child : node.getChildren()) {
                buildVisibleList(child);
            }
        }
    }

    int getVisibleNodeCount() {
        return visibleNodes.size();
    }

    String getFirstVisibleNodeId() {
        return firstVisibleNodeId;
    }

    void setFirstVisibleNodeId(String id) {
        this.firstVisibleNodeId = id;
    }

    int findNodeIndexById(String id) {
        if (id == null) {
            return -1;
        }
        Integer idx = indexById.get(id);
        return idx != null ? idx : -1;
    }

    int findNodeIndexInVisibleList(TreeNode node) {
        if (node == null) return -1;
        Integer idx = indexById.get(node.getId());
        return idx != null ? idx : -1;
    }

	TreeNode findNodeById(String id) {
		int index = findNodeIndexById(id);
		return getNodeAtVisibleIndex(index);
	}

	int getBreadcrumbHeight() {
        return breadcrumbHeight;
    }

    void setBreadcrumbHeight(int height) {
        this.breadcrumbHeight = height;
    }

    int getBlockPanelY() {
		return blockPanelY;
	}

	void setBlockPanelY(int blockPanelY) {
		this.blockPanelY = blockPanelY;
	}

	TreeNode getHoveredNode() {
        return hoveredNode;
    }

    void setHoveredNode(TreeNode node, boolean isBreadcrumb) {
        this.hoveredNode = node;
		this.isHoveredNodeContainedInBreadcrumb = isBreadcrumb;
    }

    void setHoveredNode(TreeNode node) {
        this.hoveredNode = node;
    }

    boolean isHoveredNodeContainedInBreadcrumb() {
		return isHoveredNodeContainedInBreadcrumb;
	}

	TreeNode getNodeAtVisibleIndex(int index) {
        if (index < 0 || index >= visibleNodes.size()) return null;
        return visibleNodes.get(index);
    }

    String getNodeIdAtVisibleIndex(int index) {
        TreeNode f = getNodeAtVisibleIndex(index);
        return f != null ? f.getId() : null;
    }
}

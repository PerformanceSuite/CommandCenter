package org.freeplane.view.swing.map.outline;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

final class OutlineSelectionHistory {
    private final Map<String, String> lastSelectedChildByParent = new HashMap<>();

    void record(TreeNode node) {
        if (node == null) {
            return;
        }
        TreeNode parent = node.getParent();
        if (parent == null) {
            return;
        }
        lastSelectedChildByParent.put(parent.getId(), node.getId());
    }

    TreeNode preferredChild(TreeNode parent) {
        if (parent == null) {
            return null;
        }
        List<TreeNode> children = parent.getChildren();
        if (children.isEmpty()) {
            return null;
        }
        String preferredChildId = lastSelectedChildByParent.get(parent.getId());
        if (preferredChildId != null) {
            for (TreeNode child : children) {
                if (preferredChildId.equals(child.getId())) {
                    return child;
                }
            }
        }
        return children.get(0);
    }
}

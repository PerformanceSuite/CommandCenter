package org.freeplane.view.swing.map.outline;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.lang.ref.WeakReference;

import org.freeplane.features.filter.Filter;

class OutlineTreeViewState {
    private final String firstVisibleNodeId;
    private final Map<String, Integer> expansionLevels;
    private final String rootNodeId;
    private final WeakReference<Filter> savedFilter;

    OutlineTreeViewState(String firstVisibleNodeId, Map<String, Integer> expansionLevels, String rootNodeId, WeakReference<Filter> savedFilter) {
        this.firstVisibleNodeId = firstVisibleNodeId;
        this.expansionLevels = new HashMap<>(expansionLevels);
        this.rootNodeId = rootNodeId;
        this.savedFilter = savedFilter;
    }

    String getFirstVisibleNodeId() { return firstVisibleNodeId; }
    String getRootNodeId() { return rootNodeId; }
    WeakReference<Filter> getSavedFilter() { return savedFilter; }

    void applyTo(TreeNode root) {
        Map<String, TreeNode> byId = new HashMap<>();
        Map<String, Integer> levelById = new HashMap<>();
        collect(root, 0, byId, levelById);

        List<Map.Entry<String, Integer>> ordered = new ArrayList<>();
        for (Map.Entry<String, Integer> e : expansionLevels.entrySet()) {
            if (byId.containsKey(e.getKey())) ordered.add(e);
        }
        Collections.sort(ordered, Comparator.comparingInt(e -> levelById.get(e.getKey())));
        for (Map.Entry<String, Integer> e : ordered) {
            TreeNode n = byId.get(e.getKey());
            if (n != null) n.applyExpansionLevel(e.getValue());
        }
    }

    private void collect(TreeNode node, int level, Map<String, TreeNode> byId, Map<String, Integer> levelById) {
        byId.put(node.getId(), node);
        levelById.put(node.getId(), level);
        for (TreeNode c : node.getChildren()) collect(c, level + 1, byId, levelById);
    }
}

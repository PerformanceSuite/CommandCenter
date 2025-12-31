package org.freeplane.view.swing.map.outline;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

import org.freeplane.features.filter.Filter;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.map.SummaryNode;
import org.freeplane.features.nodestyle.NodeStyleController;
import org.freeplane.view.swing.map.MapView;

class NodeTreeBuilder {
    private final MapView mapView;
    private final MapAwareOutlinePane pane;
    private final OutlineTreeViewState saved;

    private NodeModel rootModel;
    private Filter filter;
    private NodeModel overrideRootModel;
    private Filter overrideFilter;

    private TreeNode root;
    private OutlineTreeViewState applicableState;

    NodeTreeBuilder(MapView mapView, MapAwareOutlinePane pane, OutlineTreeViewState saved) {
        this.mapView = mapView;
        this.pane = pane;
        this.saved = saved;
    }

    NodeTreeBuilder build() {
        initializeRootModel();
        if (rootModel == null) {
            return this;
        }
        initializeFilter();

        boolean canApply = false;
        if (saved != null) {
            String currentRootId = rootModel.getID();
            Filter savedFilter = saved.getSavedFilter() != null ? saved.getSavedFilter().get() : null;
            canApply = Objects.equals(saved.getRootNodeId(), currentRootId) && Objects.equals(savedFilter, filter);
        }
        this.applicableState = canApply ? saved : null;

        MapTreeNode outRoot = new MapTreeNode(rootModel, pane, mapView.getModeController().getExtension(NodeStyleController.class),
        		mapView.getBackground());
        rootModel.addViewer(outRoot);
        this.root = outRoot;

        rebuildDescendants(outRoot, rootModel);

        return this;
    }

    NodeTreeBuilder withRootModel(NodeModel rootModel) {
        this.overrideRootModel = rootModel;
        return this;
    }

    NodeTreeBuilder withFilter(Filter filter) {
        this.overrideFilter = filter;
        return this;
    }

    NodeTreeBuilder rebuildSubtree(MapTreeNode existingSubtreeRoot) {
        if (existingSubtreeRoot == null) {
            return this;
        }
        NodeModel subtreeRootModel = existingSubtreeRoot.getNodeModel();
        if (subtreeRootModel == null) {
            return this;
        }
        this.rootModel = subtreeRootModel;
        initializeFilter();
        rebuildDescendants(existingSubtreeRoot, subtreeRootModel);
        this.root = existingSubtreeRoot;
        this.applicableState = null;
        return this;
    }

    private void initializeRootModel() {
        if (overrideRootModel != null) {
            rootModel = overrideRootModel;
            return;
        }
        rootModel = mapView.getRoot().getNode();
    }

    private void initializeFilter() {
        if (overrideFilter != null) {
            filter = overrideFilter;
            return;
        }
        if (mapView != null) {
            filter = mapView.getFilter();
        } else {
            filter = null;
        }
    }

    private void rebuildDescendants(MapTreeNode parentOut, NodeModel parentModel) {
        clearOutlineChildren(parentOut);
        visitChildren(parentModel, parentOut);
    }

    private void clearOutlineChildren(MapTreeNode parentOut) {
        List<TreeNode> currentChildren = new ArrayList<>(parentOut.getChildren());
        for (TreeNode child : currentChildren) {
            if (child instanceof MapTreeNode) {
                MapTreeNode mapChild = (MapTreeNode) child;
                parentOut.remove(mapChild);
                mapChild.setParent(null);
                mapChild.cleanupListeners();
            }
        }
    }

    private void visitChildren(NodeModel model, MapTreeNode parentOut) {
        for (NodeModel child : model.getChildren()) {
            boolean visible = !(SummaryNode.isSummaryNode(child) || SummaryNode.isFirstGroupNode(child)) && (filter == null || filter.isVisible(child));
            MapTreeNode nextParent = parentOut;
            if (visible) {
                MapTreeNode out = new MapTreeNode(parentOut, child);
                child.addViewer(out);
                nextParent = out;
            }
            visitChildren(child, nextParent);
        }
    }

    TreeNode getRoot() { return root; }
    OutlineTreeViewState getApplicableState() { return applicableState; }
}

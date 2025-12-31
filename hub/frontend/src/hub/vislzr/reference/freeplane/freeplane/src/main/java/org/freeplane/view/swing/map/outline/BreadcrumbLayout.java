package org.freeplane.view.swing.map.outline;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Predicate;
import java.util.function.Supplier;

import javax.swing.JPanel;

import org.freeplane.features.map.NodeModel;
import org.freeplane.features.map.SummaryNode;

final class BreadcrumbLayout {
    private final BreadcrumbPanel breadcrumbPanel;
    private final VisibleOutlineNodes visibleNodes;
    private final NavigationButtons navigationButtons;
    private final OutlineSelection outlineSelection;
    private final Supplier<Boolean> selectionDrivenMode;
    private final Predicate<TreeNode> isNodeInBreadcrumbArea;
    private final Consumer<Integer> breadcrumbHeightUpdater;
    private final JPanel blockPanel;
    private OutlineSelectionBridge selectionBridge;

    BreadcrumbLayout(BreadcrumbPanel breadcrumbPanel,
                     VisibleOutlineNodes visibleNodes,
                     NavigationButtons navigationButtons,
                     OutlineSelection outlineSelection,
                     Supplier<Boolean> selectionDrivenMode,
                     Predicate<TreeNode> isNodeInBreadcrumbArea,
                     Consumer<Integer> breadcrumbHeightUpdater,
                     JPanel blockPanel) {
        this.breadcrumbPanel = breadcrumbPanel;
        this.visibleNodes = visibleNodes;
        this.navigationButtons = navigationButtons;
        this.outlineSelection = outlineSelection;
        this.selectionDrivenMode = selectionDrivenMode;
        this.isNodeInBreadcrumbArea = isNodeInBreadcrumbArea;
        this.breadcrumbHeightUpdater = breadcrumbHeightUpdater;
        this.blockPanel = blockPanel;
    }

    void setSelectionBridge(OutlineSelectionBridge selectionBridge) {
        this.selectionBridge = selectionBridge;
    }

    void updateForSelection() {
        applyState(calculateStateForSelection());
    }

    void updateForFirstVisibleIndex(int index) {
        applyState(calculateStateForIndex(index));
    }

    List<TreeNode> calculateState(int targetFirstIndex) {
        return selectionDrivenMode.get()
                ? calculateStateForSelection()
                : calculateStateForIndex(targetFirstIndex);
    }

    void applyState(List<TreeNode> breadcrumbState) {
        if (breadcrumbState != null) {
            breadcrumbPanel.update(breadcrumbState, false);
        }
        else {
            breadcrumbHeightUpdater.accept(0);
            breadcrumbPanel.removeAll();
            breadcrumbPanel.revalidate();
            breadcrumbPanel.repaint();
        }
        reattachNavigationButtons();
    }

    void reattachNavigationButtons() {
        TreeNode hoveredNode = visibleNodes.getHoveredNode();
        if (hoveredNode == null || hoveredNode.getChildren().isEmpty()) {
            return;
        }

        boolean inBreadcrumb = visibleNodes.isHoveredNodeContainedInBreadcrumb() && isNodeInBreadcrumbArea.test(hoveredNode);
        if (inBreadcrumb) {
            List<TreeNode> breadcrumbNodes = breadcrumbPanel.getCurrentBreadcrumbNodes();
            int rowIndex = breadcrumbNodes.indexOf(hoveredNode);
            if (rowIndex >= 0) {
                navigationButtons.attachToNode(hoveredNode, breadcrumbPanel, rowIndex, rowIndex);
            }
            return;
        }

        int nodeIndex = visibleNodes.findNodeIndexInVisibleList(hoveredNode);
		navigationButtons.attachToNode(hoveredNode, blockPanel, nodeIndex, hoveredNode.getLevel());
    }

    private List<TreeNode> calculateStateForIndex(int firstVisibleNodeIndex) {
        TreeNode breadcrumbTargetNode = visibleNodes.getNodeAtVisibleIndex(firstVisibleNodeIndex);
        if (breadcrumbTargetNode == null) {
            return null;
        }
        return collectBreadcrumbNodes(breadcrumbTargetNode);
    }

    private List<TreeNode> calculateStateForSelection() {
        TreeNode selected = outlineSelection.getSelectedNode();
        if (selected == null) {
        	return null;
        }
        List<TreeNode> nodes;
        if(selected instanceof MapTreeNode)
        	nodes = collectBreadcrumbNodes((MapTreeNode)selected);
        else
        	nodes = collectBreadcrumbNodes(selected);
        nodes.add(selected);
        if (selectionBridge != null && outlineSelection.showsExtendedBreadcrumb()) {
        	List<TreeNode> extraNodes = selectionBridge.collectNodesToSelection(selected);
            if(extraNodes.isEmpty())
            	outlineSelection.setShowsExtendedBreadcrumb(false);
            for(int i = 0; i < extraNodes.size(); i++) {
            	int existingNodeIndex = visibleNodes.findNodeIndexById(extraNodes.get(i).getId());
            	if(existingNodeIndex >= 0)
            		extraNodes.set(i, visibleNodes.getNodeAtVisibleIndex(existingNodeIndex));
            }
			nodes.addAll(extraNodes);
        }
        return nodes;
    }

    private List<TreeNode> collectBreadcrumbNodes(TreeNode fromNode) {
        List<TreeNode> breadcrumbNodes = new ArrayList<>();
        TreeNode current = fromNode.getParent();
        while (current != null) {
            breadcrumbNodes.add(current);
            current = current.getParent();
        }
        Collections.reverse(breadcrumbNodes);
        return breadcrumbNodes;
    }

    private List<TreeNode> collectBreadcrumbNodes(MapTreeNode fromNode) {
        List<TreeNode> breadcrumbNodes = new ArrayList<>();
        MapTreeNode child = fromNode;
        MapTreeNode current = (MapTreeNode) child.getParent();
        while (current != null) {
        	while(child.getNodeModel().getParentNode() != current.getNodeModel()) {
        		NodeModel parentNode = child.getNodeModel().getParentNode();
				child = child.createNode(parentNode);
				if(! SummaryNode.isHidden(parentNode)) {
					child.setLevel(TreeNode.UNKNOWN_LEVEL);
					breadcrumbNodes.add(child);
				}
        	}
            breadcrumbNodes.add(current);
            child = current;
            current = (MapTreeNode) current.getParent();
        }
        Collections.reverse(breadcrumbNodes);
        return breadcrumbNodes;
    }
}

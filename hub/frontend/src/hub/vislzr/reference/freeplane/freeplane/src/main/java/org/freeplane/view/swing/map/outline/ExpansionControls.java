package org.freeplane.view.swing.map.outline;

import javax.swing.SwingUtilities;

import org.freeplane.view.swing.map.outline.ScrollableTreePanel.ScrollMode;

class ExpansionControls {
    private final ScrollableTreePanel treePanel;
	private final OutlineSelection outlineSelection;

    ExpansionControls(ScrollableTreePanel treePanel, OutlineSelection outlineSelection) {
        this.treePanel = treePanel;
		this.outlineSelection = outlineSelection;
    }

    void expandNode(TreeNode node) {
    	if(! node.isExpanded()) {
    		node.expandNodeMore(1);
    		refreshAfterExpansionChange();
    	}
    }

    void collapseNode(TreeNode node) {
    	if(node.isExpanded()) {
    		final int minimalLevel = treePanel.getDisplayMode().getMinimalOutlineLevel();
    		if (node.getLevel() >= minimalLevel) {
    			node.reduceNodeExpansion(0);
    			selectParentIfNeeded();
    			refreshAfterExpansionChange();
    		}
    		else {
    			for (TreeNode child : node.getChildren())
    				collapseNode(child);
    		}
    	}
    }

    void expandNodeMore(TreeNode node) {
    	int currentLevel = node.getMaxExpansionLevel();
    	node.expandNodeMore(currentLevel + 1);
        refreshAfterExpansionChange();
    }

    void reduceNodeExpansion(TreeNode node) {
        int currentLevel = node.getMaxExpansionLevel();
		final int minimalLevel = treePanel.getDisplayMode().getMinimalOutlineLevel();
        if (currentLevel > minimalLevel - node.getLevel()) {
            node.reduceNodeExpansion(currentLevel - 1);
            selectParentIfNeeded();
            refreshAfterExpansionChange();
        }
    }

	private void selectParentIfNeeded() {
		final TreeNode selectedNode = outlineSelection.getSelectedNode();
		if(selectedNode != null && ! selectedNode.isVisible())
			outlineSelection.selectNode(selectedNode.getParent());
	}

    private void refreshAfterExpansionChange() {
    	final boolean wasFocused = treePanel.isNodeButtonFocused();
    	treePanel.updateVisibleNodes(ScrollMode.SINGLE_ITEM);
    	SwingUtilities.invokeLater(() -> {
    		if(wasFocused)
    			treePanel.focusSelectionButtonLater(true);
    		else
    			treePanel.synchronizeSelectionButton(false);
    	});

    }

}

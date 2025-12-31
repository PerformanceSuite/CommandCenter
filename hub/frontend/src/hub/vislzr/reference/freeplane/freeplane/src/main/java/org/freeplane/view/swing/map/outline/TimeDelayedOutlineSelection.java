/*
 * Created on 5 Oct 2025
 *
 * author dimitry
 */
package org.freeplane.view.swing.map.outline;

import java.awt.Component;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;

import javax.swing.SwingUtilities;

import org.freeplane.view.swing.map.MapView;
import org.freeplane.view.swing.ui.NodeSelector;

class TimeDelayedOutlineSelection implements ActionListener {
	private static MapView findMapView(MouseEvent mouseEvent) {
	    Component component = mouseEvent.getComponent();
		final MapAwareOutlinePane pane = (MapAwareOutlinePane)SwingUtilities.getAncestorOfClass(MapAwareOutlinePane.class, component);
		if(pane == null)
			return null;
		return pane.getCurrentMapView();
	}

	static final NodeSelector outlineSelector = new NodeSelector(TimeDelayedOutlineSelection::new, TimeDelayedOutlineSelection::findMapView);

	private final MouseEvent mouseEvent;

	TimeDelayedOutlineSelection(final MouseEvent e) {
		this.mouseEvent = e;
	}

	@Override
	public void actionPerformed(ActionEvent event) {
	    if (mouseEvent.getModifiers() != 0) {
	        return;
	    }
	    final Component component = mouseEvent.getComponent();
	    final MapAwareOutlinePane pane = (MapAwareOutlinePane)SwingUtilities.getAncestorOfClass(MapAwareOutlinePane.class, component);
	    final ScrollableTreePanel treePanel = pane.getTreePanel();
	    final TreeNode node;
	    if(component instanceof NodeButton) {
	    	NodeButton button = ((NodeButton)component);
	    	node = button.getNode();
	    }
	    else {
			node = treePanel.getOutlineSelection().getSelectedNode();
	    }
	    if(node.getLevel() == 0 || node.getParent() != null)
	    	treePanel.setSelectedNode(node, true);
	}
}

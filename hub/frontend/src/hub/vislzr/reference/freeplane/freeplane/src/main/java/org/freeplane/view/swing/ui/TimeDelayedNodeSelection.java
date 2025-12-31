/*
 * Created on 5 Oct 2025
 *
 * author dimitry
 */
package org.freeplane.view.swing.ui;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;

import javax.swing.SwingUtilities;

import org.freeplane.features.map.MapController;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.mode.ModeController;
import org.freeplane.view.swing.map.MapView;
import org.freeplane.view.swing.map.NodeView;

class TimeDelayedNodeSelection implements ActionListener {
	private final MouseEvent mouseEvent;

	TimeDelayedNodeSelection(final MouseEvent e) {
		this.mouseEvent = e;
	}

	@Override
	public void actionPerformed(ActionEvent event) {
	    if (mouseEvent.getModifiers() != 0) {
	        return;
	    }
	    try {
	        Controller controller = Controller.getCurrentController();
	        ModeController modeController = controller.getModeController();
            if (!modeController.isBlocked() && controller.getSelection().size() <= 1) {
	            final NodeView nodeV = (NodeView) SwingUtilities.getAncestorOfClass(NodeView.class,
	                    mouseEvent.getComponent());
	            MapView map = nodeV.getMap();
	            if (nodeV.isDisplayable() && nodeV.getNode().hasVisibleContent(map.getFilter())) {
	                map.select();
	                NodeModel node = nodeV.getNode();
	                MouseEventActor.INSTANCE.withMouseEvent( () -> {
                        	MapController mapController = modeController.getMapController();
                        	controller.getSelection().selectAsTheOnlyOneSelected(node);
                        	mapController.scrollNodeTreeAfterSelect(node);
						});
	            }
	        }
	    }
	    catch (NullPointerException e) {
	    }
	}
}

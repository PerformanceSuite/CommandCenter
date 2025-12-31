/*
 * Created on 6 Sept 2025
 *
 * author dimitry
 */
package org.freeplane.view.swing.map.outline;

import java.util.List;

import javax.swing.SwingUtilities;

import org.freeplane.features.map.IMapSelection;
import org.freeplane.features.map.MapController;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.mode.Controller;
import org.freeplane.view.swing.map.MapView;
import org.freeplane.view.swing.map.NodeView;

class OutlineSelectionBridge {

    private final MapAwareOutlinePane outlinePane;

	OutlineSelectionBridge(MapAwareOutlinePane outlinePane) {
		this.outlinePane = outlinePane;
    }

    public void selectMapNodeById(String nodeId) {
        final MapView mv = outlinePane.getCurrentMapView();
        if (mv == null) return;
        Controller controller = Controller.getCurrentController();
        NodeModel current = null;
        IMapSelection selection = controller.getSelection();
        if (selection != null) current = selection.getSelected();
        if (current != null && nodeId != null && nodeId.equals(current.getID())) return;

        NodeModel target = mv.getMap().getNodeForID(nodeId);
        if (target == null) return;

        MapController mapController = mv.getModeController().getMapController();
		mapController.displayNode(target);
        final NodeView nodeView = mv.getNodeView(target);
        mv.selectAsTheOnlyOneSelected(nodeView, false);
        mapController.scrollNodeTreeAfterSelect(nodeView.getNode());
        SwingUtilities.invokeLater(this::focusMapNode);
    }

	void synchronizeOutlineSelection(SelectionSynchronizationTrigger selectionSynchronizationTrigger, boolean requestFocusInWindow) {
		outlinePane.synchronizeOutlineSelection(selectionSynchronizationTrigger, requestFocusInWindow);
	}

	private void focusMapNode() {
        final MapView mv = outlinePane.getCurrentMapView();
        if (mv == null) return;
        mv.getSelected().getMainView().requestFocusInWindow();
	}

	List<TreeNode> collectNodesToSelection(TreeNode ancestor) {
		return outlinePane.collectNodesToSelection(ancestor);
	}

}

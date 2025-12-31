package org.freeplane.features.bookmarks.mindmapmode;

import javax.swing.SwingUtilities;

import org.freeplane.features.filter.Filter;
import org.freeplane.features.filter.FilterController;
import org.freeplane.features.filter.hidden.NodeVisibility;
import org.freeplane.features.map.IMapSelection;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.ui.IMapViewManager;

public class NodeNavigator {
	private final NodeModel node;

	public NodeNavigator(NodeModel node) {
		super();
		this.node = node;
	}

	public NodeModel getNode() {
		return node;
	}

	public void open(boolean openAsRoot) {
		final Controller controller = Controller.getCurrentController();
		final IMapViewManager mapViewManager = controller.getMapViewManager();
		final IMapSelection mapSelection = controller.getSelection();
		final NodeModel nodeToSelect;
		if(openAsRoot) {
			final MapBookmarks mapBookmarks = mapSelection.getMap().getExtension(MapBookmarks.class);
			final NodeModel previouslySelectedNode = mapBookmarks.getSelectedNodeForRoot(node);

			if (mapSelection.getSelectionRoot() != node) {
				mapViewManager.setViewRoot(node);
				nodeToSelect = previouslySelectedNode;
			}
			else
				nodeToSelect = node;
		}
		else
			nodeToSelect = node;
		if(openAsRoot || ! NodeVisibility.isHidden(nodeToSelect)){
			if(mapSelection.getSelectionRoot() != nodeToSelect
					&& ! nodeToSelect.isDescendantOf(mapSelection.getSelectionRoot())) {
				mapViewManager.setViewRoot(node.getMap().getRootNode());
			}
			final Filter filter = mapSelection.getFilter();
			if(! nodeToSelect.isVisible(filter)) {
				FilterController.getController(controller).applyNoFiltering(node.getMap());
			}
			controller.getModeController().getMapController().displayNode(nodeToSelect);
			if(nodeToSelect.isRoot()){
				mapSelection.selectRoot();
			}
			else {
				mapSelection.selectAsTheOnlyOneSelected(nodeToSelect);
				mapSelection.scrollNodeTreeToVisible(nodeToSelect, false);
			}
		}
	}

	public void openAsNewView() {
		final Controller controller = Controller.getCurrentController();
		final IMapViewManager mapViewManager = controller.getMapViewManager();
		mapViewManager.newMapView(node.getMap(), controller.getModeController());
		SwingUtilities.invokeLater(() -> open(true));
	}
}

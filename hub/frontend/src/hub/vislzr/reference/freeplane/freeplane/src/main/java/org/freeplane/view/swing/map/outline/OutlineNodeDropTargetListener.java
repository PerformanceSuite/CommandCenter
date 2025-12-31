package org.freeplane.view.swing.map.outline;

import java.awt.Component;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.dnd.DnDConstants;
import java.awt.dnd.DropTargetAdapter;
import java.awt.dnd.DropTargetDragEvent;
import java.awt.dnd.DropTargetDropEvent;
import java.awt.dnd.DropTargetEvent;
import java.io.IOException;

import org.freeplane.features.map.NodeModel;
import org.freeplane.features.map.NodeModel.Side;
import org.freeplane.features.map.mindmapmode.InsertionRelation;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.mode.ModeController;
import org.freeplane.view.swing.ui.NodeDropUtils;

class OutlineNodeDropTargetListener extends DropTargetAdapter {

	@Override
	public void dragEnter(DropTargetDragEvent dropTargetDragEvent) {
		dragOver(dropTargetDragEvent);
	}

	@Override
	public void dragOver(DropTargetDragEvent dropTargetDragEvent) {
		NodeButton nodeButton = resolveTargetButton(dropTargetDragEvent.getDropTargetContext().getComponent());
		if (nodeButton == null) {
			dropTargetDragEvent.rejectDrag();
			return;
		}

		handleDragOver(dropTargetDragEvent, nodeButton);
	}

	@Override
	public void dragExit(DropTargetEvent dropTargetEvent) {
		NodeButton nodeButton = resolveTargetButton(dropTargetEvent.getDropTargetContext().getComponent());
		if (nodeButton != null) {
			nodeButton.clearDropFeedback();
		}
	}

	@Override
	public void drop(DropTargetDropEvent dropTargetDropEvent) {
		NodeButton nodeButton = resolveTargetButton(dropTargetDropEvent.getDropTargetContext().getComponent());
		if (nodeButton == null) {
			dropTargetDropEvent.rejectDrop();
			return;
		}

		performDrop(dropTargetDropEvent, nodeButton);
	}

	private void handleDragOver(DropTargetDragEvent dropTargetDragEvent, NodeButton nodeButton) {
		NodeModel nodeModel = nodeButton.getNodeModel();
		if (nodeModel == null || !NodeDropUtils.isDragAcceptable(dropTargetDragEvent, nodeModel, NodeDropUtils.AcceptedContent.ANY)) {
			dropTargetDragEvent.rejectDrag();
			nodeButton.clearDropFeedback();
			return;
		}

		int dropAction = NodeDropUtils.getDropAction(dropTargetDragEvent.getTransferable(), dropTargetDragEvent.getDropAction());
		dropTargetDragEvent.acceptDrag(dropAction);
		nodeButton.showDropFeedback();
	}

	private void performDrop(DropTargetDropEvent dropTargetDropEvent, NodeButton nodeButton) {
		NodeModel nodeModel = nodeButton.getNodeModel();
		if (nodeModel == null) {
			dropTargetDropEvent.rejectDrop();
			return;
		}

		int dropAction = NodeDropUtils.getDropAction(dropTargetDropEvent);
		if (!NodeDropUtils.isDropAcceptable(dropTargetDropEvent, nodeModel, dropAction, NodeDropUtils.AcceptedContent.ANY)) {
			dropTargetDropEvent.rejectDrop();
			nodeButton.clearDropFeedback();
			return;
		}

		Transferable transferable = dropTargetDropEvent.getTransferable();
		try {
			dropTargetDropEvent.acceptDrop(dropAction);
			if (dropAction == DnDConstants.ACTION_LINK) {
				Controller controller = Controller.getCurrentController();
				ModeController modeController = controller.getModeController();
				NodeDropUtils.handleLinkAction(transferable, nodeModel, controller, modeController);
			} else {
				NodeDropUtils.handleMoveOrCopyAction(transferable, nodeModel, dropAction, dropTargetDropEvent.isLocalTransfer(), InsertionRelation.AS_CHILD, Side.DEFAULT);
			}
			dropTargetDropEvent.dropComplete(true);
		} catch (UnsupportedFlavorException | IOException exception) {
			dropTargetDropEvent.dropComplete(false);
		} finally {
			nodeButton.clearDropFeedback();
		}
	}

	private NodeButton resolveTargetButton(Component component) {
		if (component instanceof NodeButton) {
			return (NodeButton) component;
		}
		return null;
	}
}

package org.freeplane.view.swing.map.outline;

import java.awt.Cursor;
import java.awt.dnd.DnDConstants;
import java.awt.dnd.DragGestureEvent;
import java.awt.dnd.DragGestureListener;
import java.awt.dnd.DragSource;
import java.awt.event.InputEvent;
import java.awt.datatransfer.Transferable;
import java.util.Collections;

import org.freeplane.features.map.NodeModel;
import org.freeplane.features.map.clipboard.MapClipboardController;
import org.freeplane.features.map.clipboard.MapClipboardController.CopiedNodeSet;
import org.freeplane.features.map.clipboard.MindMapNodesSelection;

class OutlineNodeDragGestureListener implements DragGestureListener {

	private final NodeButton nodeButton;

	OutlineNodeDragGestureListener(NodeButton nodeButton) {
		this.nodeButton = nodeButton;
	}

	@Override
	public void dragGestureRecognized(DragGestureEvent dragGestureEvent) {
		NodeModel nodeModel = nodeButton.getNodeModel();
		if (nodeModel == null) {
			return;
		}

		DragAction dragAction = determineDragAction(dragGestureEvent);
		Transferable transferable = MapClipboardController.getController().copy(
			Collections.singletonList(nodeModel),
			CopiedNodeSet.ALL_NODES,
			CopiedNodeSet.ALL_NODES);

		if (transferable instanceof MindMapNodesSelection) {
			MindMapNodesSelection nodeSelection = (MindMapNodesSelection) transferable;
			nodeSelection.setDropAction(dragAction.actionType);
			nodeSelection.setNodeObjects(Collections.singletonList(nodeModel), false);
		}

		dragGestureEvent.startDrag(dragAction.cursor, transferable);
	}

	private DragAction determineDragAction(DragGestureEvent dragGestureEvent) {
		int dragActionType = dragGestureEvent.getDragAction();
		Cursor cursor = getCursor(dragActionType);
		int modifiers = dragGestureEvent.getTriggerEvent().getModifiersEx();
		if ((modifiers & InputEvent.BUTTON2_DOWN_MASK) != 0) {
			dragActionType = DnDConstants.ACTION_COPY;
			cursor = DragSource.DefaultCopyDrop;
		}
		else if ((modifiers & InputEvent.BUTTON3_DOWN_MASK) != 0) {
			dragActionType = DnDConstants.ACTION_LINK;
			cursor = DragSource.DefaultLinkDrop;
		}
		return new DragAction(cursor, dragActionType);
	}

	private Cursor getCursor(int dragActionType) {
		switch (dragActionType) {
			case DnDConstants.ACTION_COPY:
				return DragSource.DefaultCopyDrop;
			case DnDConstants.ACTION_LINK:
				return DragSource.DefaultLinkDrop;
			default:
				return DragSource.DefaultMoveDrop;
		}
	}

	private static class DragAction {
		private final Cursor cursor;
		private final int actionType;

		private DragAction(Cursor cursor, int actionType) {
			this.cursor = cursor;
			this.actionType = actionType;
		}
	}
}

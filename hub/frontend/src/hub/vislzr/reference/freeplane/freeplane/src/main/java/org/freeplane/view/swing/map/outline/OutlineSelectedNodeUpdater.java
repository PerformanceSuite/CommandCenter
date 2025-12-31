package org.freeplane.view.swing.map.outline;

import java.lang.ref.WeakReference;

import org.freeplane.features.map.INodeSelectionListener;
import org.freeplane.features.map.NodeModel;

class OutlineSelectedNodeUpdater implements INodeSelectionListener {
    private final WeakReference<MapAwareOutlinePane> paneRef;

    OutlineSelectedNodeUpdater(MapAwareOutlinePane pane) {
        this.paneRef = new WeakReference<>(pane);
    }

    @Override
    public void onSelect(NodeModel node) {
        MapAwareOutlinePane pane = paneRef.get();
        if (pane == null) return;
        pane.handleMapSelectionChanged(node);
    }
}

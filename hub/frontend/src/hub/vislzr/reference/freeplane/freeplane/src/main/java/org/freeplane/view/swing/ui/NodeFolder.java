/*
 *  Freeplane - mind map editor
 *  Copyright (C) 2025 Dimitry
 *
 *  This file author is Dimitry
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General License for more details.
 *
 *  You should have received a copy of the GNU General License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.freeplane.view.swing.ui;

import java.awt.Component;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;

import javax.swing.SwingUtilities;

import org.freeplane.core.resources.ResourceController;
import org.freeplane.features.map.MapController;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.mode.ModeController;
import org.freeplane.view.swing.map.MapView;
import org.freeplane.view.swing.map.NodeView;

/**
 * @author Dimitry Polivaev
 * 19.06.2013
 */
class NodeFolder implements MouseTimerDelegate.ActionProvider {
    private static final String MOUSE_OVER_FOLDING = "mouse_over_folding";
    private static final String MOUSE_OVER_FOLDING_ACTION = "mouse_over_folding_action";
    private static final String FOLDING_DISABLED = "disabled";
    private static final String FOLDING_IMMEDIATE = "immediate";
    private static final String FOLDING_TOGGLE = "toggle";
    private static final String FOLDING_UNFOLD_ONLY = "unfold_only";
    private static final String FOLDING_PREVIEW = "preview";

    class TimeDelayedFolding implements ActionListener {
        private final MouseEvent mouseEvent;
        private final String foldingBehavior;
        private boolean wasFired;

        TimeDelayedFolding(final MouseEvent e, String foldingBehavior) {
            this.mouseEvent = e;
            this.foldingBehavior = foldingBehavior;
            this.wasFired = false;
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
                        MouseEventActor.INSTANCE.withMouseEvent(() -> {
                            MapController mapController = modeController.getMapController();
                            performFoldingAction(mapController, node, map, foldingBehavior);
                        });
                        this.wasFired = true;
                    }
                }
            }
            catch (NullPointerException e) {
            }
        }

        private void performFoldingAction(MapController mapController, NodeModel node, MapView map, String behavior) {
            switch (behavior) {
                case FOLDING_TOGGLE:
                    mapController.toggleFoldedAndScroll(node);
                    break;
                case FOLDING_UNFOLD_ONLY:
                    unfoldIfFolded(mapController, node, map);
                    break;
                case FOLDING_PREVIEW:
                    unfoldForPreview(mapController, node, map);
                    break;
                default:
                    break;
            }
        }

        private void unfoldIfFolded(MapController mapController, NodeModel node, MapView map) {
            if (node.isFolded()) {
                mapController.unfoldAndScroll(node, map.getFilter());
            }
        }

        private void unfoldForPreview(MapController mapController, NodeModel node, MapView map) {
            if (node.isFolded()) {
                mapController.unfoldAndScroll(node, map.getFilter());
                previewUnfoldedNode = node;
            }
        }
    }

    private final MouseTimerDelegate timerDelegate = new MouseTimerDelegate();
    private NodeModel previewUnfoldedNode = null;
    private TimeDelayedFolding delayedFolding;

    void handleMouseEvent(final MouseEvent e) {
        if(delayedFolding != null && delayedFolding.wasFired) {
            return;
        }

        final String folding = ResourceController.getResourceController().getProperty(MOUSE_OVER_FOLDING);
        if (folding.equals(FOLDING_DISABLED)) {
            return;
        }
        if (folding.equals(FOLDING_IMMEDIATE)) {
            ActionListener action = createDelayedAction(e);
            action.actionPerformed(new ActionEvent(this, 0, ""));
            // Mark as fired to prevent timer from triggering again
            if (delayedFolding != null) {
                delayedFolding.wasFired = true;
            }
            return;
        }
        // FOLDING_DELAYED case
        timerDelegate.createTimer(e, this);
    }

    void stopTimerForDelayedFolding() {
        timerDelegate.stopTimer();
        delayedFolding = null;
        previewUnfoldedNode = null;
    }

    void onMouseExited() {
        restorePreviewUnfoldedNode();
    }

    void makePreviewUnfoldingPermanent() {
        previewUnfoldedNode = null;
    }

    boolean isPreviewUnfolded(NodeModel node) {
        return previewUnfoldedNode == node;
    }

    private void restorePreviewUnfoldedNode() {
        if (previewUnfoldedNode != null && !previewUnfoldedNode.isFolded()) {
            Controller controller = Controller.getCurrentController();
            ModeController modeController = controller.getModeController();
            MapController mapController = modeController.getMapController();
            mapController.setFolded(previewUnfoldedNode, true, controller.getSelection().getFilter());
            previewUnfoldedNode = null;
        }
        stopTimerForDelayedFolding();
    }

    @Override
    public ActionListener createDelayedAction(MouseEvent e) {
        final String foldingAction = ResourceController.getResourceController().getProperty(MOUSE_OVER_FOLDING_ACTION);
        delayedFolding = new TimeDelayedFolding(e, foldingAction);
        return delayedFolding;
    }

    @Override
    public boolean isActionEnabled(MouseEvent e) {
        final String folding = ResourceController.getResourceController().getProperty(MOUSE_OVER_FOLDING);
        return !folding.equals(FOLDING_DISABLED);
    }

    NodeView getRelatedNodeView(MouseEvent e) {
        return timerDelegate.getRelatedNodeView(e);
    }

    private static boolean shouldMigrateFoldingMethodFromSelectionMethod(ResourceController rc) {
        return userHasCustomizedSelectionMethod(rc) && userHasNotCustomizedFoldingMethod(rc);
    }

    private static boolean userHasCustomizedSelectionMethod(ResourceController rc) {
        return rc.isPropertySetByUser("selection_method");
    }

    private static boolean userHasNotCustomizedFoldingMethod(ResourceController rc) {
        return !rc.isPropertySetByUser(MOUSE_OVER_FOLDING) && !rc.isPropertySetByUser(MOUSE_OVER_FOLDING_ACTION);
    }

    void trackWindowForComponent(Component c) {
        timerDelegate.trackWindowForComponent(c);
    }
}

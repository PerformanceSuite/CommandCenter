/*
 *  Freeplane - mind map editor
 *  Copyright (C) 2025 Dimitry
 *
 *  This file author is Dimitry
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.freeplane.view.swing.ui;

import java.awt.Component;
import java.awt.KeyboardFocusManager;
import java.awt.Rectangle;
import java.awt.Window;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.awt.geom.Point2D;

import javax.swing.FocusManager;
import javax.swing.SwingUtilities;
import javax.swing.Timer;
import javax.swing.text.JTextComponent;

import org.freeplane.core.resources.ResourceController;
import org.freeplane.view.swing.map.NodeView;

/**
 * Delegate for mouse event handlers that need timing behavior
 * @author Dimitry Polivaev
 */
public class MouseTimerDelegate {
    protected static final String MOUSE_OVER_DELAY = "mouse_over_delay";

    private Rectangle controlRegionForDelayedAction;
    private Timer timerForDelayedAction;
    private ActionListener delayedAction;

    public interface ActionProvider {
        ActionListener createDelayedAction(MouseEvent e);
        boolean isActionEnabled(MouseEvent e);
    }

    public void createTimer(final MouseEvent e, ActionProvider actionProvider) {
        if (controlRegionForDelayedAction != null && controlRegionForDelayedAction.contains(e.getPoint())) {
            return;
        }

        stopTimer();

        Window focusedWindow = FocusManager.getCurrentManager().getFocusedWindow();
        if (focusedWindow == null) {
            return;
        }
        if (KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner() instanceof JTextComponent) {
            return;
        }

        controlRegionForDelayedAction = getControlRegion(e.getPoint());

        if (!actionProvider.isActionEnabled(e)) {
            return;
        }

        delayedAction = actionProvider.createDelayedAction(e);

        final int mouseOverDelay = getMouseOverDelay();
        timerForDelayedAction = new Timer(mouseOverDelay, delayedAction);
        timerForDelayedAction.setRepeats(false);
        timerForDelayedAction.start();
    }

    public void stopTimer() {
        if (timerForDelayedAction != null) {
            timerForDelayedAction.stop();
        }
        timerForDelayedAction = null;
        controlRegionForDelayedAction = null;
        delayedAction = null;
    }

    protected Rectangle getControlRegion(final Point2D p) {
        final int side = 8;
        return new Rectangle((int) (p.getX() - side / 2), (int) (p.getY() - side / 2), side, side);
    }

    public NodeView getRelatedNodeView(MouseEvent e) {
        return (NodeView) SwingUtilities.getAncestorOfClass(NodeView.class, e.getComponent());
    }


    private int getMouseOverDelay() {
        ResourceController rc = ResourceController.getResourceController();
        return rc.getIntProperty(MOUSE_OVER_DELAY, 100);
    }

    public void trackWindowForComponent(Component c) {
        // Default implementation - can be overridden by subclasses
    }
}

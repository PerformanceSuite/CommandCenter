/*
 * Created on 26 Oct 2025
 *
 * author dimitry
 */
package org.freeplane.view.swing.map.outline;

import java.awt.AWTEvent;
import java.awt.Point;
import java.awt.Toolkit;
import java.awt.event.AWTEventListener;
import java.awt.event.MouseEvent;

import javax.swing.JComponent;
import javax.swing.SwingUtilities;

class NavigationButtonHider {
	static NavigationButtonHider INSTANCE = new NavigationButtonHider();
	private AWTEventListener mouseMovementDetector;
	private OutlineController outlineController;
	private NavigationButtons navigationButtons;
	void enable(JComponent buttonParent, NavigationButtons attachedNavigationButtons) {
		if(navigationButtons == attachedNavigationButtons)
			return;
		if(navigationButtons != null) {
			navigationButtons.hideNavigationButtons();
			outlineController.resetHoveredNode();
		}
		disable();
		this.navigationButtons = attachedNavigationButtons;
		OutlinePane outlinePane = (OutlinePane) SwingUtilities.getAncestorOfClass(OutlinePane.class, buttonParent);
		outlineController = outlinePane.getController();
        mouseMovementDetector = new AWTEventListener() {
		    @Override
		    public void eventDispatched(AWTEvent event) {
		        if (event instanceof MouseEvent) {
		            MouseEvent mouseEvent = (MouseEvent) event;
		            Point eventPoint = new Point (mouseEvent.getXOnScreen(),mouseEvent.getYOnScreen());
		            SwingUtilities.convertPointFromScreen(eventPoint, outlinePane);
		            if(eventPoint.x < 0 || eventPoint.y < 0 || eventPoint.x >= outlinePane.getWidth() || eventPoint.y >= outlinePane.getHeight()) {
						attachedNavigationButtons.hideNavigationButtons();
						outlineController.resetHoveredNode();
						disable();
					}
		        }
		    }
		};
		Toolkit.getDefaultToolkit().addAWTEventListener(
            mouseMovementDetector, AWTEvent.MOUSE_EVENT_MASK | AWTEvent.MOUSE_MOTION_EVENT_MASK | AWTEvent.MOUSE_WHEEL_EVENT_MASK
        );

	}

	void disable() {
		if(mouseMovementDetector != null) {
			Toolkit.getDefaultToolkit().removeAWTEventListener(mouseMovementDetector);
			outlineController = null;
			navigationButtons = null;
			mouseMovementDetector = null;
		}
	}
}

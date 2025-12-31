/*
 *  Freeplane - mind map editor
 *  Copyright (C) 2025 Dimitry Polivaev
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
package org.freeplane.main.application;

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Container;
import java.awt.EventQueue;
import java.awt.KeyboardFocusManager;
import java.awt.Window;
import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeListener;

import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JMenuBar;
import javax.swing.SwingUtilities;

import org.freeplane.core.resources.IFreeplanePropertyListener;
import org.freeplane.core.resources.ResourceController;
import org.freeplane.core.ui.components.UITools;
import org.freeplane.core.util.Compat;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.ui.IMapViewChangeListener;
import org.freeplane.features.ui.IMapViewManager;

class FrameComponentMover implements IMapViewChangeListener, PropertyChangeListener, IFreeplanePropertyListener {
	private static final String SELECTED_MAP_FOLLOWS_ACTIVE_WINDOW = "selected_map_follows_active_window";
	private static final String UI_ELEMENTS_FOLLOW_SELECTED_MAP_PROPERTY = "ui_elements_follow_selected_map";
	private JFrame lastUIFrame = null;
	private boolean uiElementsFollowSelectedMap;

	public FrameComponentMover(JFrame frame) {
		lastUIFrame = frame;
		uiElementsFollowSelectedMap = uiElementsFollowSelectedMap();
	}

	public void installFocusListener() {
		KeyboardFocusManager.getCurrentKeyboardFocusManager()
			.addPropertyChangeListener("focusedWindow", this);
		ResourceController.getResourceController().addPropertyChangeListener(this);
	}

	public void uninstall() {
		KeyboardFocusManager.getCurrentKeyboardFocusManager()
			.removePropertyChangeListener("focusedWindow", this);
	}

	void moveUIElements() {
		 final Window uiFrame = findUIFrame();
		 afterUIWindowChange(uiFrame);
	}


	@Override
	public void propertyChange(PropertyChangeEvent evt) {
		Window newFocusedWindow = (Window) evt.getNewValue();
		final IMapViewManager mapViewManager = Controller.getCurrentController().getMapViewManager();
		final JComponent selectedComponent = mapViewManager.getMapViewComponent();
        final JComponent containedMapView = mapViewManager.getLastSelectedMapViewContainedIn(newFocusedWindow);
		if(selectedComponent == containedMapView) {
			if(uiElementsFollowSelectedMap)
				afterUIWindowChange(newFocusedWindow);
		} else if(containedMapView != null && selectedMapFollowsActiveWindow())
			mapViewManager.changeToMapView(containedMapView);
	}

	static boolean selectedMapFollowsActiveWindow() {
		return ResourceController.getResourceController().getBooleanProperty(SELECTED_MAP_FOLLOWS_ACTIVE_WINDOW);
	}

	@Override
	public void propertyChanged(String propertyName, String newValue, String oldValue) {
		if(propertyName.equals(UI_ELEMENTS_FOLLOW_SELECTED_MAP_PROPERTY)) {
			uiElementsFollowSelectedMap = Boolean.parseBoolean(newValue);
			Window menuWindow = findUIFrame();
			afterUIWindowChange(menuWindow);
		}
	}

	private Window findUIFrame() {
		return uiElementsFollowSelectedMap ? UITools.getCurrentFrame() : UITools.getFrame();
	}

	@Override
	public void afterViewChange(Component oldView, Component newView) {
		if(newView != null && uiElementsFollowSelectedMap) {
			Window newFocusedWindow = SwingUtilities.getWindowAncestor(newView);
			afterUIWindowChange(newFocusedWindow);
		}
	}

	private boolean uiElementsFollowSelectedMap() {
		return ResourceController.getResourceController().getBooleanProperty(UI_ELEMENTS_FOLLOW_SELECTED_MAP_PROPERTY);
	}

	private void afterUIWindowChange(Window newFocusedWindow) {
		if (newFocusedWindow instanceof JFrame) {
			JFrame currentFrame = (JFrame) newFocusedWindow;

			if (lastUIFrame != null && lastUIFrame != currentFrame) {
				EventQueue.invokeLater(() ->
					moveNonCenterComponents(lastUIFrame, currentFrame));
			}
			else
				lastUIFrame = currentFrame;
		}
	}

	private void moveNonCenterComponents(JFrame fromFrame, JFrame toFrame) {
		if(toFrame != KeyboardFocusManager.getCurrentKeyboardFocusManager().getActiveWindow())
			return;
		moveMenuBar(fromFrame, toFrame);

		Container fromContentPane = fromFrame.getContentPane();
		Container toContentPane = toFrame.getContentPane();

		if (!(fromContentPane.getLayout() instanceof BorderLayout) ||
			!(toContentPane.getLayout() instanceof BorderLayout)) {
			return;
		}

		moveComponentIfExists(fromContentPane, toContentPane, BorderLayout.NORTH);
		moveComponentIfExists(fromContentPane, toContentPane, BorderLayout.SOUTH);
		moveComponentIfExists(fromContentPane, toContentPane, BorderLayout.EAST);
		moveComponentIfExists(fromContentPane, toContentPane, BorderLayout.WEST);

		moveAuxiliaryComponents(fromFrame, toFrame);

		fromContentPane.revalidate();
		fromContentPane.repaint();
		toContentPane.revalidate();
		toContentPane.repaint();
		lastUIFrame = toFrame;
	}

	private void moveMenuBar(JFrame fromFrame, JFrame toFrame) {
		JMenuBar menuBar = fromFrame.getJMenuBar();
		if (menuBar != null) {
			if(Compat.isMacOsX()) {
		        System.setProperty("apple.laf.useScreenMenuBar", "true");
		        toFrame.setJMenuBar(menuBar);
	            System.setProperty("apple.laf.useScreenMenuBar", "false");
	        }
		    else
		    	toFrame.setJMenuBar(menuBar);
		}
	}

	private void moveComponentIfExists(Container fromPane, Container toPane, String position) {
		BorderLayout fromLayout = (BorderLayout) fromPane.getLayout();
		Component component = fromLayout.getLayoutComponent(fromPane, position);
		if (component != null) {
			fromPane.remove(component);
			toPane.add(component, position);
		}
	}

	private void moveAuxiliaryComponents(JFrame fromFrame, JFrame toFrame) {
		AuxiliarySplitPanes fromSplitPanes = findAuxiliarySplitPanes(fromFrame);
		AuxiliarySplitPanes toSplitPanes = findAuxiliarySplitPanes(toFrame);

		if (fromSplitPanes != null && toSplitPanes != null) {
			EventQueue.invokeLater(() ->
				moveAuxiliaryComponentBetweenManagers(fromSplitPanes, toSplitPanes));
		}
	}

	private AuxiliarySplitPanes findAuxiliarySplitPanes(JFrame frame) {
		Container contentPane = frame.getContentPane();
		if (contentPane.getLayout() instanceof BorderLayout) {
			Component centerComponent = ((BorderLayout) contentPane.getLayout())
				.getLayoutComponent(contentPane, BorderLayout.CENTER);
			if (centerComponent instanceof AuxillaryEditorSplitPane) {
				AuxillaryEditorSplitPane rootPane = (AuxillaryEditorSplitPane) centerComponent;
				return rootPane.getManager();
			}
		}
		return null;
	}

    private void moveAuxiliaryComponentBetweenManagers(AuxiliarySplitPanes fromManager, AuxiliarySplitPanes toManager) {
        String modeName = Controller.getCurrentModeController().getModeName();
        // Only move the level-0 auxiliary (note pane). Outline and other levels remain per-frame.
        fromManager.moveAuxiliaryNoteTo(toManager, modeName);
    }

	public JFrame getUIFrame() {
		return lastUIFrame;
	}
}

/*
 *  Freeplane - mind map editor
 *  Copyright (C) 2013 Dimitry
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

import java.awt.AWTEvent;
import java.awt.Component;
import java.awt.Rectangle;
import java.awt.Toolkit;
import java.awt.Window;
import java.awt.event.AWTEventListener;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.util.function.Function;

import javax.swing.FocusManager;
import javax.swing.SwingUtilities;
import javax.swing.text.JTextComponent;

import org.freeplane.core.resources.ResourceController;
import org.freeplane.core.util.Compat;
import org.freeplane.features.map.IMapSelection;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.mode.Controller;
import org.freeplane.view.swing.map.MainView;
import org.freeplane.view.swing.map.MapView;
import org.freeplane.view.swing.map.NodeView;

/**
 * @author Dimitry Polivaev
 * 19.06.2013
 */
public class NodeSelector implements MouseTimerDelegate.ActionProvider {
	public static final NodeSelector mapNodeSelector = new NodeSelector();
	public static final NodeSelector mapViewSelector = new NodeSelector(
			mev -> (aev -> ((MapView)mev.getComponent()).getSelected().getMainView().requestFocusInWindow()),
			mev -> ((MapView)mev.getComponent())
			);

	private static final String SELECTION_INSIDE_SAME_MAP = "selection_inside.same_map";
	private static final String SELECTION_INSIDE_SELECTED_WINDOW = "selection_inside.selected_window";
	private static final String SELECTION_INSIDE_ANY_MAP = "selection_inside.any_map";
	private static final String SELECTION_INSIDE_SELECTED_MAP_VIEW = "selection_inside.selected_map_view";
	private static final String MOUSE_OVER_SELECTION_INSIDE = "mouse_over_selection_inside";

	static {
        migrateSelectionPropertiesFromLegacyMethod();
    }
	private static void migrateSelectionPropertiesFromLegacyMethod() {
		ResourceController rc = ResourceController.getResourceController();

		final boolean shouldMigrateSelectionMethod = rc.isPropertySetByUser("selection_method") &&
		   !rc.isPropertySetByUser(MOUSE_OVER_SELECTION);
		if (shouldMigrateSelectionMethod) {
			String selectionMethod = rc.getProperty("selection_method");
			migrateSelectionSettingsFromSelectionMethod(rc, selectionMethod);
		}
	}

	private static void migrateSelectionSettingsFromSelectionMethod(ResourceController rc, String selectionMethod) {
		switch (selectionMethod) {
			case "selection_method_direct":
				rc.setProperty(MOUSE_OVER_SELECTION, SELECTION_IMMEDIATE);
				break;
			case "selection_method_delayed":
				rc.setProperty(MOUSE_OVER_SELECTION, SELECTION_DELAYED);
				break;
			case "selection_method_by_click":
				rc.setProperty(MOUSE_OVER_SELECTION, SELECTION_DISABLED);
				break;
		}
	}

	private static final AWTEventListener mouseMovementDetector;
    static {
        mouseMovementDetector = new AWTEventListener() {
		    int lastX = -1;
		    int lastY = -1;
		    @Override
		    public void eventDispatched(AWTEvent event) {
		        if (event instanceof MouseEvent &&
		        		(event.getID() != MouseEvent.MOUSE_EXITED)) {
		            MouseEvent mouseEvent = (MouseEvent) event;
		            int x = mouseEvent.getXOnScreen();
		            int y = mouseEvent.getYOnScreen();
		            mouseWasMoved = lastX != x || lastY != y;
		            lastX = x;
		            lastY = y;
		        }
		    }
		};
		Toolkit.getDefaultToolkit().addAWTEventListener(
            mouseMovementDetector, AWTEvent.MOUSE_EVENT_MASK | AWTEvent.MOUSE_MOTION_EVENT_MASK | AWTEvent.MOUSE_WHEEL_EVENT_MASK
        );
    }

	private static final String MOUSE_OVER_SELECTION = "mouse_over_selection";
	private static final String SELECTION_DISABLED = "disabled";
	private static final String SELECTION_DELAYED = "delayed";
	private static final String SELECTION_IMMEDIATE = "immediate";
	private static boolean mouseWasMoved = false;
	private final MovedMouseEventFilter windowMouseTracker = new MovedMouseEventFilter();
	private final MouseTimerDelegate timerDelegate = new MouseTimerDelegate();
	private final Function<MouseEvent, ActionListener> actionFactory;
	private final Function<MouseEvent, MapView> mapViewProvider;

	private NodeSelector() {
		this(NodeSelector::createNodeSelectorAction, NodeSelector::provideMapView);
	}



	public NodeSelector(Function<MouseEvent, ActionListener> actionFactory,
	        Function<MouseEvent, MapView> mapViewProvider) {
		super();
		this.actionFactory = actionFactory;
		this.mapViewProvider = mapViewProvider;
	}

	public void handleMouseEvent(final MouseEvent e) {
		if(! mouseWasMoved) {
			return;
		}
		final Component focusOwner = FocusManager.getCurrentManager().getFocusOwner();
		final Component eventSource = e.getComponent();
		if(focusOwner instanceof JTextComponent || focusOwner != null && SwingUtilities.isDescendingFrom(focusOwner, eventSource))
			return;

		Window w =  SwingUtilities.windowForComponent(eventSource);
		final Component windowFocusOwner = w.getFocusOwner();
		if(windowFocusOwner instanceof JTextComponent)
			return;

		if (!isInside(e)) {
			return;
		}

		final String selectionTiming = getSelectionBehavior(e);
		if (selectionTiming.equals(SELECTION_DISABLED)) {
			return;
		}
		if (selectionTiming.equals(SELECTION_IMMEDIATE)) {
			ActionListener action = createDelayedAction(e);
			action.actionPerformed(new ActionEvent(this, 0, ""));
			return;
		}
		// SELECTION_DELAYED case
		timerDelegate.createTimer(e, this);
	}

	protected boolean isInside(final MouseEvent e) {
		return new Rectangle(0, 0, e.getComponent().getWidth(), e.getComponent().getHeight())
		    .contains(e.getPoint());
	}

	public void stopTimerForDelayedSelection() {
		timerDelegate.stopTimer();
	}

	@Override
	public ActionListener createDelayedAction(MouseEvent e) {
		return actionFactory.apply(e);
	}

	static private ActionListener createNodeSelectorAction(MouseEvent e) {
		return new TimeDelayedNodeSelection(e);
	}
	private static MapView provideMapView(MouseEvent event) {
		return (MapView) SwingUtilities.getAncestorOfClass(MapView.class, event.getComponent());
	}

	@Override
	public boolean isActionEnabled(MouseEvent e) {
		final String selectionBehavior = getSelectionBehavior(e);
		return !selectionBehavior.equals(SELECTION_DISABLED);
	}

	boolean shouldSelectOnClick(MouseEvent e) {
		if (isInside(e)) {
			final NodeView nodeView = getRelatedNodeView(e);
			return !nodeView.isSelected() || Controller.getCurrentController().getSelection().size() != 1;
		}
		return false;
	}

	void extendSelection(final MouseEvent e, boolean scrollNodeTree) {
		final Controller controller = Controller.getCurrentController();
		final NodeView nodeView = getRelatedNodeView(e);
		final NodeModel newlySelectedNode = nodeView.getNode();
		final boolean extend = Compat.isMacOsX() ? e.isMetaDown() : e.isControlDown();
		final boolean range = e.isShiftDown();
		final IMapSelection selection = controller.getSelection();
		if (range && !extend) {
			selection.selectContinuous(newlySelectedNode);
		}
		else if (extend && !range) {
			selection.toggleSelected(newlySelectedNode);
		}
		if (extend == range) {
			if (!selection.isSelected(newlySelectedNode)
			        || selection.size() != 1
			        || !(FocusManager.getCurrentManager().getFocusOwner() instanceof MainView)) {
				MouseEventActor.INSTANCE.withMouseEvent( () ->
					selection.selectAsTheOnlyOneSelected(newlySelectedNode));
				e.consume();
			}
			if(! extend && scrollNodeTree && ! newlySelectedNode.isFolded()) {
				MouseEventActor.INSTANCE.withMouseEvent( () ->
					controller.getModeController().getMapController().scrollNodeTreeAfterSelect(newlySelectedNode));
                e.consume();
            }
		}
	}

	void selectSingleNode(MouseEvent e) {
		final NodeView nodeV = getRelatedNodeView(e);
		final Controller controller = Controller.getCurrentController();
		if (!((MapView) controller.getMapViewManager().getMapViewComponent()).isSelected(nodeV)) {
			MouseEventActor.INSTANCE.withMouseEvent( () ->
				controller.getSelection().selectAsTheOnlyOneSelected(nodeV.getNode()));
		}
	}

	public NodeView getRelatedNodeView(MouseEvent e) {
		return timerDelegate.getRelatedNodeView(e);
	}

	boolean isRelevant(MouseEvent e) {
		return windowMouseTracker.isRelevant(e);
	}

	void trackWindowForComponent(Component c) {
		windowMouseTracker.trackWindowForComponent(c);
		timerDelegate.trackWindowForComponent(c);
	}

	private String getSelectionBehavior(MouseEvent e) {
		ResourceController rc = ResourceController.getResourceController();
		String behavior = rc.getProperty(MOUSE_OVER_SELECTION, SELECTION_IMMEDIATE);
		if (SELECTION_DISABLED.equals(behavior)) {
			return SELECTION_DISABLED;
		} else if ("enabled".equals(behavior)) {
			behavior = SELECTION_IMMEDIATE;
			rc.setProperty(MOUSE_OVER_SELECTION, SELECTION_IMMEDIATE);
		}
		String selectionInside = rc.getProperty(MOUSE_OVER_SELECTION_INSIDE, SELECTION_INSIDE_SELECTED_MAP_VIEW);
		switch (selectionInside) {
		case SELECTION_INSIDE_ANY_MAP:
			return behavior;
		case SELECTION_INSIDE_SELECTED_MAP_VIEW: {
			final MapView map = mapViewProvider.apply(e);
			return map != null && map.isSelected() ? behavior : SELECTION_DISABLED;
		}
		case SELECTION_INSIDE_SAME_MAP: {
			final MapView map = mapViewProvider.apply(e);
			if( map == null)
				return SELECTION_DISABLED;
			final IMapSelection selection = map.getModeController().getController().getSelection();
			return selection != null  && map.getMap() == selection.getMap() ? behavior : SELECTION_DISABLED;
		}
		case SELECTION_INSIDE_SELECTED_WINDOW: {
			final Window windowAncestor = SwingUtilities.getWindowAncestor(mapViewProvider.apply(e));
			return  windowAncestor != null && windowAncestor.isFocused() ? behavior : SELECTION_DISABLED;
		}
		default:
			return SELECTION_DISABLED;
		}
	}

}

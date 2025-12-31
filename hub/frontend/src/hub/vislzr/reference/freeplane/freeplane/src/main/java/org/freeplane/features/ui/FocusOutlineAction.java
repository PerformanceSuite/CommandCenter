package org.freeplane.features.ui;

import java.awt.Component;
import java.awt.KeyboardFocusManager;
import java.awt.event.ActionEvent;
import java.awt.Window;

import javax.swing.JComponent;
import javax.swing.SwingUtilities;

import org.freeplane.core.ui.AFreeplaneAction;
import org.freeplane.features.mode.Controller;
import org.freeplane.view.swing.map.outline.MapAwareOutlinePane;

public class FocusOutlineAction extends AFreeplaneAction {
    private static final long serialVersionUID = 1L;
    public static final String OUTLINE_FOCUS_PROPERTY = "outlineFocus";

    public FocusOutlineAction() {
        super("FocusOutlineAction");
    }

    @Override
    public void actionPerformed(ActionEvent e) {
        final KeyboardFocusManager kfm = KeyboardFocusManager.getCurrentKeyboardFocusManager();
        final Component focusOwner = kfm != null ? kfm.getFocusOwner() : null;
        final boolean inOutline =
                (focusOwner != null && SwingUtilities.getAncestorOfClass(MapAwareOutlinePane.class, focusOwner) != null);

        final IMapViewManager mvm = Controller.getCurrentController().getMapViewManager();
        final Window window = focusOwner != null
                ? SwingUtilities.getWindowAncestor(focusOwner)
                : SwingUtilities.getWindowAncestor(Controller.getCurrentController().getViewController().getCurrentRootComponent());
        final Component mv = window != null ? mvm.getLastSelectedMapViewContainedIn(window) : mvm.getMapViewComponent();
        if (!(mv instanceof JComponent))
            return;
        final JComponent mapViewComponent = (JComponent) mv;

        mapViewComponent.putClientProperty(OUTLINE_FOCUS_PROPERTY, inOutline ? "back" : "switch");
    }
}

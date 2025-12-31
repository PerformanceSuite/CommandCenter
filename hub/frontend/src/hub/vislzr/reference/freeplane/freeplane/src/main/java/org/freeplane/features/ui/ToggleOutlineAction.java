package org.freeplane.features.ui;

import java.awt.event.ActionEvent;

import org.freeplane.core.ui.AFreeplaneAction;
import org.freeplane.core.ui.SelectableAction;
import org.freeplane.core.ui.menubuilders.generic.UserRole;

@SelectableAction(checkOnPopup = true)
class ToggleOutlineAction extends AFreeplaneAction {
    private static final long serialVersionUID = 1L;
    private final ViewController controller;

    ToggleOutlineAction(final ViewController viewController) {
        super("ToggleOutlineAction");
        this.controller = viewController;
    }

    @Override
    public void actionPerformed(final ActionEvent event) {
        controller.setOutlineVisible(!controller.isOutlineVisible());
    }

    @Override
    public void setSelected() {
        setSelected(controller.isOutlineVisible());
    }

    @Override
    public void afterMapChange(UserRole userRole) {
    }
}

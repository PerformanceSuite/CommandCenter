package org.freeplane.view.swing.map.outline;

import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

class FocusSelectedButtonClickAdapter extends MouseAdapter {
    private final OutlineFocusManager focusManager;

    FocusSelectedButtonClickAdapter(OutlineFocusManager focusManager) {
        this.focusManager = focusManager;
    }

    @Override
    public void mouseClicked(MouseEvent e) {
        focusManager.focusSelectionButtonLater(true);
    }
}

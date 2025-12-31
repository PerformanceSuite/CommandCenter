package org.freeplane.view.swing.map.outline;

import java.awt.Component;
import java.awt.Container;
import java.awt.KeyboardFocusManager;
import java.awt.Window;

import javax.swing.FocusManager;
import javax.swing.SwingUtilities;

class OutlineFocusManager {
    private final ScrollableTreePanel panel;
    private final BreadcrumbPanel breadcrumbPanel;
    private final OutlineSelection outlineSelection;

    OutlineFocusManager(ScrollableTreePanel panel, BreadcrumbPanel breadcrumbPanel, OutlineSelection outlineSelection) {
        this.panel = panel;
        this.breadcrumbPanel = breadcrumbPanel;
        this.outlineSelection = outlineSelection;
    }

    boolean isWithinOutline(Component c) {
        if (c == null) return false;
        return SwingUtilities.isDescendingFrom(c, panel) || SwingUtilities.isDescendingFrom(c, breadcrumbPanel);
    }

    boolean isNodeButtonFocused() {
        final Component focusOwner = FocusManager.getCurrentManager().getFocusOwner();
        final Container outlinePane = SwingUtilities.getAncestorOfClass(OutlinePane.class, panel);
        final boolean wasFocused = (focusOwner instanceof NodeButton) && outlinePane != null && SwingUtilities.isDescendingFrom(focusOwner, outlinePane);
        return wasFocused;
    }

    void focusSelectionButtonLater(boolean requestFocus) {
        SwingUtilities.invokeLater(() -> focusSelectionButton(requestFocus));
    }

    void focusSelectionButton(boolean requestFocusInWindow) {
        TreeNode selected = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        if (selected == null) {
            return;
        }
        if(! requestFocusInWindow) {
            final Component focusOwner = FocusManager.getCurrentManager().getCurrentFocusCycleRoot();
            if(focusOwner == null)
            	return;
            if (! SwingUtilities.isDescendingFrom(focusOwner, panel)) {
                return;
            }
        }
        boolean isSelectionDrivenBreadcrumbMode = panel.isSelectionDrivenBreadcrumbMode();
        TreeNode n = outlineSelection.getSelectedNode();
        while (n != null) {
            if (!isSelectionDrivenBreadcrumbMode && focusButtonInBreadcrumbForNode(n)) return;
            if (focusButtonInBlocksForNode(n)) return;
            if (isSelectionDrivenBreadcrumbMode && focusButtonInBreadcrumbForNode(n)) return;
            n = n.getParent();
        }
    }

    void restoreFocusIfNeeded(boolean previousWasInOutline) {
        if (!previousWasInOutline) return;

        Window w = SwingUtilities.getWindowAncestor(panel);
        if (w == null || !w.isDisplayable()) return;

        Component current = KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner();
        if (isWithinOutline(current)) return;

        TreeNode selected = outlineSelection != null ? outlineSelection.getSelectedNode() : null;
        if (selected != null) {
            for (Component comp : breadcrumbPanel.getComponents()) {
                if (comp instanceof NodeButton) {
                    NodeButton btn = (NodeButton) comp;
                    if (btn.getNode() == selected && btn.isShowing()) {
                        btn.requestFocusInWindow();
                        return;
                    }
                }
            }
            for (BlockPanel panel : panel.getBlockPanels()) {
                for (Component comp : panel.getComponents()) {
                    if (comp instanceof NodeButton) {
                        NodeButton btn = (NodeButton) comp;
                        if (btn.getNode() == selected && btn.isShowing()) {
                            btn.requestFocusInWindow();
                            return;
                        }
                    }
                }
            }
        }
        if (panel.isShowing()) panel.requestFocusInWindow();
    }

    private boolean focusButtonInBreadcrumbForNode(TreeNode node) {
        if (node == null) return false;
        for (Component comp : breadcrumbPanel.getComponents()) {
            if (comp instanceof NodeButton) {
                NodeButton btn = (NodeButton) comp;
                if (btn.getNode() == node && btn.isShowing()) {
                    btn.requestFocusInWindow();
                    return true;
                }
            }
        }
        return false;
    }

    private boolean focusButtonInBlocksForNode(TreeNode node) {
        if (node == null) return false;
        for (BlockPanel panel : panel.getBlockPanels()) {
            for (Component comp : panel.getComponents()) {
                if (comp instanceof NodeButton) {
                    NodeButton btn = (NodeButton) comp;
                    if (btn.getNode() == node && btn.isShowing()) {
                        btn.requestFocusInWindow();
                        return true;
                    }
                }
            }
        }
        return false;
    }
}

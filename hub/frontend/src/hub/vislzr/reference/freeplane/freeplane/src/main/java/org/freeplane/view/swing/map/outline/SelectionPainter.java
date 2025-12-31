package org.freeplane.view.swing.map.outline;

import java.awt.BasicStroke;
import java.awt.Component;
import java.awt.Graphics;
import java.awt.Graphics2D;

import org.freeplane.core.resources.ResourceController;

final class SelectionPainter {
    private SelectionPainter() {}

    static void paintForBlockPanel(BlockPanel panel, ScrollableTreePanel parentPanel, OutlineSelection selection, Graphics g) {
        if (panel == null || parentPanel == null || selection == null || g == null) return;
        for (Component comp : panel.getComponents()) {
            if (comp instanceof NodeButton) {
                NodeButton btn = (NodeButton) comp;
                TreeNode node = btn.getNode();
			if (node != null && selection.isSelected(node)) {
				boolean allowBreadcrumbOverlap = parentPanel.isSelectionDrivenBreadcrumbMode();
				if (allowBreadcrumbOverlap || ! parentPanel.isNodeInBreadcrumbArea(node)) {
					paintSelection(g, panel, btn);
				}
			}
            }
        }
    }

	private static void paintSelection(Graphics g, Component panel, Component btn) {
		g.setColor(ResourceController.getResourceController().getColorProperty("standardselectednoderectanglecolor"));
		((Graphics2D)g).setStroke(new BasicStroke(3));
		final int y1 = Math.max(0, btn.getY() + 2);
		final int y2 =  Math.min(panel.getHeight() - 1, btn.getY() + OutlineGeometry.getInstance().rowHeight - 1);
		if(btn.hasFocus()) {
			final int x1 = btn.getX();
			g.drawRoundRect(x1, y1, btn.getWidth(), y2 - y1, 5, 5);
		}
		else {
			g.drawLine(0, y1, panel.getWidth(), y1);
			g.drawLine(0, y2, panel.getWidth(), y2);
		}
	}

	static void paintForBreadcrumbPanel(BreadcrumbPanel panel, OutlineController controller, OutlineSelection selection, Graphics g) {
        if (panel == null || controller == null || selection == null || g == null) return;
        if (controller.getBreadcrumbMode() == BreadcrumbMode.FOLLOW_SELECTED_ITEM) return;
        for (Component comp : panel.getComponents()) {
            if (comp instanceof NodeButton) {
                NodeButton btn = (NodeButton) comp;
                TreeNode node = btn.getNode();
                if (node != null && selection.isSelected(node)) {
                	paintSelection(g, panel, btn);
                }
            }
        }
    }
}

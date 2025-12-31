package org.freeplane.view.swing.map.outline;

import java.awt.Point;

import javax.swing.JComponent;
import javax.swing.JScrollPane;

class OutlineViewport {
    private final JScrollPane scrollPane;
    private final VisibleOutlineNodes visibleState;
    private final int blockSize;
    OutlineViewport(JScrollPane scrollPane, VisibleOutlineNodes visibleState, int blockSize) {
        this.scrollPane = scrollPane;
        this.visibleState = visibleState;
		this.blockSize = blockSize;
    }

    private void setViewPosition(Point position) {
        scrollPane.getViewport().setViewPosition(position);
    }

    void setViewPosition(int startFromNodeIndex, int blockBreadcrumbOverlap) {
    	OutlineGeometry instance = OutlineGeometry.getInstance();
		int rowHeight = instance.rowHeight;
    	int targetY = (startFromNodeIndex * rowHeight) - blockBreadcrumbOverlap;
    	targetY = Math.max(0, targetY);
    	Point viewPosition = new Point(-scrollPane.getViewport().getView().getX(), targetY);
    	setViewPosition(viewPosition);
    }

	int getViewportHeight() {
		int viewportHeight = scrollPane.getViewport().getHeight();
		return viewportHeight;
	}
	int getViewY() {
		int viewY = -scrollPane.getViewport().getView().getY();
		return viewY;
	}

    int getViewportWidth() {
        return scrollPane.getViewport().getWidth();
    }

    void refreshViewport() {
        java.awt.Component view = scrollPane.getViewport().getView();
        if (view instanceof JComponent) {
            ((JComponent) view).revalidate();
        }
        scrollPane.getViewport().revalidate();
        scrollPane.repaint();
    }

    OutlineVisibleBlockRange calculateVisibleBlockRange() {
        OutlineGeometry geometry = OutlineGeometry.getInstance();
		int blockHeight = blockSize * geometry.rowHeight;
        int visibleNodeCount = visibleState.getVisibleNodeCount();
        int totalBlocks = (visibleNodeCount + blockSize - 1) / blockSize;

        int breadcrumbHeight = visibleState.getBreadcrumbHeight();
        int blockPanelY = visibleState.getBlockPanelY();
		int adjustedViewY = Math.max(0, getViewY() - (breadcrumbHeight - blockPanelY));
        int adjustedViewHeight = getViewportHeight();

        int firstBlock = Math.max(0, adjustedViewY / blockHeight);
        int lastBlock = Math.min(totalBlocks - 1, (adjustedViewY + adjustedViewHeight) / blockHeight);

        int viewportWidth = getViewportWidth();
        return new OutlineVisibleBlockRange(firstBlock, lastBlock, breadcrumbHeight, viewportWidth, visibleNodeCount);
    }
}

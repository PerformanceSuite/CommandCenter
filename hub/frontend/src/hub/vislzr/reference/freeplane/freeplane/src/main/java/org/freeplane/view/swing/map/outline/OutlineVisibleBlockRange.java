package org.freeplane.view.swing.map.outline;

class OutlineVisibleBlockRange {
    private final int firstBlock;
    private final int lastBlock;
    private final int breadcrumbHeight;
    private final int viewportWidth;
    private final int visibleNodeCount;

    OutlineVisibleBlockRange(int firstBlock, int lastBlock, int breadcrumbHeight, int viewportWidth, int visibleNodeCount) {
        this.firstBlock = firstBlock;
        this.lastBlock = lastBlock;
        this.breadcrumbHeight = breadcrumbHeight;
        this.viewportWidth = viewportWidth;
        this.visibleNodeCount = visibleNodeCount;
    }

    int getFirstBlock() { return firstBlock; }
    int getLastBlock() { return lastBlock; }
    int getBreadcrumbHeight() { return breadcrumbHeight; }
    int getViewportWidth() { return viewportWidth; }
    int getVisibleNodeCount() { return visibleNodeCount; }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (!(obj instanceof OutlineVisibleBlockRange)) return false;
        OutlineVisibleBlockRange other = (OutlineVisibleBlockRange) obj;
        return firstBlock == other.firstBlock
                && lastBlock == other.lastBlock
                && breadcrumbHeight == other.breadcrumbHeight
                && viewportWidth == other.viewportWidth
                && visibleNodeCount == other.visibleNodeCount;
    }

    @Override
    public int hashCode() {
        int result = Integer.hashCode(firstBlock);
        result = 31 * result + Integer.hashCode(lastBlock);
        result = 31 * result + Integer.hashCode(breadcrumbHeight);
        result = 31 * result + Integer.hashCode(viewportWidth);
        result = 31 * result + Integer.hashCode(visibleNodeCount);
        return result;
    }

    @Override
    public String toString() {
        return "OutlineVisibleBlockRange [firstBlock=" + firstBlock + ", lastBlock=" + lastBlock
                + ", breadcrumbHeight=" + breadcrumbHeight + ", viewportWidth=" + viewportWidth
                + ", visibleNodeCount=" + visibleNodeCount + "]";
    }
}

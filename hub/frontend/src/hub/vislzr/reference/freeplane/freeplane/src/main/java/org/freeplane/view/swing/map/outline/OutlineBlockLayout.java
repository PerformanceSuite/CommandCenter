package org.freeplane.view.swing.map.outline;

import java.awt.Component;
import java.awt.Dimension;
import java.awt.Rectangle;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JButton;
import javax.swing.JPanel;

class OutlineBlockLayout {
    private final OutlineBlockViewCache blockCache;
    private final VisibleOutlineNodes visibleState;
    private OutlineGeometry geometry;
    private final int blockSize;
    private final ScrollableTreePanel treePanel;
    private int cachedMaxWidth = 0;

    OutlineBlockLayout(OutlineBlockViewCache blockCache,
                       VisibleOutlineNodes visibleState,
                       OutlineGeometry geometry,
                       int blockSize,
                       ScrollableTreePanel treePanel) {
        this.blockCache = blockCache;
        this.visibleState = visibleState;
        this.geometry = geometry;
        this.blockSize = blockSize;
        this.treePanel = treePanel;
    }

    void updateGeometry(OutlineGeometry geometry) {
        this.geometry = geometry;
        resetCachedMaxWidth();
    }

    void updateVisibleBlocks(JPanel owner, OutlineVisibleBlockRange range, int panelWidth) {
        for (int b = range.getFirstBlock(); b <= range.getLastBlock(); b++) {
            if (!blockCache.has(b)) {
                createBlock(owner, b, panelWidth);
            }
        }
        owner.repaint();
    }

    void removeBlocksFromBlockIndex(JPanel owner, int startBlock) {
        List<Integer> indices = new ArrayList<>(blockCache.keySet());
        for (int idx : indices) {
            if (idx >= startBlock) {
                BlockPanel p = blockCache.get(idx);
                if (p != null) owner.remove(p);
                blockCache.remove(idx);
            }
        }
    }

    void updateBlockPreferredSize(JPanel owner) {
        final int visibleNodeCount = visibleState.getVisibleNodeCount();
        int height =(visibleNodeCount + 1) * geometry.rowHeight;
        Dimension preferredSize = new Dimension(cachedMaxWidth, height);
        owner.setPreferredSize(preferredSize);

        for (BlockPanel panel : blockCache.blockPanels()) {
            panel.setSize(cachedMaxWidth, panel.getHeight());
        }
    }

    private void createBlock(JPanel owner, int blockIndex, int panelWidth) {
        int start = blockIndex * blockSize;
        int end = Math.min(start + blockSize, visibleState.getVisibleNodeCount());

        List<TreeNode> blockNodes = new ArrayList<>();
        for (int i = start; i < end; i++) {
            TreeNode n = visibleState.getNodeAtVisibleIndex(i);
            if (n != null) blockNodes.add(n);
        }
        BlockPanel bp = new BlockPanel(blockNodes, geometry.rowHeight, geometry.outlineTextOrientation, treePanel, treePanel.getOutlineSelection());
        bp.setComponentOrientation(geometry.outlineTextOrientation);
        Rectangle bounds = calculateBlockBounds(blockIndex, blockSize, panelWidth);
        bp.setBounds(bounds);
        owner.add(bp);
        blockCache.put(blockIndex, bp);
        boolean rightToLeft = geometry.isRightToLeft();
        for (Component comp : bp.getComponents()) {
            if (comp instanceof JButton) {
                int rightEdge = rightToLeft ? panelWidth - comp.getX()  : comp.getX() + comp.getWidth();
                if (rightEdge > cachedMaxWidth) cachedMaxWidth = rightEdge;
            }
        }
    }

    private Rectangle calculateBlockBounds(int blockIndex, int blockSize, int panelWidth) {
        int start = blockIndex * blockSize;

        int end = Math.min(start + blockSize, visibleState.getVisibleNodeCount());
        int visibleNodesInBlock = end - start;

        int rowHeight = geometry.rowHeight;
        int blockY = start * rowHeight;
        int blockHeight = visibleNodesInBlock * rowHeight;

        return new Rectangle(0, blockY, panelWidth, blockHeight);
    }


    void recordButtonRightEdge(int rightEdge) {
        if (rightEdge > cachedMaxWidth) cachedMaxWidth = rightEdge;
    }

    void resetCachedMaxWidth() {
        cachedMaxWidth = 0;
    }

    void removeBlocksOutsideRange(JPanel owner, OutlineVisibleBlockRange range) {
        List<Integer> toRemove = new ArrayList<>();
        for (int idx : blockCache.keySet()) {
            if (idx < range.getFirstBlock() || idx > range.getLastBlock()) {
                BlockPanel p = blockCache.get(idx);
                if (p != null) owner.remove(p);
                toRemove.add(idx);
            }
        }
        for (int idx : toRemove) blockCache.remove(idx);
    }
}

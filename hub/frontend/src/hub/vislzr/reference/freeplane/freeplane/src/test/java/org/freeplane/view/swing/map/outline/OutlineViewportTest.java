package org.freeplane.view.swing.map.outline;

import org.junit.Test;
import static org.assertj.core.api.Assertions.assertThat;

import javax.swing.*;
import java.awt.*;

public class OutlineViewportTest {

    private static TreeNode createLinearTree(int count) {
        TreeNode root = new TreeNode("root", () -> "root");
        for (int i = 0; i < count; i++) {
        	int k = i;
            root.addChild(new TreeNode("id"+i, () -> "n" + k));
        }
        root.applyExpansionLevel(1);
        return root;
    }

    @Test
    public void calculatesVisibleBlockRangeWithBreadcrumbOffset() {
        OutlineGeometry geometry = OutlineGeometry.getInstance();
        TreeNode root = createLinearTree(25);

        VisibleOutlineNodes vs = new VisibleOutlineNodes(root);
        vs.setBreadcrumbHeight(geometry.rowHeight * 2);

        JPanel view = new JPanel();
        view.setPreferredSize(new Dimension(600, geometry.rowHeight * 100));
        JScrollPane scroll = new JScrollPane(view);
        JViewport viewport = scroll.getViewport();
        viewport.setView(view);
        viewport.setExtentSize(new Dimension(600, geometry.rowHeight * 5));
        viewport.setViewPosition(new Point(0, geometry.rowHeight * 0));

        int blockSize = 10;
        OutlineViewport ov = new OutlineViewport(scroll, vs, blockSize);

        OutlineVisibleBlockRange r0 = ov.calculateVisibleBlockRange();
        assertThat(r0.getFirstBlock()).isEqualTo(0);
        assertThat(r0.getLastBlock()).isGreaterThanOrEqualTo(0);
        assertThat(r0.getBreadcrumbHeight()).isEqualTo(geometry.rowHeight * 2);

        // Scroll down by one block + breadcrumb height to land in block 1
        int blockHeight = blockSize * geometry.rowHeight;
        viewport.setViewPosition(new Point(0, blockHeight + vs.getBreadcrumbHeight() + 1));
        OutlineVisibleBlockRange r1 = ov.calculateVisibleBlockRange();
        assertThat(r1.getFirstBlock()).isGreaterThanOrEqualTo(1);
        assertThat(r1.getLastBlock()).isGreaterThanOrEqualTo(r1.getFirstBlock());
    }
}

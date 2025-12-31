package org.freeplane.view.swing.map.outline;

import org.junit.Test;
import static org.assertj.core.api.Assertions.assertThat;

public class OutlineSelectionHistoryTest {

    @Test
    public void preferredChildDefaultsToFirstAndTracksLastSelected() {
        TreeNode parent = new TreeNode("p", () -> "p");
        TreeNode c1 = new TreeNode("c1", () -> "c1");
        TreeNode c2 = new TreeNode("c2", () -> "c2");
        parent.addChild(c1);
        parent.addChild(c2);

        OutlineSelectionHistory uut = new OutlineSelectionHistory();

        // Default to first
        assertThat(uut.preferredChild(parent)).isSameAs(c1);

        // After selecting c2, it becomes preferred
        uut.record(c2);
        assertThat(uut.preferredChild(parent)).isSameAs(c2);
    }
}

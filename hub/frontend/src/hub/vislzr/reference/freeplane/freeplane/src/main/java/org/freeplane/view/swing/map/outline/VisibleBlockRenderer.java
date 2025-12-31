package org.freeplane.view.swing.map.outline;

import java.awt.Component;
import java.awt.KeyboardFocusManager;
import java.util.function.IntSupplier;
import java.util.function.Predicate;

import javax.swing.JPanel;

final class VisibleBlockRenderer {
    private OutlineViewport viewport;
    private final OutlineBlockLayout blockLayout;
    private final OutlineBlockViewCache blockCache;
    private final JPanel blockPanel;
    private final VisibleOutlineNodes visibleNodes;
    private final NavigationButtons navigationButtons;
    private final OutlineFocusManager focusManager;
    private final IntSupplier panelWidthSupplier;
    private final Runnable updatePreferredSize;
    private final Runnable refreshUI;
    private final Runnable updateFirstVisibleNodeId;
    private final Predicate<TreeNode> isInBreadcrumbArea;
    private OutlineVisibleBlockRange lastVisibleRange;

    VisibleBlockRenderer(OutlineBlockLayout blockLayout,
                         OutlineBlockViewCache blockCache,
                         JPanel blockPanel,
                         VisibleOutlineNodes visibleNodes,
                         NavigationButtons navigationButtons,
                         OutlineFocusManager focusManager,
                         IntSupplier panelWidthSupplier,
                         Runnable updatePreferredSize,
                         Runnable refreshUI,
                         Runnable updateFirstVisibleNodeId,
                         Predicate<TreeNode> isInBreadcrumbArea) {
        this.blockLayout = blockLayout;
        this.blockCache = blockCache;
        this.blockPanel = blockPanel;
        this.visibleNodes = visibleNodes;
        this.navigationButtons = navigationButtons;
        this.focusManager = focusManager;
        this.panelWidthSupplier = panelWidthSupplier;
        this.updatePreferredSize = updatePreferredSize;
        this.refreshUI = refreshUI;
        this.updateFirstVisibleNodeId = updateFirstVisibleNodeId;
        this.isInBreadcrumbArea = isInBreadcrumbArea;
    }

    void setViewport(OutlineViewport viewport) {
        this.viewport = viewport;
        resetCachedRange();
    }

    void resetCachedRange() {
        lastVisibleRange = null;
    }

    void render() {
        render(false, 0);
    }

    void renderFromIndex(int startFromNodeIndex) {
        render(true, startFromNodeIndex);
    }

    private void render(boolean repositionViewport, int startFromNodeIndex) {
        if (viewport == null) {
            return;
        }

        Component previousFocus = KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner();
        boolean focusWasInsideOutline = focusManager.isWithinOutline(previousFocus);

        if (repositionViewport) {
            viewport.setViewPosition(startFromNodeIndex, visibleNodes.getBreadcrumbHeight() - visibleNodes.getBlockPanelY());
        }

        OutlineVisibleBlockRange range = viewport.calculateVisibleBlockRange();
        boolean haveBlocks = !blockCache.isEmpty();
        boolean unchanged = !repositionViewport && haveBlocks && range.equals(lastVisibleRange);

        if (unchanged) {
            viewport.refreshViewport();
            updateFirstVisibleNodeId.run();
            lastVisibleRange = range;
            focusManager.restoreFocusIfNeeded(focusWasInsideOutline);
            return;
        }

        blockLayout.removeBlocksOutsideRange(blockPanel, range);
        blockLayout.updateVisibleBlocks(blockPanel, range, panelWidthSupplier.getAsInt());

        lastVisibleRange = range;

        updatePreferredSize.run();
        refreshUI.run();
        updateFirstVisibleNodeId.run();
        attachNavigationButtonsIfNeeded();

        focusManager.restoreFocusIfNeeded(focusWasInsideOutline);
    }

    private void attachNavigationButtonsIfNeeded() {
        TreeNode hoveredNode = visibleNodes.getHoveredNode();
        if (hoveredNode == null || hoveredNode.getChildren().isEmpty()) {
            return;
        }
        boolean inBreadcrumb = visibleNodes.isHoveredNodeContainedInBreadcrumb() && isInBreadcrumbArea.test(hoveredNode);
        if (!inBreadcrumb) {
            navigationButtons.attachToNode(hoveredNode, blockPanel, visibleNodes.findNodeIndexInVisibleList(hoveredNode), hoveredNode.getLevel());
        }
    }
}

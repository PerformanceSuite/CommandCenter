package org.freeplane.view.swing.map.outline;

import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

class OutlineBlockViewCache {
    private final Map<Integer, BlockPanel> blocks = new HashMap<>();

    boolean has(int blockIndex) { return blocks.containsKey(blockIndex); }
    BlockPanel get(int blockIndex) { return blocks.get(blockIndex); }
    void put(int blockIndex, BlockPanel panel) { blocks.put(blockIndex, panel); }
    void remove(int blockIndex) { blocks.remove(blockIndex); }
    void clear() { blocks.clear(); }
    boolean isEmpty() { return blocks.isEmpty(); }
    Set<Integer> keySet() { return Collections.unmodifiableSet(blocks.keySet()); }
    Collection<BlockPanel> blockPanels() { return Collections.unmodifiableCollection(blocks.values()); }
    void setBlockWidhts(int width) {
    	blocks.values().forEach(block -> block.setSize(width, block.getHeight()));
    }
}

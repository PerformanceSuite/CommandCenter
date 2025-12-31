/*
 * Created on 2 Nov 2025
 *
 * author dimitry
 */
package org.freeplane.view.swing.map.edge;

import java.awt.Color;

public interface EdgeColorContext {
	int computeColumnPaletteIndex();
	int computeBranchPaletteIndex();
	int computeLevelPaletteIndex();
	Color getParentEdgeColor();
}

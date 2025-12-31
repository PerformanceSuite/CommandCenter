package org.freeplane.view.swing.map.edge;

import java.awt.Color;

import org.freeplane.core.util.ObjectRule;
import org.freeplane.features.edge.EdgeController;
import org.freeplane.features.map.MapModel;
import org.freeplane.features.mode.ModeController;

public class AutomaticEdgeStyle {
	private final ModeController modeController;
	private final MapModel mapModel;
	private final EdgeColorContext edgeColorContext;

	public AutomaticEdgeStyle(ModeController modeController, MapModel mapModel,
			EdgeColorContext edgeColorContext) {
		this.modeController = modeController;
		this.mapModel = mapModel;
		this.edgeColorContext = edgeColorContext;
	}

	public Color resolve(ObjectRule<Color, EdgeController.Rules> edgeColorRule) {
		if (edgeColorRule == null)
			return EdgeController.STANDARD_EDGE_COLOR;
		if (edgeColorRule.hasValue())
			return edgeColorRule.getValue();
		EdgeController.Rules rule = edgeColorRule.getRule();
		if (rule == null)
			return EdgeController.STANDARD_EDGE_COLOR;
		Color color = resolve(rule);
		if (color != null && shouldCache(rule))
			edgeColorRule.setCache(color);
		return color != null ? color : EdgeController.STANDARD_EDGE_COLOR;
	}

	private Color resolve(EdgeController.Rules rule) {
		switch (rule) {
		case BY_PARENT:
			return edgeColorContext.getParentEdgeColor();
		case BY_COLUMN:
			return resolvePaletteColor(edgeColorContext.computeColumnPaletteIndex(), true);
		case BY_BRANCH:
			return resolvePaletteColor(edgeColorContext.computeBranchPaletteIndex(), false);
		case BY_LEVEL:
			return resolvePaletteColor(edgeColorContext.computeLevelPaletteIndex(), false);
		default:
			return null;
		}
	}

	private boolean shouldCache(EdgeController.Rules rule) {
		return rule != EdgeController.Rules.BY_PARENT;
	}

	private Color resolvePaletteColor(int paletteIndex, boolean useStandardColorFallback) {
		if (modeController == null || mapModel == null)
			return useStandardColorFallback ? EdgeController.STANDARD_EDGE_COLOR : null;
		if (paletteIndex == -1)
			return null;
		EdgeController edgeController = modeController.getExtension(EdgeController.class);
		if (edgeController == null)
			return useStandardColorFallback ? EdgeController.STANDARD_EDGE_COLOR : null;
		if (edgeController.areEdgeColorsAvailable(mapModel))
			return edgeController.getEdgeColor(mapModel, paletteIndex);
		return useStandardColorFallback ? EdgeController.STANDARD_EDGE_COLOR : null;
	}
}

package org.freeplane.view.swing.map.outline;

import java.awt.ComponentOrientation;
import java.awt.Dimension;
import java.awt.Insets;
import java.util.ArrayList;
import java.util.List;

import javax.swing.BorderFactory;
import javax.swing.JButton;

import org.freeplane.api.LengthUnit;
import org.freeplane.api.Quantity;
import org.freeplane.api.TextWritingDirection;
import org.freeplane.core.resources.ResourceController;
import org.freeplane.core.ui.components.UITools;
import org.freeplane.features.mode.Controller;

class OutlineGeometry {
	interface GeometryListener {
		void onGeometryChanged(OutlineGeometry geometry);
	}

	private static final List<GeometryListener> LISTENERS = new ArrayList<>();
	private static OutlineGeometry INSTANCE;
	static OutlineGeometry getInstance() {return INSTANCE;}
	final int rowHeight;
	final int navButtonWidth;
	private final int indent;
	private final float itemFontSize;
	final ComponentOrientation outlineTextOrientation;

	float getItemFontSize() {
		return itemFontSize;
	}

	boolean isRightToLeft() {
		boolean applyRightToLeft = outlineTextOrientation.isHorizontal() && !outlineTextOrientation.isLeftToRight();
		return applyRightToLeft;
	}


	static {
		if(Controller.getCurrentController() != null) {
			INSTANCE = createFromConfiguration();
			final ResourceController resourceController = ResourceController.getResourceController();
			resourceController.setDefaultProperty("outlineItemIndentation",
					asLength(INSTANCE.rowHeight).toString());
			resourceController.addPropertyChangeListener(OutlineGeometry::updateGeometry);
		}
		else
			INSTANCE = new OutlineGeometry(10, 10, 10, UITools.FONT_SCALE_FACTOR * 8f, ComponentOrientation.LEFT_TO_RIGHT);
	}

	private static Quantity<LengthUnit> asLength(int rowHeight) {
		return new Quantity<>(rowHeight, LengthUnit.px).in(LengthUnit.mm);
	}

	@SuppressWarnings("unused")
	private static void updateGeometry(String propertyName, String newValue, String oldValue) {
		if(propertyName.equals("outlineItemFontSize")
				|| propertyName.equals("outlineItemIndentation")
				|| propertyName.equals("showOutlineFoldingButtons")
				|| propertyName.equals("outlineTextWritingDirection"))
			replaceInstance(createFromConfiguration());
	}

	static void registerListener(GeometryListener listener) {
		if(listener == null)
			return;
		LISTENERS.add(listener);
	}

	static void unregisterListener(GeometryListener listener) {
		if(listener == null)
			return;
		LISTENERS.remove(listener);
	}

	private static void replaceInstance(OutlineGeometry newInstance) {
		INSTANCE = newInstance;
		for(GeometryListener listener : LISTENERS) {
			listener.onGeometryChanged(INSTANCE);
		}
	}

	private static OutlineGeometry createFromConfiguration() {
		final ResourceController resourceController = ResourceController.getResourceController();
		final float configuredItemFontSize = UITools.FONT_SCALE_FACTOR * (float) resourceController.getDoubleProperty("outlineItemFontSize", 8f);

		JButton sampleButton = new JButton("▼");
		sampleButton.setMargin(new Insets(0, 0, 0, 0));
		sampleButton.setFont(sampleButton.getFont().deriveFont(configuredItemFontSize * 5 / 4));
		sampleButton.setBorder(BorderFactory.createRaisedBevelBorder());

		final Dimension preferredButtonSize = sampleButton.getPreferredSize();
		final int configuredRowHeight = Math.round(preferredButtonSize.height);
		final Quantity<LengthUnit> indentQuantity = resourceController.getLengthQuantityProperty("outlineItemIndentation");
		final int configuredIndent = indentQuantity != null ? indentQuantity.toBaseUnitsRounded() : configuredRowHeight;

		final int configuredNavigationButtonWidth;
		if(resourceController.getBooleanProperty("showOutlineFoldingButtons", true))
			configuredNavigationButtonWidth = Math.round(preferredButtonSize.width * 20 / 13);
		else
			configuredNavigationButtonWidth = 0;
		TextWritingDirection textWritingDirection = resourceController.getEnumProperty("outlineTextWritingDirection", TextWritingDirection.DEFAULT);
        ComponentOrientation componentOrientation = textWritingDirection == TextWritingDirection.RIGHT_TO_LEFT ? ComponentOrientation.RIGHT_TO_LEFT : ComponentOrientation.LEFT_TO_RIGHT;

		return new OutlineGeometry(configuredRowHeight, configuredNavigationButtonWidth, configuredIndent, configuredItemFontSize, componentOrientation);
	}

	private OutlineGeometry(int rowHeight, int navigationButtonWidth, int indent, float itemFontSize, ComponentOrientation componentOrientation) {
		this.rowHeight = rowHeight;
		this.navButtonWidth = navigationButtonWidth;
		this.indent = indent;
		this.itemFontSize = itemFontSize;
		this.outlineTextOrientation = componentOrientation;
	}

    int calculateNodeButtonX(boolean showNavigationButtons, int level) {
    	if(!showNavigationButtons  || navButtonWidth == 0)
    		return level * indent;
    	else
    		return level * indent + 2 * navButtonWidth;
    }

	int calculateNavigationButtonX(final int rowIndent) {
		final int baseX = rowIndent * indent;
		return baseX;
	}
}

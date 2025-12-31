package org.freeplane.core.ui.components;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Component;
import java.awt.ComponentOrientation;
import java.awt.FontMetrics;
import java.awt.Graphics;

public class DoubleTextIcon implements StyledIcon {
    private final TextIcon firstIcon;
    private final TextIcon secondIcon;
    private int paddingX;
    private int paddingY;
    private Color iconBackgroundColor;
    private Color underlineColor;
    private BasicStroke underlineStroke;
    private UnderlinePosition underlinePosition = UnderlinePosition.NONE;

    public DoubleTextIcon(String leftText, String rightText, FontMetrics fontMetrics) {
        this.firstIcon = new TextIcon(leftText, fontMetrics);
        this.secondIcon = new TextIcon(rightText, fontMetrics);
        this.firstIcon.setPaddingX(0);
        this.secondIcon.setPaddingX(0);
        this.firstIcon.setPaddingY(0);
        this.secondIcon.setPaddingY(0);
        this.firstIcon.setBorderType(TextIcon.BorderType.UNDERLINE);
        this.secondIcon.setBorderType(TextIcon.BorderType.UNDERLINE);
        updateUnderlineState();
    }

    @Override
    public void paintIcon(Component component, Graphics graphics, int x, int y) {
        int iconWidth = getIconWidth();
        int iconHeight = getIconHeight();
        if(iconBackgroundColor != null) {
            Color originalColor = graphics.getColor();
            graphics.setColor(iconBackgroundColor);
            graphics.fillRect(x, y, iconWidth, iconHeight);
            graphics.setColor(originalColor);
        }
        int contentX = x + paddingX;
        int contentY = y + paddingY;
        ComponentOrientation orientation = component != null ? component.getComponentOrientation() : null;
        boolean paintRightToLeft = orientation != null && orientation.isHorizontal() && !orientation.isLeftToRight();
        TextIcon leftIcon = paintRightToLeft ? secondIcon : firstIcon;
        TextIcon rightIcon = paintRightToLeft ? firstIcon : secondIcon;
        leftIcon.paintIcon(component, graphics, contentX, contentY);
        int rightIconX = contentX + leftIcon.getIconWidth();
        rightIcon.paintIcon(component, graphics, rightIconX, contentY);
    }

    @Override
    public int getIconWidth() {
        return paddingX * 2 + firstIcon.getIconWidth() + secondIcon.getIconWidth();
    }

    @Override
    public int getIconHeight() {
        int baseHeight = Math.max(firstIcon.getIconHeight(), secondIcon.getIconHeight());
        return paddingY * 2 + baseHeight;
    }

    @Override
    public Color getIconTextColor() {
        return firstIcon.getIconTextColor();
    }

    @Override
    public DoubleTextIcon setIconTextColor(Color iconTextColor) {
        firstIcon.setIconTextColor(iconTextColor);
        secondIcon.setIconTextColor(iconTextColor);
        return this;
    }

    @Override
    public Color getIconBackgroundColor() {
        return iconBackgroundColor;
    }

    @Override
    public DoubleTextIcon setIconBackgroundColor(Color iconBackgroundColor) {
        this.iconBackgroundColor = iconBackgroundColor;
        if(iconBackgroundColor != null) {
            firstIcon.setIconBackgroundColor(iconBackgroundColor);
            secondIcon.setIconBackgroundColor(iconBackgroundColor);
        }
        firstIcon.setIconBackgroundColor(null);
        secondIcon.setIconBackgroundColor(null);
        return this;
    }

    @Override
    public Color getIconBorderColor() {
        return underlineColor;
    }

    @Override
    public DoubleTextIcon setIconBorderColor(Color iconBorderColor) {
        this.underlineColor = iconBorderColor;
        if(iconBorderColor != null && underlineStroke == null) {
            underlineStroke = TextIcon.DEFAULT_STROKE;
        }
        updateUnderlineState();
        return this;
    }

    public TextIcon.BorderType getBorderType() {
        return TextIcon.BorderType.UNDERLINE;
    }

    @Override
    public BasicStroke getBorderStroke() {
        return underlineStroke;
    }

    @Override
    public DoubleTextIcon setBorderStroke(BasicStroke borderStroke) {
        this.underlineStroke = borderStroke;
        updateUnderlineState();
        return this;
    }

    @Override
    public int getPaddingX() {
        return paddingX;
    }

    @Override
    public void setPaddingX(int paddingX) {
        this.paddingX = paddingX;
    }

    @Override
    public int getPaddingY() {
        return paddingY;
    }

    @Override
    public void setPaddingY(int paddingY) {
        this.paddingY = paddingY;
    }

    @Override
    public void setPadding(int padding) {
        this.paddingX = padding;
        this.paddingY = padding;
    }

    public UnderlinePosition getUnderlinePosition() {
        return underlinePosition;
    }

    public DoubleTextIcon setUnderlinePosition(UnderlinePosition underlinePosition) {
        this.underlinePosition = underlinePosition;
        updateUnderlineState();
        return this;
    }

    public String getFirstText() {
        return firstIcon.getText();
    }

    public String getSecondText() {
        return secondIcon.getText();
    }

    public int getRightIconX(Component component) {
        ComponentOrientation orientation = component != null ? component.getComponentOrientation() : null;
        boolean paintRightToLeft = orientation != null && orientation.isHorizontal() && !orientation.isLeftToRight();
        int leftIconWidth = paintRightToLeft ? secondIcon.getIconWidth() : firstIcon.getIconWidth();
        return paddingX + leftIconWidth;
    }

    private void updateUnderlineState() {
        firstIcon.setIconBorderColor(underlineColor);
        secondIcon.setIconBorderColor(underlineColor);
        firstIcon.setBorderStroke(shouldPaintUnderlineFirst() ? underlineStroke : null);
        secondIcon.setBorderStroke(shouldPaintUnderlineSecond() ? underlineStroke : null);
    }

    private boolean shouldPaintUnderlineFirst() {
        return underlinePosition == UnderlinePosition.LEFT || underlinePosition == UnderlinePosition.BOTH;
    }

    private boolean shouldPaintUnderlineSecond() {
        return underlinePosition == UnderlinePosition.RIGHT || underlinePosition == UnderlinePosition.BOTH;
    }

    public enum UnderlinePosition {
        NONE,
        LEFT,
        RIGHT,
        BOTH
    }
}

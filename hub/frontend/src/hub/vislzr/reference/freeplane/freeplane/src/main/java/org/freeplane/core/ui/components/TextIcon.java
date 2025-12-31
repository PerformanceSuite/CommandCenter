/*
 * Created on 27 Sept 2024
 *
 * author dimitry
 */
package org.freeplane.core.ui.components;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Component;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;

public class TextIcon implements StyledIcon {
	public enum BorderType {UNDERLINE, ROUND_RECTANGLE}
	public static final BasicStroke DEFAULT_STROKE = new BasicStroke(1);
    private final String text;
    private final FontMetrics fontMetrics;
    private Color iconTextColor;
    private Color iconBackgroundColor;
    private Color iconBorderColor;
    private BasicStroke borderStroke;
    private int paddingX = 0;
    private int paddingY = 0;
    private BorderType borderType = BorderType.ROUND_RECTANGLE;
    public TextIcon(String text, FontMetrics fontMetrics) {
        this.text = text;
        this.fontMetrics = fontMetrics;
    }

    @Override
    public void paintIcon(Component c, Graphics g, int x, int y) {
        Graphics2D g2d = (Graphics2D) g;
        int iconWidth = getIconWidth();
        int iconHeight = getIconHeight();
        if(iconBackgroundColor != null) {
            g2d.setColor(iconBackgroundColor);
            g2d.fillRect(x, y, iconWidth, iconHeight);
        }
        Color textColor = iconTextColor != null ? iconTextColor : c.getForeground();
        int borderLineWidth = getBorderLineWidth(1);
        if(borderStroke != null) {
            Color borderColor = iconBorderColor != null ? iconBorderColor : textColor;
            g2d.setColor(borderColor);
            g2d.setStroke(borderStroke);
            if(borderType == BorderType.ROUND_RECTANGLE)
            	g2d.drawRoundRect(x + borderLineWidth, y + borderLineWidth, iconWidth - 2 * borderLineWidth - 1, iconHeight - 2 * borderLineWidth - 1, iconHeight / 8, iconHeight / 8);
			else {
				int lineY = y + iconHeight - 2 * borderLineWidth - 1;
				g2d.drawLine(x, lineY, x + iconWidth - 1, lineY);
			}
        }
        if(text != null) {
            g2d.setColor(textColor);
            g2d.setFont(fontMetrics.getFont());
			int textX = x + paddingX;
            int textY = y + paddingY + fontMetrics.getAscent();
            if(borderLineWidth != 0 && borderType == BorderType.ROUND_RECTANGLE) {
            	textX += borderLineWidth;
            	textY += borderLineWidth;
            }
            Object textHint = g2d.getRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING);
            if(! RenderingHints.VALUE_TEXT_ANTIALIAS_ON.equals(textHint)) {
				g2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
				g2d.drawString(text, textX, textY);
				g2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, textHint);
			}
            else
				g2d.drawString(text, textX, textY);

        }
    }

    @Override
    public Color getIconTextColor() {
        return iconTextColor;
    }

    @Override
    public TextIcon setIconTextColor(Color iconTextColor) {
        this.iconTextColor = iconTextColor;
        return this;
    }

    @Override
    public Color getIconBackgroundColor() {
        return iconBackgroundColor;
    }

    @Override
    public TextIcon setIconBackgroundColor(Color iconBackgroundColor) {
        this.iconBackgroundColor = iconBackgroundColor;
        if(iconTextColor == null)
            iconTextColor = UITools.getTextColorForBackground(iconBackgroundColor);
        return this;
    }

    @Override
    public Color getIconBorderColor() {
        return iconBorderColor;
    }

    @Override
    public TextIcon setIconBorderColor(Color iconBorderColor) {
        this.iconBorderColor = iconBorderColor;
        if(iconBorderColor != null && borderStroke == null)
        	borderStroke = DEFAULT_STROKE;
        return this;
    }

    public BorderType getBorderType() {
		return borderType;
	}

    public void setBorderType(BorderType borderType) {
		this.borderType = borderType;
	}

	@Override
    public BasicStroke getBorderStroke() {
        return borderStroke;
    }

    @Override
    public TextIcon setBorderStroke(BasicStroke borderStroke) {
        this.borderStroke = borderStroke;
        return this;
    }

    @Override
    public int getIconWidth() {
        return (text == null ? 0 : fontMetrics.stringWidth(text)) +  2 * paddingX + (borderType ==  BorderType.ROUND_RECTANGLE ? getBorderLineWidth(2) : 0);
    }

    @Override
    public int getIconHeight() {
        return fontMetrics.getHeight() + 2 * paddingY + getBorderLineWidth(borderType ==  BorderType.ROUND_RECTANGLE ? 3 : 2);
    }

	private int getBorderLineWidth(int weight) {
		return borderStroke != null ? (int) (borderStroke.getLineWidth() * weight) : 0;
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
		setPaddingX(padding);
		setPaddingY(padding);
    }

    public String getText() {
        return text;
    }
}

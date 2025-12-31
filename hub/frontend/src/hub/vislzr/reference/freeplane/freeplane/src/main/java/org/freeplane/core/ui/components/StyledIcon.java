package org.freeplane.core.ui.components;

import java.awt.BasicStroke;
import java.awt.Color;

import javax.swing.Icon;

public interface StyledIcon extends Icon {
    Color getIconTextColor();
    StyledIcon setIconTextColor(Color iconTextColor);

    Color getIconBackgroundColor();
    StyledIcon setIconBackgroundColor(Color iconBackgroundColor);

    Color getIconBorderColor();
    StyledIcon setIconBorderColor(Color iconBorderColor);

    BasicStroke getBorderStroke();
    StyledIcon setBorderStroke(BasicStroke borderStroke);

    int getPaddingX();
    void setPaddingX(int paddingX);

    int getPaddingY();
    void setPaddingY(int paddingY);

    void setPadding(int padding);
}

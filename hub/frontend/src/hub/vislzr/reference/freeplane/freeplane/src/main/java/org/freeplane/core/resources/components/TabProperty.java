/*
 *  Freeplane - mind map editor
 *  Copyright (C) 2008 Dimitry Polivaev
 *
 *  This file author is Dimitry Polivaev
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.freeplane.core.resources.components;

import com.jgoodies.forms.builder.DefaultFormBuilder;

/**
 * @author Dimitry Polivaev
 * 27.12.2008
 */
public class TabProperty implements IPropertyControl {
    private static final String DEFAULT_LAYOUT_FORMAT = "right:max(40dlu;p), 4dlu, 200dlu:grow, 7dlu";
    private final String name;
    private final String labelKey;
    private final String layoutFormat;

    public TabProperty(final String name, final String labelKey) {
        this(name, labelKey, TabProperty.DEFAULT_LAYOUT_FORMAT);
    }

    public TabProperty(final String name, final String labelKey, final String layoutFormat) {
        super();
        this.name = name;
        this.labelKey = labelKey;
        this.layoutFormat = layoutFormat != null ? layoutFormat : TabProperty.DEFAULT_LAYOUT_FORMAT;
    }

    @Override
    public String getTooltip() {
        return null;
    }

    @Override
    public String getName() {
        return name;
    }

    public String getLabel() {
        return labelKey;
    }

    public String getLayout() {
        return layoutFormat;
    }

	@Override
	public void appendToForm(final DefaultFormBuilder builder) {
	}

	@Override
	public void setEnabled(final boolean pEnabled) {
	}
}

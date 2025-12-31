/*
 *  Freeplane - mind map editor
 *  Copyright (C) 2011 dimitry
 *
 *  This file author is dimitry
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
package org.freeplane.features.styles;

import java.awt.event.ActionEvent;

import javax.swing.JComponent;

import org.freeplane.core.ui.AFreeplaneAction;
import org.freeplane.core.ui.EnabledAction;
import org.freeplane.core.ui.SelectableAction;
import org.freeplane.core.util.TextUtils;
import org.freeplane.features.mode.Controller;

/**
 * @author Dimitry Polivaev
 * Mar 2, 2017
 */
@SuppressWarnings("serial")
@SelectableAction(checkOnPopup = true)
@EnabledAction(checkOnNodeChange = true)
public class SetStringMapViewPropertyAction extends AFreeplaneAction{
	private static String extractPropertyWithOption(String argument) {
		boolean isDefault = argument.endsWith(AS_DEFAULT);
	    String property;
	    if(isDefault) {
	    	property = argument.substring(0, argument.length() - AS_DEFAULT.length()).trim();
	    }
	    else {
	    	property = argument;
	    }
		return property;
	}
	private static final String AS_DEFAULT = "(default)";
	private final String propertyName;
	private final String propertyValue;
	private final String property;
	private final boolean isDefault;
	public SetStringMapViewPropertyAction(String argument) {
	    super("SetStringMapViewPropertyAction." + extractPropertyWithOption(argument),
	    	TextUtils.getRawText("OptionPanel." + extractPropertyWithOption(argument)),
	    	null);
	    this.property = extractPropertyWithOption(argument);
	    int separatorIndex = property.indexOf('.');
	    this.propertyName = property.substring(0, separatorIndex);
	    this.propertyValue = property.substring(separatorIndex + 1);
	    this.isDefault = property != argument;
	    String propertyWithOption = extractPropertyWithOption(argument);
	    setIcon(propertyWithOption + ".icon");
	    setTooltip(getTooltipKey());
    }


	@Override
	public void actionPerformed(ActionEvent e) {
		final JComponent mapViewComponent = getMapViewComponent();
		if(mapViewComponent != null) {
			final Object value = mapViewComponent.getClientProperty(propertyName);
			mapViewComponent.putClientProperty(propertyName, propertyValue);
			setSelected(true);
		}
    }

	private JComponent getMapViewComponent() {
		final JComponent mapViewComponent = Controller.getCurrentController().getMapViewManager().getMapViewComponent();
		return mapViewComponent;
	}

	@Override
	public String getTextKey() {
		return "OptionPanel." + property;
	}

	@Override
	public String getTooltipKey() {
		return getTextKey() + ".tooltip";
	}

	@Override
	public void setSelected() {
		try {
			final JComponent mapViewComponent = getMapViewComponent();
			if(mapViewComponent != null) {
				final Object currentValue = mapViewComponent.getClientProperty(propertyName);
				final boolean isSet = currentValue == null && isDefault || propertyValue.equals(currentValue);
				setSelected(isSet);
				return;
			}
		}
		catch (Exception e) {
		}
		setSelected(false);
	}

	@Override
	public void setEnabled() {
		setEnabled(getMapViewComponent() != null);
	}

}

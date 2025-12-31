/*
 *  Freeplane - mind map editor
 *  Copyright (C) 2020 Felix Natter
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
package org.freeplane.features.commandsearch;

import static org.freeplane.features.commandsearch.SearchItem.ITEM_PATH_SEPARATOR;

import java.util.ArrayList;
import java.util.Enumeration;
import java.util.LinkedList;
import java.util.List;
import java.util.stream.Collectors;

import javax.swing.tree.DefaultMutableTreeNode;
import javax.swing.tree.TreeNode;

import org.freeplane.core.resources.ResourceController;
import org.freeplane.core.resources.components.IPropertyControlCreator;
import org.freeplane.core.resources.components.OptionPanelBuilder;
import org.freeplane.core.util.HtmlUtils;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.mode.mindmapmode.MModeController;

public class PreferencesIndexer
{
    private static class StructurePathEntry {
        private final String identifier;
        private final String label;

        StructurePathEntry(String identifier, String label) {
            this.identifier = identifier;
            this.label = label != null ? label : identifier;
        }

        String getIdentifier() {
            return identifier;
        }

        String getLabel() {
            return label;
        }
    }

    private final List<StructurePathEntry> path;

    private final List<PreferencesItem> prefs;

    public PreferencesIndexer()
    {
    	prefs = new LinkedList<>();
    	path = new ArrayList<>(2);
        load();

        if(false)
            System.out.println(
                prefs.stream().map(x -> x.getDisplayedText()).collect(Collectors.joining("\n")));
    }

    public List<PreferencesItem> getPrefs()
    {
        return prefs;
    }

    private void load() {
    	final Controller controller = Controller.getCurrentController();
		MModeController modeController = (MModeController) controller.getModeController(MModeController.MODENAME);
		OptionPanelBuilder optionPanelBuilder = modeController.getOptionPanelBuilder();
		final DefaultMutableTreeNode node = optionPanelBuilder.getRoot();
		load(node, 0);
    }

	public void load(final TreeNode parent, int level) {
		@SuppressWarnings("unchecked")
		Enumeration<DefaultMutableTreeNode> children = (Enumeration<DefaultMutableTreeNode>) parent.children();
		while(children.hasMoreElements()) {
			final DefaultMutableTreeNode child = children.nextElement();
			final IPropertyControlCreator userObject = (IPropertyControlCreator)child.getUserObject();
			if(userObject != null) {
				final String propertyName = userObject.getPropertyName();
				final String translatedText = HtmlUtils.htmlToPlain(userObject.getTranslatedText());
				if(! propertyName.isEmpty()){
				    if(ResourceController.getResourceController().getBooleanProperty(propertyName + ".hide"))
	                    continue;
				    String tooltipText = HtmlUtils.htmlToPlain(userObject.getTranslatedTooltipText());
				    if(path.isEmpty())
				        continue;
				    StructurePathEntry currentTab = path.get(0);
				    String currentTabTranslated = currentTab.getLabel();
				    if(path.size() > 1) {
				    	StructurePathEntry currentSeparator = path.get(1);
				    	String currentSeparatorTranslated = currentSeparator.getLabel();
//				    	System.out.println(currentTabTranslated + ITEM_PATH_SEPARATOR + currentSeparatorTranslated + ITEM_PATH_SEPARATOR + translatedText);
				    	if(parent.getChildCount() < 20) {
				    		String prefPath = currentSeparatorTranslated + ITEM_PATH_SEPARATOR + translatedText;
				    		prefs.add(new PreferencesItem(currentTab.getIdentifier(), currentTabTranslated, propertyName, prefPath, tooltipText));
				    	}
				    	else {
				    		prefs.add(new PreferencesItem(currentTab.getIdentifier(), currentTabTranslated, propertyName, translatedText, tooltipText));
				    	}
				    }
				    else {
				    	prefs.add(new PreferencesItem(currentTab.getIdentifier(), currentTabTranslated, propertyName, translatedText, tooltipText));
				    }
				}
				else {
					final String structureIdentifier = userObject.getStructureIdentifier();
					path.add(new StructurePathEntry(structureIdentifier, translatedText));
				}
				if(level < 2) {
					load(child, level + 1);
				}
				if(propertyName.isEmpty() && !path.isEmpty()){
					path.remove(path.size() - 1);
				}
			}
			else {
				load(child, level);
			}
		}
	}
}

package org.freeplane.view.swing.map.outline;

import javax.swing.Action;
import javax.swing.AbstractAction;
import javax.swing.ActionMap;
import javax.swing.InputMap;
import javax.swing.JComponent;
import javax.swing.JPopupMenu;
import org.freeplane.core.ui.textchanger.TranslatedElementFactory;
import javax.swing.KeyStroke;
import java.awt.event.ActionEvent;

import org.freeplane.features.mode.Controller;
import org.freeplane.features.mode.mindmapmode.MModeController;

class OutlineActions {
    private final OutlineActionTargetProvider provider;
	private OutlineActionTarget controller() {
		return provider.getController();
	}

	private boolean isRightToLeft() {
		return OutlineGeometry.getInstance().isRightToLeft();
	}

    final Action navigateUp = new AbstractAction("Navigate Up") {
        @Override public void actionPerformed(ActionEvent e) { controller().navigateUp(); }

    };
    final Action navigateDown = new AbstractAction("Navigate Down") {
        @Override public void actionPerformed(ActionEvent e) { controller().navigateDown(); }
    };
    final Action navigatePageUp = new AbstractAction("Page Up") {
        @Override public void actionPerformed(ActionEvent e) { controller().navigatePageUp(); }
    };
    final Action navigatePageDown = new AbstractAction("Page Down") {
        @Override public void actionPerformed(ActionEvent e) { controller().navigatePageDown(); }
    };
    final Action goLeft = new AbstractAction("Go left") {
        @Override public void actionPerformed(ActionEvent e) {
        	if(isRightToLeft())
        		controller().expandOrGoToChild();
        	else
        		controller().collapseOrGoToParent();
        	}
    };
    final Action goRight = new AbstractAction("Go right") {
        @Override public void actionPerformed(ActionEvent e) {
        	if(isRightToLeft())
        		controller().collapseOrGoToParent();
        	else
        		controller().expandOrGoToChild();
        	}
    };
    final Action expandLeft = new AbstractAction("Expand left") {
        @Override public void actionPerformed(ActionEvent e) {
        	if(isRightToLeft())
        		controller().expandSelectedMore();
        	else
        		controller().reduceSelectedExpansion();
        	}
    };
    final Action expandRight = new AbstractAction("Expand right") {
    	@Override public void actionPerformed(ActionEvent e) {
    		if(isRightToLeft())
    			controller().reduceSelectedExpansion();
    		else
    			controller().expandSelectedMore();
    	}
    };
    final Action toggleExpand = new AbstractAction("Toggle Expand/Collapse") {
        @Override public void actionPerformed(ActionEvent e) { controller().toggleExpandSelected(); }
    };
    final Action selectInMap = new AbstractAction("Select in Map") {
        @Override public void actionPerformed(ActionEvent e) { controller().selectSelectedInMap(); }
    };
    final Action openPreferences = new AbstractAction("Preferences") {
        @Override public void actionPerformed(ActionEvent e) {
            final Controller controller = Controller.getCurrentController();
            final MModeController modeController = (MModeController) controller.getModeController(MModeController.MODENAME);
            modeController.showPreferences("Appearance", "outline_panel");
        }
    };

    OutlineActions(OutlineActionTargetProvider provider) {
        this.provider = provider;
        navigateUp.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("UP"));
        navigateDown.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("DOWN"));
        navigatePageUp.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("PAGE_UP"));
        navigatePageDown.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("PAGE_DOWN"));
        goLeft.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("LEFT"));
        goRight.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("RIGHT"));
        expandLeft.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("control LEFT"));
        expandRight.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("control RIGHT"));
        toggleExpand.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("SPACE"));
        selectInMap.putValue(Action.ACCELERATOR_KEY, KeyStroke.getKeyStroke("ENTER"));
    }

    void installOn(JComponent component, int condition) {
        InputMap inputMap = component.getInputMap(condition);
        ActionMap actionMap = component.getActionMap();

        inputMap.put(KeyStroke.getKeyStroke("UP"), "navigateUp");
        actionMap.put("navigateUp", navigateUp);

        inputMap.put(KeyStroke.getKeyStroke("DOWN"), "navigateDown");
        actionMap.put("navigateDown", navigateDown);

        inputMap.put(KeyStroke.getKeyStroke("PAGE_UP"), "navigatePageUp");
        actionMap.put("navigatePageUp", navigatePageUp);

        inputMap.put(KeyStroke.getKeyStroke("PAGE_DOWN"), "navigatePageDown");
        actionMap.put("navigatePageDown", navigatePageDown);

        inputMap.put(KeyStroke.getKeyStroke("LEFT"), "goParent");
        actionMap.put("goParent", goLeft);

        inputMap.put(KeyStroke.getKeyStroke("RIGHT"), "goChild");
        actionMap.put("goChild", goRight);

        inputMap.put(KeyStroke.getKeyStroke("control LEFT"), "reduceExpansion");
        actionMap.put("reduceExpansion", expandLeft);

        inputMap.put(KeyStroke.getKeyStroke("control RIGHT"), "expandMore");
        actionMap.put("expandMore", expandRight);
    }

    JPopupMenu buildMenuLocalized() {
        JPopupMenu menu = new JPopupMenu();
        menu.add(TranslatedElementFactory.createMenuItem(selectInMap, "outline.select.in.map"));
        menu.addSeparator();
        menu.add(TranslatedElementFactory.createMenuItem(navigateUp, "outline.navigate.up"));
        menu.add(TranslatedElementFactory.createMenuItem(navigateDown, "outline.navigate.down"));
        menu.add(TranslatedElementFactory.createMenuItem(navigatePageUp, "outline.page.up"));
        menu.add(TranslatedElementFactory.createMenuItem(navigatePageDown, "outline.page.down"));
        menu.addSeparator();
        menu.add(TranslatedElementFactory.createMenuItem(goLeft, "outline.go.parent"));
        menu.add(TranslatedElementFactory.createMenuItem(goRight, "outline.go.child"));
        menu.addSeparator();
        menu.add(TranslatedElementFactory.createMenuItem(expandRight, "outline.expand.more"));
        menu.add(TranslatedElementFactory.createMenuItem(expandLeft, "outline.reduce.expansion"));
        menu.add(TranslatedElementFactory.createMenuItem(toggleExpand, "outline.toggle.expand"));
        menu.addSeparator();
        menu.add(TranslatedElementFactory.createMenuItem(openPreferences, "preferences"));
        return menu;
    }
}

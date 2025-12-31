package org.freeplane.view.swing.map.outline;

import java.awt.ComponentOrientation;
import java.awt.Insets;
import java.awt.Point;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JPanel;

import org.freeplane.core.resources.ResourceController;

class NavigationButtons {
    final JButton expandMoreBtn;
    final JButton reduceBtn;

    private OutlineGeometry geometry;
    private final ExpansionControls expansionControls;
    private JPanel currentParent;
	private TreeNode node;
	private final OutlineDisplayMode displayMode;

    NavigationButtons(OutlineGeometry geometry, OutlineDisplayMode displayMode, ExpansionControls expansionControls) {
        this.geometry = geometry;
        this.expansionControls = expansionControls;
		this.displayMode = displayMode;

        expandMoreBtn = new JButton("▼");
        reduceBtn = new JButton("▲");

        configureNavigationButtons();
    }

    private void configureNavigationButtons() {
         configureNavButton(expandMoreBtn, e -> {
            expansionControls.expandNodeMore(node);
        });
        configureNavButton(reduceBtn, e -> {
            expansionControls.reduceNodeExpansion(node);
        });
    }

    private void configureNavButton(JButton button, ActionListener actionListener) {
        button.setMargin(new Insets(0, 0, 0, 0));
        applyButtonFont(button);
        button.setFocusable(false);
        button.setBorder(BorderFactory.createRaisedBevelBorder());
        button.setVisible(false);
        button.addActionListener(actionListener);
    }

    private void applyButtonFont(JButton button) {
        button.setFont(button.getFont().deriveFont(geometry.getItemFontSize()));
    }

    public void attachToNode(TreeNode node, JPanel targetPanel, int rowIndex, int rowIndent) {
        this.node = node;
        hideNavigationButtons();
		if (node.getChildren().isEmpty()) {
            return;
        }
		final boolean showFoldingButtons = ResourceController.getResourceController().getBooleanProperty("showOutlineFoldingButtons", true);
		if(showFoldingButtons) {

            targetPanel.add(expandMoreBtn);
            targetPanel.add(reduceBtn);

            currentParent = targetPanel;


        	Point position = calculateNavigationButtonPosition(rowIndex, rowIndent);
        	if (position == null) return;

        	int baseX = position.x;
        	int y = position.y;
        	int level = node.getLevel();
        	showButtons(baseX, y, level);
        	NavigationButtonHider.INSTANCE.enable(targetPanel, this);
        }
    }

    private Point calculateNavigationButtonPosition(int nodeIndex, int rowIndent) {
        final int baseX = geometry.calculateNavigationButtonX(rowIndent);
        final int rowHeight = geometry.rowHeight;
        int y = nodeIndex * rowHeight + 1;
		return new Point(baseX, y);
    }


    void hideNavigationButtons() {
        expandMoreBtn.setVisible(false);
        reduceBtn.setVisible(false);
        if (currentParent != null) {
            if (expandMoreBtn.getParent() == currentParent) {
                currentParent.remove(expandMoreBtn);
            }
            if (reduceBtn.getParent() == currentParent) {
                currentParent.remove(reduceBtn);
            }
        }
    }

    private void showButtons(int baseX, int y, int level) {
    	if(displayMode == OutlineDisplayMode.BOOKMARK)
    		return;
		final int buttonY = y + 2;
        final int buttonHeight = geometry.rowHeight - 4;

        int reduceX = baseX;
        int expandX = reduceX + geometry.navButtonWidth;
        expandMoreBtn.setBounds(expandX, buttonY, geometry.navButtonWidth, buttonHeight);
        RightToLeftLayout.applyToSingleComponent(expandMoreBtn);
        ComponentOrientation componentOrientation = geometry.outlineTextOrientation;
		expandMoreBtn.setComponentOrientation(componentOrientation);
        expandMoreBtn.setVisible(true);

        if(node.isExpanded() && (level > 0  || node.getMaxExpansionLevel() > 1) ) {
        	reduceBtn.setBounds(reduceX, buttonY, geometry.navButtonWidth, buttonHeight);
        	reduceBtn.setVisible(true);
        	reduceBtn.setComponentOrientation(componentOrientation);
        	RightToLeftLayout.applyToSingleComponent(reduceBtn);
        }
    }

    void updateGeometry(OutlineGeometry geometry) {
        this.geometry = geometry;
        applyButtonFont(expandMoreBtn);
        applyButtonFont(reduceBtn);
    }
}

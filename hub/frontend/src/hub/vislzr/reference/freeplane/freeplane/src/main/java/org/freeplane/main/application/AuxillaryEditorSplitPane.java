/*
 * Created on 19 Jul 2025
 *
 * author dimitry
 */
package org.freeplane.main.application;

import java.awt.Component;
import java.awt.KeyboardFocusManager;
import java.awt.LayoutManager;
import java.awt.LayoutManager2;
import java.awt.event.KeyEvent;

import javax.swing.JComponent;
import javax.swing.JSplitPane;
import javax.swing.KeyStroke;
import javax.swing.SwingUtilities;
import org.freeplane.core.resources.IFreeplanePropertyListener;
import org.freeplane.core.resources.ResourceController;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.ui.ViewController;

public class AuxillaryEditorSplitPane extends JSplitPane implements IFreeplanePropertyListener {
	private static final long serialVersionUID = 1L;
	private JComponent auxillaryComponent;
	private Component mainComponent;
	private boolean dividerLocationIsRestored;
	final private AuxiliarySplitPaneController controller;
	private String currentLocation;
	private AuxiliarySplitPanes manager;

	private String mode;

	// Optional binding to a visibility property (e.g., "outlineVisible")
	private String auxVisibilityBaseKey; // e.g., "outlineVisible"
	private boolean auxVisibilityBound;

	public AuxillaryEditorSplitPane(Component mainComponent, AuxiliarySplitPaneController controller) {
		this.controller = controller;
		this.mainComponent = mainComponent;
		this.currentLocation = controller.getLocation();
		if (JSplitPane.TOP.equals(currentLocation) || JSplitPane.LEFT.equals(currentLocation)) {
			setLeftComponent(null);
			setRightComponent(mainComponent);
		} else {
			setLeftComponent(mainComponent);
			setRightComponent(null);
		}
		dividerLocationIsRestored = false;
		setResizeWeight(0.5);
		setContinuousLayout(true);
		setOneTouchExpandable(false);
	}

	@Override
	protected boolean processKeyBinding(KeyStroke ks, KeyEvent e, int condition, boolean pressed){
		return false;
	}

	@Override
	public void setLayout(LayoutManager layout) {
		if(layout == null || layout instanceof SplitPaneLayoutManagerDecorator)
			super.setLayout(layout);
		else if(layout instanceof LayoutManager2)
			super.setLayout(new SplitPaneLayoutManager2Decorator((LayoutManager2) layout));
		else
			super.setLayout(new SplitPaneLayoutManagerDecorator(layout));
	}
	void insertComponentIntoSplitPane(final JComponent pAuxillaryComponent, String mode) {
		this.mode = mode;
		insertComponentIntoSplitPane(pAuxillaryComponent);
	}

	private void insertComponentIntoSplitPane(final JComponent pAuxillaryComponent) {
		Component focusOwner = KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner();
		this.currentLocation = controller.getLocation();
		if (JSplitPane.RIGHT.equals(currentLocation) || JSplitPane.LEFT.equals(currentLocation)) {
			if(getOrientation() != JSplitPane.HORIZONTAL_SPLIT) {
				setOrientation(JSplitPane.HORIZONTAL_SPLIT);
				dividerLocationIsRestored = false;
			}
		}
		else {
			if(getOrientation() != JSplitPane.VERTICAL_SPLIT) {
				setOrientation(JSplitPane.VERTICAL_SPLIT);
				dividerLocationIsRestored = false;
			}
		}
		if (JSplitPane.TOP.equals(currentLocation) || JSplitPane.LEFT.equals(currentLocation)) {
			if(getRightComponent() != mainComponent) {
				repositionComponent(mainComponent, JSplitPane.RIGHT);
			}
			if(getLeftComponent() != pAuxillaryComponent) {
				if(auxillaryComponent == pAuxillaryComponent)
					repositionComponent(auxillaryComponent, JSplitPane.LEFT);
				else {
					auxillaryComponent = pAuxillaryComponent;
					setLeftComponent(pAuxillaryComponent);
				}
			}
		}
		else {
			if(getLeftComponent() != mainComponent) {
				repositionComponent(mainComponent, JSplitPane.LEFT);
				dividerLocationIsRestored = false;
			}
			if(getRightComponent() != pAuxillaryComponent) {
				if(auxillaryComponent == pAuxillaryComponent)
					repositionComponent(auxillaryComponent, JSplitPane.RIGHT);
				else {
					auxillaryComponent = pAuxillaryComponent;
					setRightComponent(pAuxillaryComponent);
				}
				dividerLocationIsRestored = false;
			}
		}
		if(focusOwner != null && SwingUtilities.isDescendingFrom(focusOwner, this)) {
		    focusOwner.requestFocusInWindow();
		}
		revalidate();
		repaint();
		applyAuxVisibility();
	}

	private void repositionComponent(Component component, String constraints) {
		if(JSplitPane.RIGHT.equals(constraints)) {
			rightComponent = component;
			if(leftComponent == component)
				leftComponent = null;
		} else {
			leftComponent = component;
			if(rightComponent == component)
				rightComponent = null;
		}
		final LayoutManager layoutMgr = getLayout();
		if (layoutMgr != null) {
			layoutMgr.removeLayoutComponent(component);
		    if (layoutMgr instanceof LayoutManager2) {
		        ((LayoutManager2)layoutMgr).addLayoutComponent(component, constraints);
		    } else {
		        layoutMgr.addLayoutComponent(constraints, component);
		    }
		}
	}

	@Override
	protected void validateTree() {
		final boolean dividerLocationWasRestored = dividerLocationIsRestored;
		final int dividerLocation = getDividerLocation();
		dividerLocationIsRestored = false;
		super.validateTree();
		dividerLocationIsRestored = dividerLocationWasRestored && dividerLocation == getDividerLocation();
		restoreDividerLocation();
	}

	private void restoreDividerLocation() {
		if(dividerLocationIsRestored || auxillaryComponent == null)
			return;
		double lastSplitPanePosition = Double.NaN;
		if (JSplitPane.LEFT.equals(currentLocation) || JSplitPane.TOP.equals(currentLocation)) {
			lastSplitPanePosition = 1.0 - controller.getPosition(Double.NaN);
		}
		else {
			lastSplitPanePosition = controller.getPosition(Double.NaN);
		}

		if (Double.isNaN(lastSplitPanePosition)) {
			setDividerLocation(0.5);
		} else if(getProportionalDividerLocation() != lastSplitPanePosition) {
			setDividerLocation(lastSplitPanePosition);
		}
		dividerLocationIsRestored = true;
		invalidate();
		super.validateTree();
	}

	@Override
	public void setDividerLocation(int location) {
		super.setDividerLocation(location);
		if(dividerLocationIsRestored)
			saveSplitPanePosition();
	}

	private void saveSplitPanePosition() {
		double proportionalLocation = getProportionalDividerLocation();
		if ("left".equals(currentLocation) || "top".equals(currentLocation)) {
			controller.setPosition(1.0 - proportionalLocation);
		}
		else {
			controller.setPosition(proportionalLocation);
		}
	}

	public double getProportionalDividerLocation() {
		if (getOrientation() == VERTICAL_SPLIT) {
			int height = getHeight() - getDividerSize();
			return height > 0 ? (double) getDividerLocation() / height : 0.0;
		} else {
			int width = getWidth() - getDividerSize();
			return width > 0 ? (double) getDividerLocation() / width : 0.0;
		}
	}

	public void changeAuxComponentSide(String location) {
		if(location == null || location.equals(currentLocation))
			return;

		// Update the controller's location and save current location
		controller.setLocation(location);

		// Re-layout if we have both components
		if(getLeftComponent() != null && getRightComponent() != null){
			insertComponentIntoSplitPane(auxillaryComponent);
		}
	}

	public JComponent getAuxiliaryComponent() {
		return auxillaryComponent;
	}

	/**
	 * Sets the manager that created this split pane.
	 * This allows access back to the nested structure manager.
	 */
	void setManager(AuxiliarySplitPanes manager) {
		this.manager = manager;
	}

	/**
	 * Gets the manager that created this split pane.
	 * @return the manager or null if this was created directly
	 */
	public AuxiliarySplitPanes getManager() {
		return manager;
	}


	@Override
	public void remove(Component component) {
		if(component == auxillaryComponent)
			removeAuxiliaryComponent();
		else
			super.remove(component);
	}

	void removeAuxiliaryComponent() {
		if (auxillaryComponent != null) {
			super.remove(auxillaryComponent);
			auxillaryComponent = null;
			dividerLocationIsRestored = false;
			if (getLeftComponent() != mainComponent) {
				repositionComponent(mainComponent, JSplitPane.LEFT);
				setRightComponent(null);
			}
		}
	}

	public void moveAuxillaryComponentTo(AuxillaryEditorSplitPane toSplitPane, String targetMode) {
		if (auxillaryComponent != null) {
			final boolean isModeSame = targetMode.equals(mode);
			if(isModeSame)
				toSplitPane.insertComponentIntoSplitPane(auxillaryComponent, mode);
			else
				removeAuxiliaryComponent();
		}
	}

	// --- Property binding for auxiliary component visibility ---
	public void bindAuxiliaryVisibilityToProperty(String baseKey) {
		this.auxVisibilityBaseKey = baseKey; // expects keys baseKey and baseKey+".fullscreen"
	}

	private void applyAuxVisibility() {
		if (auxVisibilityBaseKey == null) return;
		boolean fs = false;
		try {
			ViewController vc = Controller.getCurrentController().getViewController();
			fs = vc != null && vc.isFullScreenEnabled();
		} catch (Exception ignore) { }
		String key = auxVisibilityBaseKey + (fs ? ".fullscreen" : "");
		boolean visible = ResourceController.getResourceController().getBooleanProperty(key);
		if (auxillaryComponent != null) {
			auxillaryComponent.setVisible(visible);
			revalidate();
			repaint();
		}
	}

	@Override
	public void propertyChanged(String propertyName, String newValue, String oldValue) {
		if (auxVisibilityBaseKey == null) return;
		if (propertyName.equals(auxVisibilityBaseKey)
				|| propertyName.equals(auxVisibilityBaseKey + ".fullscreen")
				|| ViewController.FULLSCREEN_ENABLED_PROPERTY.equals(propertyName)) {
			applyAuxVisibility();
		}
	}

	@Override
	public void addNotify() {
		super.addNotify();
		if (auxVisibilityBaseKey != null && !auxVisibilityBound) {
			ResourceController.getResourceController().addPropertyChangeListener(this);
			auxVisibilityBound = true;
		}
		applyAuxVisibility();
	}

	@Override
	public void removeNotify() {
		super.removeNotify();
		if (auxVisibilityBaseKey != null && auxVisibilityBound) {
			ResourceController.getResourceController().removePropertyChangeListener(this);
			auxVisibilityBound = false;
		}
	}

	@Override
	public void setBounds(int x, int y, int width, int height) {
		dividerLocationIsRestored = false;
		super.setBounds(x, y, width, height);
	}


}

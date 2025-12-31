package org.freeplane.view.swing.map.outline;

import java.awt.Component;
import java.awt.Container;

class RightToLeftLayout {
	private RightToLeftLayout() {
	}

	static void onContainerWidthChange(Container container, int oldWidth, int newWidth) {
		if (oldWidth == newWidth || !isRightToLeft()) {
			return;
		}

		int deltaX = newWidth - oldWidth;
		for (Component childComponent : container.getComponents()) {
			childComponent.setLocation(childComponent.getX() + deltaX, childComponent.getY());
		}
	}

	static void applyToContainer(Container container) {
		if (!isRightToLeft()) {
			return;
		}
		int rightX = container.getWidth();

		for (Component childComponent : container.getComponents()) {
			int newXCoordinate = rightX - childComponent.getX() - childComponent.getWidth();
			childComponent.setLocation(newXCoordinate, childComponent.getY());
		}
	}

	static void applyToSingleComponent(Component invertedComponent) {
		if (! isRightToLeft()) {
			return;
		}
		Container container = invertedComponent.getParent();
		int mirroredX = container.getWidth() - invertedComponent.getX() - invertedComponent.getWidth();
		invertedComponent.setLocation(mirroredX, invertedComponent.getY());
	}
	private static boolean isRightToLeft() {
		return OutlineGeometry.getInstance().isRightToLeft();
	}

}

/*
 *  Freeplane - mind map editor
 *  Copyright (C) 2009 Dimitry
 *
 *  This file author is Dimitry
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
package org.freeplane.view.swing.map.link;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Point;
import java.awt.Polygon;
import java.awt.Rectangle;
import java.util.LinkedList;
import java.util.List;

import org.freeplane.core.util.ColorUtils;
import org.freeplane.features.link.ArrowType;
import org.freeplane.features.link.ConnectorModel;
import org.freeplane.features.link.ConnectorShape;
import org.freeplane.features.link.LinkController;
import org.freeplane.features.mode.ModeController;
import org.freeplane.features.styles.MapViewLayout;
import org.freeplane.view.swing.map.MapView;
import org.freeplane.view.swing.map.NodeView;
import org.freeplane.view.swing.map.edge.EdgeView;
import org.freeplane.view.swing.map.edge.EdgeViewFactory;

/**
 * @author Dimitry Polivaev
 * 09.08.2009
 */
public class EdgeLinkView extends AConnectorView {
	private final EdgeView edgeView;
	private final List<Polygon> arrows;
	private LinkController linkController;

	public EdgeLinkView(final ConnectorModel model, final ModeController modeController, final NodeView source,
	                    final NodeView target) {
		super(model, source, target);
		final MapView map = source.getMap();
		if (map.getLayoutType() == MapViewLayout.OUTLINE) {
			edgeView = new OutlineLinkView(source, target, map);
		}
		else{
			edgeView = EdgeViewFactory.getInstance().getEdge(source, target, map, false);
		}
		Color color;
		linkController = LinkController.getController(modeController);
		if (ConnectorShape.EDGE_LIKE.equals(linkController.getShape(model))) {
			color = edgeView.getColor().darker();
		}
		else {
			color = linkController.getColor(viewedConnector);
			final int alpha = linkController.getOpacity(viewedConnector);
			color =  ColorUtils.alphaToColor(alpha, color);
			final int width = linkController.getWidth(model);
			edgeView.setWidth(width);
			int[] dash = linkController.getDashArray(model);
			edgeView.setDash(dash);
		}
		edgeView.setColor(color);
		arrows = new LinkedList<>();
	}

	@Override
	public boolean detectCollision(final Point p, final boolean selectedOnly) {
		if (selectedOnly) {
			final NodeView source = edgeView.getSource();
			if ((source == null || !source.isSelected())) {
				final NodeView target = edgeView.getTarget();
				if ((target == null || !target.isSelected())) {
					return false;
				}
			}
		}
		if (edgeView.detectCollision(p))
			return true;
		CollisionDetector collisionDetector = new CollisionDetector();
		return arrows.stream().anyMatch(shape -> collisionDetector.detectCollision(p, shape));

	}

	@Override
	public ConnectorModel getConnector() {
		return viewedConnector;
	}

	@Override
	public void increaseBounds(final Rectangle innerBounds) {
		//edge link does not increase inner bounds
	}

	@Override
	public void paint(final Graphics graphics) {
		arrows.clear();
		edgeView.paint((Graphics2D) graphics);
		if(ConnectorShape.EDGE_LIKE.equals(linkController.getShape(viewedConnector))){
			return;
		}
		if (isSourceVisible() && !linkController.getArrows(viewedConnector).start.equals(ArrowType.NONE)) {
			Point p1 = edgeView.getShapeStart();
			Point p2 = new Point(p1);
			p2.translate(5, 0);
			paintArrow(graphics, p2, p1);
		}
		if (isTargetVisible() && !linkController.getArrows(viewedConnector).end.equals(ArrowType.NONE)) {
			Point p1 = edgeView.getEnd();
			Point p2 = new Point(p1);
			p2.translate(5, 0);
			paintArrow(graphics, p2, p1);
		}

	}

	private void paintArrow(final Graphics graphics, Point from, Point to) {
	    Polygon arrow = paintArrow(from, to, (Graphics2D)graphics, getZoom() * 10, ArrowDirection.INCOMING);
	    if(arrow != null)
	    	arrows.add(arrow);
    }
}

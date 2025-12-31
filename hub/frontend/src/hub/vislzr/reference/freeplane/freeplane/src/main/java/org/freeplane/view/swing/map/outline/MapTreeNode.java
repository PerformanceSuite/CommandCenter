
package org.freeplane.view.swing.map.outline;

import java.awt.Color;
import java.awt.ComponentOrientation;
import java.awt.FontMetrics;

import javax.swing.Icon;
import javax.swing.JComponent;
import javax.swing.SwingUtilities;

import org.freeplane.core.ui.components.DoubleTextIcon;
import org.freeplane.core.ui.components.StyledIcon;
import org.freeplane.core.ui.components.TextIcon;
import org.freeplane.core.ui.components.TextIcon.BorderType;
import org.freeplane.core.ui.components.UITools;
import org.freeplane.core.util.ColorUtils;
import org.freeplane.core.util.ObjectRule;
import org.freeplane.features.edge.EdgeController;
import org.freeplane.features.map.INodeView;
import org.freeplane.features.map.NodeChangeEvent;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.mode.ModeController;
import org.freeplane.features.nodestyle.NodeStyleController;
import org.freeplane.features.styles.LogicalStyleController.StyleOption;
import org.freeplane.features.text.TextController;
import org.freeplane.view.swing.map.MapView;
import org.freeplane.view.swing.map.NodeView;
import org.freeplane.view.swing.map.edge.AutomaticEdgeStyle;
import org.freeplane.view.swing.map.edge.EdgeColorContext;

/**
 * TreeNode that wraps a NodeModel and implements INodeView to receive
 * live updates when the underlying node changes.
 */
class MapTreeNode extends TreeNode implements INodeView, EdgeColorContext {

    private final NodeModel nodeModel;
    private final OutlinePane outlinePane;
	private final NodeStyleController styleController;
	private final Color mapBackground;

    MapTreeNode(NodeModel nodeModel, OutlinePane outlinePane, NodeStyleController styleController, Color mapBackground) {
        super(nodeModel.createID(), null);
        this.nodeModel = nodeModel;
        this.outlinePane = outlinePane;
		this.styleController = styleController;
		this.mapBackground = mapBackground;
        setTitleSupplier(this::getNodeText);
    }

    public MapTreeNode(MapTreeNode parent, NodeModel child) {
    	this(child, parent.outlinePane, parent.styleController, parent.mapBackground);
    	parent.addChild(this);
	}

    MapTreeNode createNode(NodeModel node) {
    	return new MapTreeNode(node, outlinePane, styleController, mapBackground);
    }
	NodeModel getNodeModel() {
        return nodeModel;
    }

    private String getNodeText() {
        String shortPlainText = TextController.getController().getShortPlainText(nodeModel).trim();
		return shortPlainText.isEmpty() ? "--" : shortPlainText;
    }

    @Override
    public void nodeChanged(NodeChangeEvent event) {
    	if (event.getNode() == nodeModel) {
    		update();
    		SwingUtilities.invokeLater(() -> {
    			outlinePane.updateNodeTitleLater(this);
    		});
    	}
    }

    @Override
	public
    boolean hasStandardLayoutWithRootNode(NodeModel root) {
        return false;
    }

    @Override
	public
    boolean isTopOrLeft() {
        return true;
    }

    /**
     * Recursively cleanup all INodeView listeners for this node and its children.
     * Called when the tree is being destroyed or replaced.
     */
    void cleanupListeners() {

        if (nodeModel != null) {
            nodeModel.removeViewer(this);
        }


        for (TreeNode child : getChildren()) {
            if (child instanceof MapTreeNode) {
                ((MapTreeNode) child).cleanupListeners();
            }
        }
    }

    boolean isContainedIn(MapAwareOutlinePane pane) {
    	return pane== outlinePane;
    }

	public Icon createIcon(JComponent component, boolean usesColoredOutlineItems, boolean showsFoldingStatus) {
		String text = getTitle();
		FontMetrics fontMetrics = component.getFontMetrics(component.getFont());
		final StyledIcon icon;
		if(showsFoldingStatus && nodeModel.hasChildren()) {
			String childrenHint;
			ComponentOrientation componentOrientation = component.getComponentOrientation();
			if(componentOrientation.isHorizontal() && ! componentOrientation.isLeftToRight()) {
				childrenHint = isExpanded() ? "- " : "+ ";
			}
			else {
				childrenHint = isExpanded() ? " -" : " +";
			}

			DoubleTextIcon doubleTextIcon = new DoubleTextIcon(childrenHint, text, fontMetrics);
			doubleTextIcon.setUnderlinePosition(DoubleTextIcon.UnderlinePosition.RIGHT);
			icon = doubleTextIcon;
		}
		else {
			TextIcon textIcon = new TextIcon(text, fontMetrics);
			textIcon.setBorderType(BorderType.UNDERLINE);
			icon = textIcon;
		}
		icon.setPaddingX((int) (3 * UITools.FONT_SCALE_FACTOR));
		icon.setBorderStroke(TextIcon.DEFAULT_STROKE);
		if(usesColoredOutlineItems) {
			Color color = styleController.getColor(nodeModel, StyleOption.FOR_UNSELECTED_NODE);
			Color backgroundColor = styleController.getBackgroundColor(nodeModel, StyleOption.FOR_UNSELECTED_NODE);
			if (backgroundColor != null) {
				if (backgroundColor.getAlpha() < 255) {
					backgroundColor = ColorUtils.blendColors(backgroundColor, mapBackground);
				}
			}
			else
				backgroundColor = mapBackground;
			icon.setIconTextColor(color);
			icon.setIconBackgroundColor(backgroundColor);
			if(icon.getBorderStroke() != null)
				icon.setIconBorderColor(determineBorderColor());
		}
		return icon;
	}

	private Color determineBorderColor() {
		Boolean matches = styleController.getBorderColorMatchesEdgeColor(nodeModel, StyleOption.FOR_UNSELECTED_NODE);
		boolean borderMatchesEdgeColor = matches != null && matches.booleanValue();
		if (!borderMatchesEdgeColor) {
			Color explicitBorderColor = styleController.getBorderColor(nodeModel, StyleOption.FOR_UNSELECTED_NODE);
			return explicitBorderColor != null ? explicitBorderColor : EdgeController.STANDARD_EDGE_COLOR;
		}
		return resolveEdgeColor();
	}

	private Color resolveEdgeColor() {
		ModeController modeController = styleController.getModeController();
		if (modeController == null)
			return EdgeController.STANDARD_EDGE_COLOR;
		EdgeController edgeController = modeController.getExtension(EdgeController.class);
		if (edgeController == null)
			return EdgeController.STANDARD_EDGE_COLOR;
		ObjectRule<Color, EdgeController.Rules> colorRule = edgeController.getColorRule(nodeModel, StyleOption.FOR_UNSELECTED_NODE);
		AutomaticEdgeStyle edgeStyle = new AutomaticEdgeStyle(modeController, nodeModel.getMap(), this);
		return edgeStyle.resolve(colorRule);
	}

	private MapView findMapView() {
		if (outlinePane instanceof MapAwareOutlinePane)
			return ((MapAwareOutlinePane) outlinePane).getCurrentMapView();
		return null;
	}

	private NodeView findNodeView() {
		return findNodeView(nodeModel);
	}

	private NodeView findNodeView(NodeModel node) {
		MapView mapView = findMapView();
		if (mapView == null || node == null)
			return null;
		return mapView.getNodeView(node);
	}

	@Override
	public int computeColumnPaletteIndex() {
		NodeView nodeView = findNodeView();
		if (nodeView != null)
			return nodeView.computeColumnPaletteIndex();
		return getLevel();
	}

	@Override
	public int computeBranchPaletteIndex() {
		NodeView nodeView = findNodeView();
		if (nodeView != null)
			return nodeView.computeBranchPaletteIndex();
		NodeModel parentNode = nodeModel.getParentNode();
		if (parentNode == null || ! parentNode.isRoot())
			return 0;
		return parentNode.getIndex(nodeModel) + 1;
	}

	@Override
	public int computeLevelPaletteIndex() {
		NodeView nodeView = findNodeView();
		if (nodeView != null)
			return nodeView.computeLevelPaletteIndex();
		MapView mapView = findMapView();
		int baseLevel = mapView != null ? nodeModel.getNodeLevel(mapView.getFilter()) : nodeModel.getNodeLevel();
		return baseLevel + (nodeModel.isHiddenSummary() ? 1 : 0);
	}

	@Override
	public Color getParentEdgeColor() {
		NodeView nodeView = findNodeView();
		if (nodeView != null)
			return nodeView.getParentEdgeColor();
		NodeModel parentNode = nodeModel.getParentNode();
		if (parentNode == null)
			return null;
		NodeView parentView = findNodeView(parentNode);
		if (parentView != null)
			return parentView.getEdgeColor();
		TreeNode parentTreeNode = getParent();
		if (parentTreeNode instanceof MapTreeNode)
			return ((MapTreeNode) parentTreeNode).resolveEdgeColor();
		return null;
	}

}

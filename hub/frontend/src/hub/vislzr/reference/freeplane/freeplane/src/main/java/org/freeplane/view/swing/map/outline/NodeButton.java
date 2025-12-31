package org.freeplane.view.swing.map.outline;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Component;
import java.awt.ComponentOrientation;
import java.awt.Container;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Toolkit;
import java.awt.dnd.DnDConstants;
import java.awt.dnd.DragSource;
import java.awt.dnd.DropTarget;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.awt.event.KeyEvent;
import java.awt.event.MouseEvent;
import java.awt.Insets;
import java.awt.Rectangle;
import java.util.Collections;

import javax.swing.AbstractAction;
import javax.swing.AbstractButton;
import javax.swing.Action;
import javax.swing.BorderFactory;
import javax.swing.Icon;
import javax.swing.JButton;
import javax.swing.JMenuItem;
import javax.swing.JPopupMenu;
import javax.swing.KeyStroke;
import javax.swing.SwingConstants;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;
import javax.swing.plaf.ButtonUI;
import javax.swing.plaf.UIResource;
import javax.swing.plaf.basic.BasicButtonUI;

import org.freeplane.core.ui.AntiAliasingConfigurator;
import org.freeplane.core.ui.components.DoubleTextIcon;
import org.freeplane.core.ui.components.TextIcon;
import org.freeplane.core.ui.textchanger.TranslatedElementFactory;
import org.freeplane.features.bookmarks.mindmapmode.NodeNavigator;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.map.NodeModel.Side;
import org.freeplane.features.map.clipboard.MapClipboardController;
import org.freeplane.features.map.clipboard.MapClipboardController.CopiedNodeSet;
import org.freeplane.features.map.clipboard.MindMapNodesSelection;
import org.freeplane.features.map.mindmapmode.clipboard.MMapClipboardController;
import org.freeplane.view.swing.ui.NodeDropUtils;

class NodeButton extends JButton {
    private static final long serialVersionUID = 1L;
    private static final String COPY_ACTION_KEY = "outlineCopy";
    private static final String PASTE_ACTION_KEY = "outlinePaste";
    private static final int MENU_SHORTCUT_MASK = Toolkit.getDefaultToolkit().getMenuShortcutKeyMask();
    private static final KeyStroke COPY_KEY_STROKE = KeyStroke.getKeyStroke(KeyEvent.VK_C, MENU_SHORTCUT_MASK);
    private static final KeyStroke PASTE_KEY_STROKE = KeyStroke.getKeyStroke(KeyEvent.VK_V, MENU_SHORTCUT_MASK);
	private static final FocusListener repaint = new FocusListener() {

		@Override
		public void focusLost(FocusEvent e) {
			repaintParent(e.getComponent());
		}

		@Override
		public void focusGained(FocusEvent e) {
			repaintParent(e.getComponent());
		}

		private void repaintParent(final Component component) {
			final Container parent = component.getParent();
			if(parent != null)
				parent.repaint(0, component.getY() - 3, parent.getWidth(), component.getHeight() + 6);
		}
	};
	private static final ButtonUI nodeButtonUI = new BasicButtonUI() {
		@Override
		protected void installDefaults(AbstractButton b) {
	        String pp = getPropertyPrefix();
	        Font f = b.getFont();
	        if (f == null || f instanceof UIResource) {
	        	String defaultFontName = pp + "font";
				b.setFont(UIManager.getFont(defaultFontName));
	        }
	        b.setBorder(BorderFactory.createEmptyBorder(0, 2, 0, 2));
	        b.setOpaque(false);
	        b.addFocusListener(repaint);
		}

	};

    private final TreeNode node;
    private boolean dropFeedbackVisible;
	private final boolean usesColoredOutlineItems;
	private final boolean showsFoldingStatus;

    NodeButton(TreeNode node, boolean usesColoredOutlineItems, ComponentOrientation componentOrientation) {
    	this(node, usesColoredOutlineItems, true, Font.PLAIN, componentOrientation);
    }

    NodeButton(TreeNode node, boolean usesColoredOutlineItems, boolean showsFoldingStatus, int fontStyle, ComponentOrientation componentOrientation) {
        super();
        this.node = node;
		this.usesColoredOutlineItems = usesColoredOutlineItems;
		this.showsFoldingStatus = showsFoldingStatus;
        final float itemFontSize = OutlineGeometry.getInstance().getItemFontSize();
        final Font font = getFont().deriveFont(fontStyle, itemFontSize);
        setFont(font);
        setHorizontalAlignment(SwingConstants.LEADING);
        updateLabel();
        installNodePopupMenu();
        installDragAndDrop();
        installClipboardActions();
		setComponentOrientation(componentOrientation);
    }

	@Override
	public void updateUI() {
    	setUI(nodeButtonUI);
	}



	TreeNode getNode() {
        return node;
    }

    NodeModel getNodeModel() {
        if (node instanceof MapTreeNode) {
            return ((MapTreeNode) node).getNodeModel();
        }
        return null;
    }

    private void installNodePopupMenu() {
        if (!(node instanceof MapTreeNode)) {
            return;
        }
        MapTreeNode mapTreeNode = (MapTreeNode) node;
        NodeModel nodeModel = mapTreeNode.getNodeModel();
        if (nodeModel == null) {
            return;
        }
        NodeNavigator nodeNavigator = new NodeNavigator(nodeModel);

        JPopupMenu popupMenu = new JPopupMenu();
        addGotoNodeMenuItem(popupMenu, nodeNavigator);
        addOpenAsRootDirectMenuItem(popupMenu, nodeNavigator);
        addOpenAsNewViewRootMenuItem(popupMenu, nodeNavigator);
        popupMenu.addSeparator();
        addCopyMenuItem(popupMenu);
        addPasteMenuItem(popupMenu);
        setComponentPopupMenu(popupMenu);
    }

    private void addGotoNodeMenuItem(JPopupMenu popupMenu, NodeNavigator nodeNavigator) {
        JMenuItem menuItem = TranslatedElementFactory.createMenuItem("bookmark.goto_node");
        menuItem.addActionListener(actionEvent -> nodeNavigator.open(false));
        popupMenu.add(menuItem);
    }

    private void addOpenAsRootDirectMenuItem(JPopupMenu popupMenu, NodeNavigator nodeNavigator) {
        JMenuItem menuItem = TranslatedElementFactory.createMenuItem("bookmark.open_as_root");
        menuItem.addActionListener(actionEvent -> nodeNavigator.open(true));
        popupMenu.add(menuItem);
    }

    private void addOpenAsNewViewRootMenuItem(JPopupMenu popupMenu, NodeNavigator nodeNavigator) {
        JMenuItem menuItem = TranslatedElementFactory.createMenuItem("bookmark.open_as_new_view_root");
        menuItem.addActionListener(actionEvent -> nodeNavigator.openAsNewView());
        popupMenu.add(menuItem);
    }

    private void addCopyMenuItem(JPopupMenu popupMenu) {
        JMenuItem copyMenuItem = TranslatedElementFactory.createMenuItem("menu_copy");
        copyMenuItem.addActionListener(actionEvent -> performCopyAction());
        popupMenu.add(copyMenuItem);
    }

    private void addPasteMenuItem(JPopupMenu popupMenu) {
        JMenuItem pasteMenuItem = TranslatedElementFactory.createMenuItem("simplyhtml.pasteLabel");
        pasteMenuItem.addActionListener(actionEvent -> performPasteAction());
        popupMenu.add(pasteMenuItem);
    }

    private void installDragAndDrop() {
        if (!(node instanceof MapTreeNode)) {
            return;
        }
        DragSource dragSource = DragSource.getDefaultDragSource();
        dragSource.createDefaultDragGestureRecognizer(this,
                DnDConstants.ACTION_COPY | DnDConstants.ACTION_MOVE | DnDConstants.ACTION_LINK,
                new OutlineNodeDragGestureListener(this));

        @SuppressWarnings("unused")
		DropTarget dropTarget = new DropTarget(this,
                DnDConstants.ACTION_COPY | DnDConstants.ACTION_MOVE | DnDConstants.ACTION_LINK,
                new OutlineNodeDropTargetListener());
    }

    void showDropFeedback() {
        if (!dropFeedbackVisible) {
            dropFeedbackVisible = true;
            repaint();
        }
    }

    void clearDropFeedback() {
        if (dropFeedbackVisible) {
            dropFeedbackVisible = false;
            repaint();
        }
    }

    private void installClipboardActions() {
        if (!(node instanceof MapTreeNode)) {
            return;
        }

        Action copyAction = new AbstractAction() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent actionEvent) {
                performCopyAction();
            }
        };

        Action pasteAction = new AbstractAction() {
            @Override
            public void actionPerformed(java.awt.event.ActionEvent actionEvent) {
                performPasteAction();
            }
        };

        getInputMap(WHEN_FOCUSED).put(COPY_KEY_STROKE, COPY_ACTION_KEY);
        getActionMap().put(COPY_ACTION_KEY, copyAction);

        getInputMap(WHEN_FOCUSED).put(PASTE_KEY_STROKE, PASTE_ACTION_KEY);
        getActionMap().put(PASTE_ACTION_KEY, pasteAction);
    }

    private void performCopyAction() {
        NodeModel nodeModel = getNodeModel();
        if (nodeModel == null) {
            return;
        }

        MapClipboardController clipboardController = MapClipboardController.getController();
        MindMapNodesSelection selection = clipboardController.copy(Collections.singletonList(nodeModel),
                CopiedNodeSet.ALL_NODES,
                CopiedNodeSet.ALL_NODES);

        if (selection == null) {
            return;
        }

        selection.setDropAction(DnDConstants.ACTION_COPY);
        selection.setNodeObjects(Collections.singletonList(nodeModel), false);
        clipboardController.setClipboardContents(selection);
    }

    private void performPasteAction() {
        NodeModel nodeModel = getNodeModel();
        if (nodeModel == null) {
            return;
        }

        MapClipboardController clipboardController = MapClipboardController.getController();
        if (!(clipboardController instanceof MMapClipboardController)) {
            return;
        }

        MMapClipboardController mapClipboardController = (MMapClipboardController) clipboardController;
        java.awt.datatransfer.Transferable clipboardContents = mapClipboardController.getClipboardContents();
        if (clipboardContents == null) {
            return;
        }

        int dropAction = NodeDropUtils.getDropAction(clipboardContents, DnDConstants.ACTION_COPY);
        mapClipboardController.paste(clipboardContents, nodeModel, Side.DEFAULT, dropAction);
    }

    @Override
    protected void paintComponent(Graphics graphics) {
    	Icon icon = getIcon();
		if(icon != null) {
    		Graphics2D g2 = (Graphics2D)graphics.create();
            AntiAliasingConfigurator.setAntialiasing(g2);
            if(!usesColoredOutlineItems && icon instanceof TextIcon) {
            	TextIcon textIcon = (TextIcon) icon;
            	Color foreground = getForeground();
            	textIcon.setIconTextColor(foreground);
            	if(textIcon.getBorderStroke() != null)
            		textIcon.setIconBorderColor(foreground);
            }
            super.paintComponent(g2);
            g2.dispose();

    	}
    	else
    		super.paintComponent(graphics);
        if (dropFeedbackVisible) {
        	paintDropFeedback(graphics);
        }
    }

	private void paintDropFeedback(Graphics graphics) {
		Graphics2D graphics2D = (Graphics2D) graphics.create();
        try {
            graphics2D.setColor(getForeground());
            graphics2D.setStroke(new BasicStroke(2f));
            int height = getHeight() - 4;
            int y = 2;
            graphics2D.drawLine(2, y, 2, y + height);
            graphics2D.drawLine(getWidth() - 3, y, getWidth() - 3, y + height);
        }
        finally {
            graphics2D.dispose();
        }
	}

	void updateLabel() {
		if(node instanceof MapTreeNode) {
			setIcon(((MapTreeNode)node).createIcon(this, usesColoredOutlineItems, showsFoldingStatus));
		}
		else {
			String buttonText = node.getTitle();
			setText(buttonText);
		}
	}

    boolean isFirstIconClick(MouseEvent event) {
        if(event == null || event.getSource() != this) {
            return false;
        }
        Icon icon = getIcon();
        if(!(icon instanceof DoubleTextIcon)) {
            return false;
        }
        Rectangle iconArea = calculateIconRect(icon);
        if(iconArea == null || !iconArea.contains(event.getX(), event.getY())) {
            return false;
        }
        int relativeX = event.getX() - iconArea.x;
        int rightIconX = ((DoubleTextIcon) icon).getRightIconX(this);
        ComponentOrientation componentOrientation = getComponentOrientation();
		if(componentOrientation.isHorizontal() && ! componentOrientation.isLeftToRight())
			return relativeX > rightIconX;
		else
			return relativeX < rightIconX;
    }

    private Rectangle calculateIconRect(Icon icon) {
        if(icon == null) {
            return null;
        }
        Rectangle iconRect = new Rectangle();
        Rectangle textRect = new Rectangle();
        Rectangle viewRect = new Rectangle();
        Insets insets = getInsets();
        viewRect.x = insets.left;
        viewRect.y = insets.top;
        viewRect.width = getWidth() - (insets.left + insets.right);
        viewRect.height = getHeight() - (insets.top + insets.bottom);
        SwingUtilities.layoutCompoundLabel(
            this,
            getFontMetrics(getFont()),
            getText(),
            icon,
            getVerticalAlignment(),
            getHorizontalAlignment(),
            getVerticalTextPosition(),
            getHorizontalTextPosition(),
            viewRect,
            iconRect,
            textRect,
            getIconTextGap()
        );
        return iconRect.width > 0 ? iconRect : null;
    }
}

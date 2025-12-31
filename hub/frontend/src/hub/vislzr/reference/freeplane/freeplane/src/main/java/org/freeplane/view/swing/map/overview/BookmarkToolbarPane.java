package org.freeplane.view.swing.map.overview;

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Window;

import javax.swing.JComponent;
import javax.swing.SwingUtilities;

import org.freeplane.core.resources.IFreeplanePropertyListener;
import org.freeplane.core.resources.ResourceController;
import org.freeplane.features.bookmarks.mindmapmode.BookmarksController;
import org.freeplane.features.bookmarks.mindmapmode.MapBookmarks;
import org.freeplane.features.bookmarks.mindmapmode.ui.BookmarkToolbar;
import org.freeplane.features.filter.Filter;
import org.freeplane.features.map.IMapChangeListener;
import org.freeplane.features.map.INodeSelectionListener;
import org.freeplane.features.map.MapChangeEvent;
import org.freeplane.features.map.MapModel;
import org.freeplane.features.map.NodeDeletionEvent;
import org.freeplane.features.map.NodeModel;
import org.freeplane.features.mode.Controller;
import org.freeplane.features.mode.mindmapmode.MModeController;
import org.freeplane.features.ui.IMapViewChangeListener;
import org.freeplane.features.ui.IMapViewManager;
import org.freeplane.features.ui.ViewController;
import org.freeplane.view.swing.map.MapView;


public class BookmarkToolbarPane extends JComponent implements IMapViewChangeListener, IFreeplanePropertyListener, IMapChangeListener, INodeSelectionListener {
    private static final long serialVersionUID = 1L;

    private final static String BOOKMARKS_TOOLBAR_VISIBLE_PROPERTY = "bookmarksToolbarVisible";
    private final static String BOOKMARKS_TOOLBAR_VISIBLE_FS_PROPERTY = "bookmarksToolbarVisible.fullscreen";

    private final Component rootWindow;
    private BookmarkToolbar bookmarksToolbar;
    private boolean isBookmarksToolbarVisible;
    private MapView currentSelectedMapView;
    private MapModel currentMap;
    private boolean bookmarksUpdateScheduled;

    public BookmarkToolbarPane(Component rootWindow) {
        this.rootWindow = rootWindow;
        setLayout(new BorderLayout(0, 0));

        final ViewController viewController = Controller.getCurrentController().getViewController();
        isBookmarksToolbarVisible = viewController.isBookmarksToolbarVisible();

        add(rootWindow, BorderLayout.CENTER);

        Controller.getCurrentController().getMapViewManager().addMapViewChangeListener(this);
        ResourceController.getResourceController().addPropertyChangeListener(this);


        refreshToolbarForContainedMapViews();
    }

    @Override
    public void afterViewChange(Component oldView, Component newView) {  }

    @Override
    public void afterViewClose(Component oldView) {  }

    @Override
    public void afterViewCreated(Component newView) {  }

    @Override
    public void propertyChanged(String propertyName, String newValue, String oldValue) {
        if (ViewController.FULLSCREEN_ENABLED_PROPERTY.equals(propertyName)
                || BOOKMARKS_TOOLBAR_VISIBLE_PROPERTY.equals(propertyName)
                || BOOKMARKS_TOOLBAR_VISIBLE_FS_PROPERTY.equals(propertyName)) {
            final ViewController viewController = Controller.getCurrentController().getViewController();
            if (isBookmarksToolbarVisible != viewController.isBookmarksToolbarVisible()) {
                isBookmarksToolbarVisible = !isBookmarksToolbarVisible;
                if (bookmarksToolbar != null) {
                    bookmarksToolbar.setVisible(isBookmarksToolbarVisible);
                }
                refreshToolbarLater();
            }
        }
    }


    private boolean isMindMapEditor(MapView mapView) {
        return mapView.getModeController().getModeName().equals(MModeController.MODENAME);
    }

    private void refreshToolbarForContainedMapViews() {
        final IMapViewManager mapViewManager = Controller.getCurrentController().getMapViewManager();
        MapView mapViewToUse = (MapView) mapViewManager.getLastSelectedMapViewContainedIn(rootWindow);
        if (mapViewToUse != null) {
            updateToolbarForMapView(mapViewToUse);
        } else {
            if (bookmarksToolbar != null) {
                remove(bookmarksToolbar);
                bookmarksToolbar = null;
            }
            if (currentMap != null) {
                currentMap.removeMapChangeListener(this);
                currentMap = null;
            }
            currentSelectedMapView = null;
        }
    }

	private void updateToolbarForMapView(MapView mapView) {
    	if(currentSelectedMapView == mapView)
    		return;
        if (currentMap != null) {
            currentMap.removeMapChangeListener(this);
        }
        if (currentSelectedMapView != null) {
            currentSelectedMapView.getModeController().getMapController().removeNodeSelectionListener(this);
        }
        currentSelectedMapView = mapView;
        currentMap = mapView.getMap();

        final boolean isMindMapEditor = isMindMapEditor(mapView);
        isBookmarksToolbarVisible = isMindMapEditor && Controller.getCurrentController().getViewController().isBookmarksToolbarVisible();

        if (isMindMapEditor) {
            if (bookmarksToolbar == null) {
                BookmarksController bookmarksController = mapView.getModeController().getExtension(BookmarksController.class);
                bookmarksToolbar = new BookmarkToolbar(bookmarksController, currentMap);
                bookmarksToolbar.setReducesButtonSize(false);
                bookmarksToolbar.setVisible(isBookmarksToolbarVisible);
                add(bookmarksToolbar, BorderLayout.SOUTH);
            } else {
                bookmarksToolbar.setMap(currentMap);
                bookmarksToolbar.setVisible(isBookmarksToolbarVisible);
            }
        } else {
            if (bookmarksToolbar != null) {
                remove(bookmarksToolbar);
                bookmarksToolbar = null;
            }
        }

        if (currentMap != null) {
            currentMap.addMapChangeListener(this);
        }
        if (currentSelectedMapView != null && isMindMapEditor) {
            currentSelectedMapView.getModeController().getMapController().addNodeSelectionListener(this);
        }
        updateBookmarksToolbar();
    }

    private void updateBookmarksToolbar() {
        if (currentSelectedMapView != null && isBookmarksToolbarVisible && bookmarksToolbar != null) {
            BookmarksController bookmarksController = currentSelectedMapView.getModeController()
                    .getExtension(BookmarksController.class);
            if (bookmarksController != null) {
                bookmarksController.updateBookmarksToolbar(bookmarksToolbar, currentSelectedMapView.getMap());
            }
        }
        bookmarksUpdateScheduled = false;
    }

    private boolean refreshScheduled;

    private void refreshToolbarLater() {
        if (refreshScheduled) {
            return;
        }
        refreshScheduled = true;
        SwingUtilities.invokeLater(() -> {
            try {
                refreshToolbarForContainedMapViews();
            } finally {
                refreshScheduled = false;
            }
        });
    }

    private void updateBookmarksToolbarLater() {
        if (currentSelectedMapView != null && !bookmarksUpdateScheduled) {
            bookmarksUpdateScheduled = true;
            SwingUtilities.invokeLater(this::updateBookmarksToolbar);
        }
    }

    public void requestFocusForBookmarkToolbar() {
        if (isBookmarksToolbarVisible && bookmarksToolbar != null) {
            bookmarksToolbar.requestInitialFocusInWindow();
        }
    }

    @Override
    public void mapChanged(MapChangeEvent event) {
        if (event.getMap() != currentMap) {
            return;
        }
        final Object property = event.getProperty();
        if (property.equals(MapBookmarks.class) || property.equals(Filter.class)) {
            updateBookmarksToolbarLater();
            return;
        }
        if (property.equals(MapView.class)) {
            if (event.getOldValue() == currentSelectedMapView) {
                if (currentMap != null) {
                    currentMap.removeMapChangeListener(this);
                }
                currentMap = currentSelectedMapView != null ? currentSelectedMapView.getMap() : null;
                if (currentMap != null) {
                    currentMap.addMapChangeListener(this);
                }
            }
        }
        if (property.equals(IMapViewManager.MapChangeEventProperty.MAP_VIEW_ROOT)) {
            if (bookmarksToolbar != null) {
                bookmarksToolbar.repaint();
            }
        }
    }

    @Override
    public void onNodeDeleted(NodeDeletionEvent nodeDeletionEvent) {
        if (currentSelectedMapView != null && nodeDeletionEvent.parent.getMap() == currentSelectedMapView.getMap()) {
            updateBookmarksToolbarLater();
        }
    }

    @Override
    public void onNodeInserted(NodeModel parent, NodeModel child, int newIndex) {
        if (currentSelectedMapView != null && child.getMap() == currentSelectedMapView.getMap()) {
            updateBookmarksToolbarLater();
        }
    }

    @Override
    public void onSelect(NodeModel node) {
        if(currentSelectedMapView == null) {
            final Component selectedMapView = Controller.getCurrentController().getMapViewManager().getMapViewComponent();
            if(selectedMapView instanceof MapView && SwingUtilities.isDescendingFrom(selectedMapView, rootWindow))
                refreshToolbarLater();
        }
        if (currentSelectedMapView != null && currentSelectedMapView.isSelected()) {
            updateBookmarksToolbarLater();
        }
    }

    public void dispose() {
        Controller.getCurrentController().getMapViewManager().removeMapViewChangeListener(this);
        ResourceController.getResourceController().removePropertyChangeListener(this);
        if (currentMap != null) {
            currentMap.removeMapChangeListener(this);
            currentMap = null;
        }
        if (currentSelectedMapView != null) {
            currentSelectedMapView.getModeController().getMapController().removeNodeSelectionListener(this);
            currentSelectedMapView = null;
        }
    }

    @Override
    public void afterWindowLastSelectedMapViewChanged(Window window, Component newView) {
        Window myWindow = SwingUtilities.getWindowAncestor(this);
        if (myWindow == window && newView != currentSelectedMapView && newView instanceof MapView) {
            updateToolbarForMapView((MapView) newView);
        }
    }

    @Override
    public void afterWindowLastSelectedMapViewRemoved(Window window) {
        Window myWindow = SwingUtilities.getWindowAncestor(this);
        if (myWindow == window) {
            refreshToolbarForContainedMapViews();
        }
    }

}

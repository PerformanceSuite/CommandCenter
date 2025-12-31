package org.freeplane.view.swing.map.outline;

interface OutlineActionTarget {
    void navigateUp();
    void navigateDown();
    void navigatePageUp();
    void navigatePageDown();
    void collapseOrGoToParent();
    void expandOrGoToChild();
    void expandSelectedMore();
    void reduceSelectedExpansion();
    void toggleExpandSelected();
    void selectSelectedInMap();
}

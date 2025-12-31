/*
 * Created on 23 Aug 2025
 *
 * author dimitry
 */
package org.freeplane.main.application;

import java.awt.Component;
import java.util.ArrayList;
import java.util.List;
import javax.swing.JComponent;
import org.freeplane.view.swing.map.outline.MapAwareOutlinePane;

/**
 * Manager for N-level nested auxiliary split panes. Creates and manages
 * a configurable number of nested AuxillaryEditorSplitPane instances.
 *
 * Structure for N levels:
 *   User Content
 *     ↓ main component of
 *   Level 0 AuxillaryEditorSplitPane (innermost - for notes)
 *     ↓ main component of
 *   Level 1 AuxillaryEditorSplitPane
 *     ↓ main component of
 *   ...
 *     ↓ main component of
 *   Level N-1 AuxillaryEditorSplitPane (outermost)
 */
class AuxiliarySplitPanes {

    private final List<AuxillaryEditorSplitPane> panes;
    private final int numLevels;

    /**
     * Creates nested auxiliary split panes with the given user content as the base.
     * Uses default 2 levels for backward compatibility.
     *
     * @param userContent the main user content (e.g., BookmarkToolbarPane)
     */
    public AuxiliarySplitPanes(Component userContent) {
        this(userContent, 2);
    }

    /**
     * Creates nested auxiliary split panes with the specified number of levels.
     *
     * @param userContent the main user content (e.g., BookmarkToolbarPane)
     * @param numLevels number of split pane levels (must be >= 1)
     */
    public AuxiliarySplitPanes(Component userContent, int numLevels) {
        if (numLevels < 1) {
            throw new IllegalArgumentException("Number of levels must be at least 1, got: " + numLevels);
        }

        this.numLevels = numLevels;
        this.panes = new ArrayList<>(numLevels);

        // Create controllers and panes for each level
        Component currentMain = userContent;
        for (int level = 0; level < numLevels; level++) {
            AuxiliarySplitPaneController controller = createControllerForLevel(level);
            AuxillaryEditorSplitPane pane = new AuxillaryEditorSplitPane(currentMain, controller);
            pane.setManager(this);
            panes.add(pane);

            // Next level uses this pane as its main component
            currentMain = pane;
        }

        // Initialize level 1 with MapAwareOutlinePane on the left (if it exists)
        if (numLevels >= 2) {
        	AuxillaryEditorSplitPane pane = getPane(1);
            MapAwareOutlinePane outlinePane = new MapAwareOutlinePane(pane);
            insertComponentIntoSplitPane(1, outlinePane, "outline");
			pane.bindAuxiliaryVisibilityToProperty("outlineVisible");
        }
    }

    /**
     * Creates a controller for the specified level with appropriate property keys.
     * Level 0 uses original keys for backward compatibility with notes.
     */
    private AuxiliarySplitPaneController createControllerForLevel(int level) {
        if (level == 0) {
            // Level 0 (innermost) uses original property keys for backward compatibility
            return new AuxiliarySplitPaneController(
                "aux_split_pane_last_position", "bottom");
        } else {
            // Other levels use generated property keys
            String positionKey = "aux_split_pane_level_" + level + "_position";
            String defaultLocation = level == 1 ? "right" : "bottom";
            return new AuxiliarySplitPaneController(positionKey, defaultLocation);
        }
    }

    /**
     * Gets the root pane for UI layout. This is the outermost split pane
     * that should be added to the container.
     *
     * @return the outermost split pane for UI layout
     */
    public AuxillaryEditorSplitPane getRootPane() {
        return panes.get(numLevels - 1); // Last pane is outermost
    }

    /**
     * Gets the number of levels in this nested structure.
     *
     * @return number of split pane levels
     */
    public int getNumLevels() {
        return numLevels;
    }

    /**
     * Inserts a component into the specified level.
     *
     * @param level which level to use (0 = innermost for notes, higher = outer levels)
     * @param component the component to insert
     * @param mode the mode string
     * @throws IndexOutOfBoundsException if level is invalid
     */
    public void insertComponentIntoSplitPane(int level, JComponent component, String mode) {
        validateLevel(level);
        panes.get(level).insertComponentIntoSplitPane(component, mode);
    }

    /**
     * Changes the window location for the specified level.
     *
     * @param level which level to change (0 = innermost, higher = outer levels)
     * @param location the new location ("top", "bottom", "left", "right")
     * @throws IndexOutOfBoundsException if level is invalid
     */
    public void changeAuxComponentSide(int level, String location) {
        validateLevel(level);
        panes.get(level).changeAuxComponentSide(location);
    }

    /**
     * Removes the auxiliary component from the specified level.
     *
     * @param level which level to remove from (0 = innermost, higher = outer levels)
     * @throws IndexOutOfBoundsException if level is invalid
     */
    public void removeAuxiliaryComponent(int level) {
        validateLevel(level);
        panes.get(level).removeAuxiliaryComponent();
    }

    /**
     * Gets the auxiliary component from the specified level.
     *
     * @param level which level to get from (0 = innermost, higher = outer levels)
     * @return the auxiliary component or null if none
     * @throws IndexOutOfBoundsException if level is invalid
     */
    public JComponent getAuxiliaryComponent(int level) {
        validateLevel(level);
        return panes.get(level).getAuxiliaryComponent();
    }

    /**
     * Gets the split pane for the specified level.
     *
     * @param level which level (0 = innermost, higher = outer levels)
     * @return the split pane at that level
     * @throws IndexOutOfBoundsException if level is invalid
     */
    public AuxillaryEditorSplitPane getPane(int level) {
        validateLevel(level);
        return panes.get(level);
    }

    /**
     * Moves only the level-0 auxiliary component (note pane) from this manager to the target manager.
     * Other auxiliary components (e.g., outline at level 1) are not moved and remain per-frame.
     *
     * @param target the destination AuxiliarySplitPanes
     * @param mode the current mode name used by the note pane
     */
    public void moveAuxiliaryNoteTo(AuxiliarySplitPanes target, String mode) {
        if (target == null) {
            return;
        }
        if (this.getNumLevels() < 1 || target.getNumLevels() < 1) {
            return;
        }
        AuxillaryEditorSplitPane fromPane = this.getPane(0);
        AuxillaryEditorSplitPane toPane = target.getPane(0);
        fromPane.moveAuxillaryComponentTo(toPane, mode);
    }

    /**
     * Validates that the level is within valid range.
     *
     * @param level the level to validate
     * @throws IndexOutOfBoundsException if level is invalid
     */
    private void validateLevel(int level) {
        if (level < 0 || level >= numLevels) {
            throw new IndexOutOfBoundsException("Level " + level + " is invalid. Valid range: 0 to " + (numLevels - 1));
        }
    }
}

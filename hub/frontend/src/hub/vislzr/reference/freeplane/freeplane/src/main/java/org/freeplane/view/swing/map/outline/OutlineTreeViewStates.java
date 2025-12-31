package org.freeplane.view.swing.map.outline;

import java.util.EnumMap;
import java.util.Map;

import org.freeplane.core.resources.ResourceController;
import org.freeplane.features.filter.Filter;

class OutlineTreeViewStates {
    static final String OUTLINE_DISPLAY_MODE_SYNC_PROPERTY = "outline.displayMode";
	private OutlineDisplayMode currentMode;
    private boolean followsJumpIn;
    private Filter filter;
    private final EnumMap<OutlineDisplayMode, OutlineTreeViewState> viewStatesByMode;

    OutlineTreeViewStates() {
        this(defaultMode(), true, null, new EnumMap<>(OutlineDisplayMode.class));
    }

	private static OutlineDisplayMode defaultMode() {
		return ResourceController.getResourceController().getBooleanProperty(OUTLINE_DISPLAY_MODE_SYNC_PROPERTY, false) ? OutlineDisplayMode.MAP_VIEW_SYNC : OutlineDisplayMode.MAP_VIEW;
	}

    OutlineTreeViewStates(OutlineDisplayMode currentMode,  boolean followsJumpIn, Filter filter, EnumMap<OutlineDisplayMode, OutlineTreeViewState> viewStatesByMode) {
        this.followsJumpIn = followsJumpIn;
		this.filter = filter;
		this.currentMode = currentMode != null ? currentMode : OutlineDisplayMode.MAP_VIEW;
        this.viewStatesByMode = viewStatesByMode;

    }

    OutlineTreeViewStates copy() {
        return new OutlineTreeViewStates(currentMode, followsJumpIn, filter, new EnumMap<>(viewStatesByMode));
    }

    boolean followsJumpIn() {
		return followsJumpIn;
	}

	void setFollowsJumpIn(boolean followsJumpIn) {
		this.followsJumpIn = followsJumpIn;
	}


	Filter getFilter() {
		return filter;
	}

	void setFilter(Filter filter) {
		this.filter = filter;
	}

	OutlineDisplayMode getCurrentMode() {
        return currentMode;
    }

    void setCurrentMode(OutlineDisplayMode mode) {
        if (mode != null) {
            currentMode = mode;
        }
    }

    OutlineTreeViewState getViewState() {
        return viewStatesByMode.get(currentMode.baseMode());
    }

    void putViewState(OutlineTreeViewState state) {
        final OutlineDisplayMode stateKey = currentMode.baseMode();
		if (state == null) {
            viewStatesByMode.remove(stateKey);
        } else {
            viewStatesByMode.put(stateKey, state);
        }
    }

    void loadFrom(OutlineTreeViewStates other) {
        if (other == null) {
            return;
        }
        currentMode = other.currentMode;
        viewStatesByMode.clear();
        viewStatesByMode.putAll(other.viewStatesByMode);
    }

    void loadFromMap(Map<?, ?> storedStates) {
        viewStatesByMode.clear();
        if (storedStates == null) {
            return;
        }
        for (Map.Entry<?, ?> entry : storedStates.entrySet()) {
            if (entry.getKey() instanceof OutlineDisplayMode && entry.getValue() instanceof OutlineTreeViewState) {
                viewStatesByMode.put((OutlineDisplayMode) entry.getKey(), (OutlineTreeViewState) entry.getValue());
            }
        }
    }

}

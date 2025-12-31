package org.freeplane.view.swing.map.outline;

import java.util.function.Supplier;

import org.freeplane.features.filter.Filter;
import org.freeplane.features.map.MapModel;
import org.freeplane.view.swing.map.MapView;

class FilterCache {
    private Filter cachedFilter;
    private MapModel cachedMapModel;

    Filter prepare(MapView mapView, Supplier<Filter> filterFactory) {
        MapModel mapModel = mapView.getMap();
        if (cachedFilter == null || cachedMapModel != mapModel) {
            cachedFilter = filterFactory.get();
            cachedMapModel = mapModel;
        }
        if (cachedFilter != null) {
            cachedFilter.calculateFilterResults(mapModel);
        }
        return cachedFilter;
    }

    void refresh(MapView mapView) {
        if (cachedFilter != null && mapView.getMap() == cachedMapModel) {
            cachedFilter.calculateFilterResults(cachedMapModel);
        }
    }

    void reset() {
        cachedFilter = null;
        cachedMapModel = null;
    }

    Filter current() {
        return cachedFilter;
    }
}

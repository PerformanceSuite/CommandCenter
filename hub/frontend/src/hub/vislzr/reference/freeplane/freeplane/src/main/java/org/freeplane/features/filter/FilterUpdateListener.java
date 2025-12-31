/*
 * Created on 1 Nov 2025
 *
 * author dimitry
 */
package org.freeplane.features.filter;

import org.freeplane.features.map.NodeModel;

@FunctionalInterface
public interface FilterUpdateListener {
	void onFilterResultUpdate(Filter filter, NodeModel node);
}

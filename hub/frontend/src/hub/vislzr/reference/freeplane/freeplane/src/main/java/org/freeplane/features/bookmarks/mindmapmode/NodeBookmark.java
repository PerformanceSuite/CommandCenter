package org.freeplane.features.bookmarks.mindmapmode;

import org.freeplane.features.map.NodeModel;

public class NodeBookmark {
	private final NodeModel node;
	private final NodeBookmarkDescriptor descriptor;

	public NodeBookmark(NodeModel node, NodeBookmarkDescriptor descriptor) {
		super();
		this.node = node;
		this.descriptor = descriptor;
	}

	public NodeModel getNode() {
		return node;
	}

	public NodeBookmarkDescriptor getDescriptor() {
		return descriptor;
	}

	public void open(boolean asRoot) {
		new NodeNavigator(node).open(asRoot);
	}

	public void open() {
		open(opensAsRoot());
	}

	public String getName() {
		return descriptor.getName();
	}

	boolean opensAsRoot() {
		return descriptor.opensAsRoot();
	}

	public void openAsNewView() {
		new NodeNavigator(node).openAsNewView();
	}

	public void alternativeOpen() {
		open(!opensAsRoot());
	}
}

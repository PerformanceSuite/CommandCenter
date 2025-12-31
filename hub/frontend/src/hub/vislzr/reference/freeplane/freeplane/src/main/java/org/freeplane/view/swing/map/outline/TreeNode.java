
package org.freeplane.view.swing.map.outline;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Supplier;

class TreeNode {

	enum LevelOperation {
		SET {
    		@Override
    		boolean canApply(int newLevel, int currentLevel) {
    			return true;
    		}
    	},
		REDUCE {
    		@Override
    		boolean canApply(int newLevel, int currentLevel) {
    			return newLevel < currentLevel;
    		}
    	},
		EXPAND {
    		@Override
    		boolean canApply(int newLevel, int currentLevel) {
    			return newLevel > currentLevel;
    		}
    	};

		abstract boolean canApply(int newLevel, int currentLevel);
	}

	static final int UNKNOWN_LEVEL = -1;

    private Supplier<String> titleSupplier;
    private String title;

    private final String id;
    private final List<TreeNode> children = new ArrayList<>();
    private int expansionLevel = -1;
    private TreeNode parent = null;
    private int level = 0;

    TreeNode(String id, Supplier<String> titleSupplier) {
    	this.id = id;
        this.titleSupplier = titleSupplier;
    }



    protected void setTitleSupplier(Supplier<String> titleSupplier) {
		this.titleSupplier = titleSupplier;
	}



	void update() {
        this.title = null;
    }

    void addChild(TreeNode child) {
        child.setParent(this);
        children.add(child);
        if (expansionLevel >= 0) {
            child.applyExpansionLevel(expansionLevel - 1);
        }
    }

    void applyExpansionLevel(int level) {
    	applyExpansionLevel(level, LevelOperation.SET);
    }

    private void applyExpansionLevel(int level, LevelOperation expand) {
    	if(expand.canApply(level, expansionLevel))
    		this.setExpansionLevel(level);
        if (level >= 0) {
            for (TreeNode child : getChildren()) {
                child.applyExpansionLevel(level - 1, expand);
            }
        } else {
            for (TreeNode child : getChildren()) {
                child.applyExpansionLevel(-1, expand);
            }
        }
    }

	void reduceNodeExpansion(int level) {
    	applyExpansionLevel(level, LevelOperation.REDUCE);
	}

	void expandNodeMore(int level) {
    	applyExpansionLevel(level, LevelOperation.EXPAND);
	}



    int getMaxExpansionLevel() {
        if (expansionLevel <= 0 || getChildren().isEmpty()) {
            return expansionLevel;
        }
        int maxLevel = 0;
        for (TreeNode child : getChildren()) {
            maxLevel = Math.max(maxLevel, 1 + child.getMaxExpansionLevel());
        }
        return maxLevel;
    }

    boolean isExpanded() {
        return expansionLevel > 0;
    }

    boolean isVisible() {
        return expansionLevel >= 0;
    }

    int getExpansionLevel() {
        return expansionLevel;
    }


    @Override
	public String toString() {
        return "TreeNode [title=" + getTitle() + "]";
    }

    TreeNode getParent() {
        return parent;
    }

    void setParent(TreeNode parent) {
        this.parent = parent;
        if(parent != null) {
			refreshLevelsRecursively();
			applyExpansionLevel(Math.max(0, parent.expansionLevel) - 1);
		}
    }

	private void setExpansionLevel(int expansionLevel) {
		this.expansionLevel = expansionLevel;
	}

    List<TreeNode> getChildren() { return Collections.unmodifiableList(children); }

    int childCount() { return children.size(); }

	void add(MapTreeNode node, int index) {
		if (index < children.size()) {
		    children.add(index, node);
		} else {
		    children.add(node);
		}
	}

	boolean remove(MapTreeNode toRemove) {
		return children.remove(toRemove);
	}

    String getId() {
        return id;
    }

	String getTitle() {
		if(title == null)
			title = titleSupplier.get();
		return title;
	}

    TreeNode findVisibleAncestorOrSelf() {

        for(TreeNode node = this;
        		node != null;
        		node = node.getParent()) {
            if(node.isVisible())
                return node;
        }
        return null;
    }

    int getLevel() {
        return level;
    }

    private void refreshLevelsRecursively() {
    	level = parent.level + 1;
        for (TreeNode child : children) {
            child.refreshLevelsRecursively();
        }
    }



	void setLevel(int level) {
		if(parent == null)
			this.level = level;
		else
			throw new IllegalStateException();
	}



	boolean isAncestorOf(TreeNode node) {
		for(TreeNode ancestor = node.getParent(); ancestor != null; ancestor = ancestor.getParent()) {
			if(this == ancestor)
				return true;
		}
		return false;
	}
}

Refactoring Plan for org.freeplane.view.swing.map.outline

Purpose: maintain a living refactoring roadmap that reflects the actual code, clarifies responsibilities, and sequences safe improvements.

Guiding Principles
- Tell, do not ask: prefer behavior‑oriented methods over exposing internal data.
- Single responsibility: isolate rendering, layout, state, selection, focus, and integration concerns.
- No inner classes: extract inner/anonymous classes to top‑level types; avoid hiding complexity.
- No duplication: deduplicate key bindings, selection painting, and focus logic.
- Remove unused code: delete dead parameters, fields, and empty overrides.
- Backward compatibility by default: prefer local, non‑breaking changes; document any necessary interface updates.
- Minimal, focused diffs: avoid opportunistic refactors; keep scope tight and auditable.
- Phase gates: no code until plan approved for each change phase.

Design

Core containers and views
- OutlinePane — top‑level container; lays out breadcrumb + content and wires scroll listeners.
- MapAwareOutlinePane — integrates outline with MapView; listens to map/filter/selection changes and swaps roots.
- ScrollableTreePanel — content view hosting BlockPanel instances; renders visible nodes; delegates actions and focus.
- BreadcrumbPanel — renders ancestor buttons; forwards interactions to the controller.
- BlockPanel — hosts a contiguous slice of node buttons (one block) without extra logic.

Models and state
- TreeNode — logical outline node (id, title, children, parent, level, expansion); behavior methods over data exposure.
- MapTreeNode — TreeNode backed by NodeModel; listens to insert/delete/change and updates the outline view.
- VisibleOutlineState — computes/stores visible node list, hovered node, breadcrumb height, first visible node id.
- OutlineSelection — selected‑node model with helpers (get, set, isSelected).
- BreadcrumbState — immutable snapshot of breadcrumb nodes, height, and anchor index.
- OutlineViewState — persistent expansion + first visible + root + filter; applies to a tree.

Layout, geometry, viewport
- OutlineGeometry — derived dimensions: row height, indents, button widths, gaps, icon size.
- NodePositioning — positioning math for buttons, icons, blocks, and viewport positions.
- OutlineViewport — JScrollPane adapter computing visible ranges and page size; updates view position.
- OutlineVisibleBlockRange (new) — extracted from OutlineViewport.VisibleBlockRange; immutable and query‑oriented.

Block orchestration
- OutlineBlockLayout — creates/removes/positions BlockPanel instances; updates preferred sizes from content.
- OutlineBlockViewCache — caches block panels by index; read‑only views for keys/values.

Controllers, actions, focus
- OutlineController — thin delegator for navigation/expansion; keeps panel logic out of widgets.
- ExpansionControls — expand/collapse/more/less; refreshes visible state; keeps selection visible.
- OutlineSelectionBridge — syncs outline selection with MapView and focuses map node on demand.
- OutlineActions (new) — shared Swing actions and key bindings (up/down/page, left/right, expand more/reduce) used by panels.
- OutlineFocusManager (new) — focuses selected NodeButton, restores focus after updates, determines outline vs map focus.
- OutlineSelectionHistory — keeps preferred-child tracking across selections.

Rendering helpers
- NodeButton — typed JButton bound to a TreeNode.
- SelectionCircleIcon — paints the selection indicator.
- SelectionPainter (new) — paints selection indicator next to a NodeButton using NodePositioning; removes duplication.

Integration and building
- NodeTreeBuilder — builds TreeNode graph from MapView honoring filter and saved state.
- BreadcrumbPath — computes breadcrumb path, height, and anchor index from the first fully visible node.
- ExpansionHandler — interface for expansion operations (kept as an abstraction).

Supporting data structures
- lastSelectedChildByParent (Map) — lives in OutlineSelectionHistory to centralize selection-related state.
- Unmodifiable children — TreeNode.getChildren returns an unmodifiable list to prevent external mutation.
- Caches — OutlineBlockViewCache provides controlled access to BlockPanel instances.

Current Architecture Snapshot (as implemented now)
- OutlinePane: composes BreadcrumbPanel and ScrollableTreePanel inside a scroll pane; wires layout and scroll listeners.
- ScrollableTreePanel: orchestrates visible state, block creation, navigation buttons, selection and focus, scrolling, and repaint triggers.
- BreadcrumbPanel: renders breadcrumb buttons, handles its own key bindings, and triggers navigation and selection through OutlineController.
- VisibleOutlineState: computes and stores the visible node sequence, hovered node, breadcrumb area height, and the first visible node identifier.
- NodePositioning and OutlineGeometry: provide geometry metrics and positioning calculations for buttons, icons, blocks, and viewport.
- OutlineBlockLayout and OutlineBlockViewCache: create, size, and cache BlockPanel instances for visible content.
- NavigationButtons and ExpansionControls: display per‑node navigation controls and perform expansion operations with selection synchronization.
- MapAwareOutlinePane, MapTreeNode, NodeTreeBuilder, OutlineViewState: integrate with MapView, build and update the TreeNode graph, and persist and restore outline view state.
- NodeButton and SelectionCircleIcon: typed node button and selection indicator used by both BreadcrumbPanel and BlockPanel.

What Is Already Done (baseline)
- Typed node buttons: NodeButton replaces ad‑hoc client properties.
- VisibleOutlineState encapsulation: callers use getVisibleNodeCount, getNodeAtVisibleIndex, and getNodeIdAtVisibleIndex rather than iterating raw lists.
- TreeNode levels: TreeNode carries level and maintains it on parent assignment; layout uses TreeNode.getLevel.
- Block view caching: OutlineBlockViewCache owned by ScrollableTreePanel; OutlineBlockLayout handles block creation and preferred sizing.
- Data object encapsulation: OutlineViewport.VisibleBlockRange and OutlineViewState expose immutable fields through getters; BreadcrumbState encapsulates breadcrumb data (see package peer).
- FlatNode removal: the previous FlatNode concept is gone; the visible list uses TreeNode directly.

Key Observations and Opportunities
- ScrollableTreePanel remains large and mixes focus management, selection scrolling, navigation button placement, block orchestration, and repaint concerns.
- Key bindings are duplicated between BreadcrumbPanel and ScrollableTreePanel, increasing maintenance cost.
- Selection indicator painting logic is duplicated in BreadcrumbPanel and BlockPanel.
- Minor cleanup candidates exist (for example, an unused parameter in VisibleOutlineState.buildVisibleList, an unused field in OutlineController, and an empty paintComponent override in ScrollableTreePanel).
- Responsibilities are otherwise reasonably separated: geometry, positioning, viewport math, and block layout are already extracted.

Phased Refactoring Plan
For every phase below: no code until plan approved.

Phase 1: Remove inner/anonymous classes (no behavior change)
- Extract MapAwareOutlinePane.SelectedNodeUpdater to a top‑level OutlineSelectedNodeUpdater implementing INodeSelectionListener.
- Extract OutlineViewport.VisibleBlockRange to a top‑level OutlineVisibleBlockRange and update OutlineViewport to use it.
- Replace anonymous adapters in ScrollableTreePanel/BlockPanel/BreadcrumbPanel with named top‑level adapters where needed, or rewire through shared actions.
- Success criteria: identical behavior; all significant logic in top‑level types; improved readability.

Phase 2: Centralize key bindings and actions (no behavior change)
- Problem: BreadcrumbPanel and ScrollableTreePanel each define identical key bindings and action wiring.
- Change: introduce OutlineActions (a small holder of javax.swing.Action instances) or OutlineKeyBindings that exposes shared actions. Panels bind to those shared actions instead of duplicating mappings.
- Success criteria: single source of truth for navigation actions; both panels respond exactly as before.
- Touch points: BreadcrumbPanel, ScrollableTreePanel, new OutlineActions (package‑private), OutlineController (delegations unchanged).

Phase 3: Extract focus management from ScrollableTreePanel
- Problem: focusSelectionButton, restoreFocusIfNeeded, isWithinOutline, and the logic to locate the NodeButton for a node are embedded and partially duplicated.
- Change: create OutlineFocusManager responsible for focus queries and moves within outline components and back to the map view via OutlineSelectionBridge.
- Success criteria: ScrollableTreePanel shrinks; focus logic covered in one place; no focus regressions when scrolling, changing selection, or switching between outline and map.
- Touch points: ScrollableTreePanel (delegate), BreadcrumbPanel (optional minimal delegate), OutlineSelectionBridge (reuse), new OutlineFocusManager.

Phase 4: Unify selection indicator painting
- Problem: duplicated painting of the selection icon in BreadcrumbPanel and BlockPanel.
- Change: introduce SelectionPainter (utility) that computes icon placement via NodePositioning and paints SelectionCircleIcon for a given NodeButton and selection.
- Success criteria: identical visuals with one implementation; future changes to selection appearance are localized.
- Touch points: BreadcrumbPanel, BlockPanel, NodePositioning (reused), new SelectionPainter.

Phase 5: Small internal cleanups (safe, mechanical)
- Remove unused code and noise:
  - Remove the unused level parameter from VisibleOutlineState.buildVisibleList and update callers.
  - Remove the unused scrollPane field from OutlineController or use it where appropriate.
  - Remove the empty paintComponent override in ScrollableTreePanel if there is no side effect.
- Success criteria: no behavior change; smaller surface and fewer warnings.
- Touch points: VisibleOutlineState, OutlineController, ScrollableTreePanel.

Phase 6: Optional consolidation of selection orchestration
- Problem: setSelectedNode currently triggers multiple responsibilities (state update, cache invalidation, block rebuild, scrolling, and focusing) inside ScrollableTreePanel.
- Change: introduce OutlineSelectionHistory to encapsulate selection tracking while keeping UI updates in ScrollableTreePanel (future selection orchestrator remains optional).
- Success criteria: cleaner ScrollableTreePanel with selection orchestration isolated; unchanged observable behavior.
- Touch points: ScrollableTreePanel, new OutlineSelectionHistory.

Phase 7: Documentation and invariants
- Document invariants for geometry and positioning (for example, how breadcrumb height is computed and how it affects block ranges) and assert them where low‑risk.
- Add targeted unit tests for helper classes that are already logic‑centric (NodePositioning, OutlineVisibleBlockRange/OutlineViewport calculations, OutlineViewState.applyTo).
- Success criteria: clearer invariants, safer future edits; helper logic covered by tests.

Progress
- Phase 1: done — extracted inner/anonymous classes (VisibleBlockRange → OutlineVisibleBlockRange; SelectedNodeUpdater → OutlineSelectedNodeUpdater; focus click adapter top‑level).
- Phase 2: done — centralized key bindings via OutlineActions and OutlineActionTarget; panels bind to shared actions.
- Phase 3: done — focus logic extracted to OutlineFocusManager; ScrollableTreePanel now delegates.
- Phase 4: done — unified selection painting via SelectionPainter; removed duplication in BlockPanel and BreadcrumbPanel.
- Phase 5: done — removed unused parameter in VisibleOutlineState and empty paint override in ScrollableTreePanel.
- Phase 6: in progress — introduced OutlineSelectionHistory for preferred-child tracking; further selection orchestration extraction remains optional.
- Phase 7: done — documented invariants and added AssertJ tests for NodePositioning and OutlineViewport/OutlineVisibleBlockRange.

Invariants (initial)
- OutlineGeometry: rowHeight > 0; indent == rowHeight; navButtonsTotalWidth == 3 * navButtonWidth; iconDiameter > 0.
- VisibleOutlineState: visibleNodes is a pre‑order list of expanded nodes starting at root; breadcrumbAreaHeight is a non‑negative multiple of rowHeight.
- OutlineViewport: when calculating block ranges, adjusted view y is max(0, viewRect.y − breadcrumbAreaHeight); firstBlock ≤ lastBlock when nodes exist.
- NodePositioning: calculateTextButtonX(level) is monotonic non‑decreasing over level; selection icon position lies to the right of the button bounds.

Verification Notes
- Tests use AssertJ assertions. Current helper tests live under freeplane/src/test/java/org/freeplane/view/swing/map/outline/.
- Add further tests where logic is pure and decoupled (e.g., BreadcrumbPath and OutlineSelectionHistory preferredChild behavior).
- Manual checks still recommended for: focus transitions (OutlineFocusManager), selection sync with MapView (OutlineSelectionBridge), and navigation buttons behavior.

Risks and Rollback
- Phases 1–4 are low risk and mechanical; each step is independently revertible.
- Phases 5–6 alter orchestration and carry higher coordination risk; gate with focused tests and manual checks; rollback by reverting the new manager classes and delegations.

Verification Checklist (per phase)
- Manual flows: navigation keys, mouse hover navigation buttons, expand and collapse, page navigation, selection sync with MapView, focus transitions between outline and map.
- Performance sanity on large maps (block creation and scrolling remain responsive).

Notes on Completed Baseline (for historical context)
- FlatNode removed. Do not depend on snapshot depths for layout; use TreeNode.getLevel.
- VisibleOutlineState is the single source for visible nodes; prefer behavior methods over list exposure.
- Block creation and sizing delegated to OutlineBlockLayout with OutlineBlockViewCache.

Appendix: Candidate follow‑ups not yet planned
- Consider a lighter geometry bootstrap that does not require an actual JButton instance.
- Evaluate whether OutlineController adds value beyond indirection; keep if it meaningfully decouples panels.

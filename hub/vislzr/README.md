# VISLZR - CommandCenter Graph Visualization

Interactive graph visualization for CommandCenter projects. Real-time visualization of code structure, dependencies, tasks, and audits.

## Features

- 🎨 **Interactive Graph Visualization** - ReactFlow-powered graph with custom node types
- 🔄 **Real-time Updates** - Server-Sent Events for live graph synchronization
- 🔍 **Code Review & Audits** - Trigger audits directly from graph nodes
- 📊 **Custom Node Types** - File, Symbol, Service, and Task visualizations
- 🎯 **Detail Panel** - In-depth node information and actions
- ⚡ **GraphQL API** - Efficient data fetching with urql

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Graph**: ReactFlow
- **State**: Zustand (for future state management)
- **API**: urql (GraphQL client)
- **Real-time**: Server-Sent Events (SSE)
- **Animations**: Framer Motion

## Prerequisites

- Node.js 18+
- npm or yarn
- CommandCenter backend running on http://localhost:8000

## Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

## Environment Variables

Create a `.env.local` file with:

```env
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:8000/graphql
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Project Structure

```
vislzr/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout with GraphQLProvider
│   │   ├── page.tsx                # Home page - project selector
│   │   ├── project/[id]/
│   │   │   └── page.tsx            # Project graph view
│   │   ├── ecosystem/              # Multi-project federation (Phase 9)
│   │   └── workflows/              # Workflow visualization (Phase 10)
│   ├── components/
│   │   ├── graph/
│   │   │   └── GraphCanvas.tsx     # Main visualization component
│   │   ├── nodes/
│   │   │   ├── FileNode.tsx        # File entity node
│   │   │   ├── SymbolNode.tsx      # Symbol entity node
│   │   │   ├── ServiceNode.tsx     # Service entity node
│   │   │   └── TaskNode.tsx        # Task entity node
│   │   ├── panels/
│   │   │   └── NodeDetailPanel.tsx # Node detail sidebar
│   │   └── providers/
│   │       └── GraphQLProvider.tsx # urql client wrapper
│   └── lib/
│       ├── graphql/
│       │   ├── client.ts           # urql client config
│       │   ├── queries.ts          # GraphQL queries
│       │   └── mutations.ts        # GraphQL mutations
│       └── websocket/
│           └── events.ts           # SSE event hooks
```

## Usage

### Viewing a Project Graph

1. Navigate to http://localhost:3000
2. Click on a project card
3. The graph will load showing files, symbols, services, and tasks

### Interacting with Nodes

- **Click a node** to open the detail panel
- **Pan & Zoom** using mouse/trackpad
- **Use controls** in bottom-left for zoom/fit
- **Mini-map** in bottom-right for navigation

### Triggering Audits

1. Click any file or symbol node
2. Open the **Audits** tab in the detail panel
3. Click one of the audit buttons:
   - 🔍 Run Code Review
   - 🔒 Run Security Scan
   - ✅ Run Completeness Check
4. The audit will trigger via NATS and update in real-time

### Real-time Updates

The graph automatically updates when:
- New symbols are indexed
- Tasks are created
- Audits complete
- Graph data changes

## GraphQL Queries

### Get Project Graph

```graphql
query GetProjectGraph($projectId: Int!, $depth: Int) {
  projectGraph(projectId: $projectId, depth: $depth) {
    nodes {
      id
      entity
      label
      metadata
    }
    edges {
      fromId
      toId
      type
    }
  }
}
```

### Trigger Audit

```graphql
mutation TriggerAudit(
  $targetEntity: String!
  $targetId: Int!
  $kind: String!
  $projectId: Int!
) {
  triggerAudit(
    targetEntity: $targetEntity
    targetId: $targetId
    kind: $kind
    projectId: $projectId
  ) {
    id
    status
    summary
  }
}
```

## Development

### Running the Dev Server

```bash
npm run dev
```

### Building for Production

```bash
npm run build
npm run start
```

### Linting

```bash
npm run lint
```

## Integration with CommandCenter

VISLZR connects to the CommandCenter backend via:

1. **GraphQL API** (`/graphql`) - Graph data queries
2. **SSE Events** (`/api/events/stream`) - Real-time updates
3. **REST API** (`/api/graph/*`) - Future direct endpoints

Ensure the backend is running with:
- Phase 7 GraphService implemented
- GraphQL endpoint enabled
- SSE streaming endpoint active

## Node Types

### FileNode
- **Entity**: `graph_file`
- **Icon**: File icon
- **Color**: Blue
- **Shows**: File path

### SymbolNode
- **Entity**: `graph_symbol`
- **Icon**: Letter (f=function, C=class, etc.)
- **Color**: Purple
- **Shows**: Qualified name

### ServiceNode
- **Entity**: `service`
- **Icon**: Server icon
- **Color**: Varies by health (green=up, red=down, yellow=degraded)
- **Shows**: Service name and type

### TaskNode
- **Entity**: `graph_task`
- **Icon**: Emoji by kind (✨=feature, 🐛=bug, etc.)
- **Color**: Varies by status
- **Shows**: Task title

## Future Enhancements (Phase 9-12)

- [ ] **Ecosystem Mode** - Multi-project federation view
- [ ] **Workflow Visualization** - Agent orchestration display
- [ ] **Ghost Nodes** - Planned items without implementation
- [ ] **Time Slider** - Historical graph states
- [ ] **Search** - Full-text search across graph
- [ ] **Filters** - Filter by entity type, status, etc.
- [ ] **Layout Algorithms** - Force-directed, hierarchical, circular
- [ ] **WebGL Rendering** - High-performance for 10k+ nodes

## Troubleshooting

### Graph not loading

- Check backend is running on http://localhost:8000
- Verify GraphQL endpoint: http://localhost:8000/graphql
- Check browser console for errors
- Ensure Phase 7 GraphService is implemented

### Real-time updates not working

- Verify SSE endpoint: http://localhost:8000/api/events/stream
- Check NATS is running
- Ensure event publishing is configured in backend

### Audit triggers failing

- Check GraphQL mutation is succeeding
- Verify NATS client is connected in backend
- Ensure audit agents are running

## License

MIT

## Phase Information

- **Phase**: 8 - VISLZR Frontend
- **Week**: 1 of 4 (Weeks 13-16)
- **Status**: Initial implementation complete
- **Milestone**: MVP with ReactFlow visualization and audit triggers

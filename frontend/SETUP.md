# Command Center Frontend - Setup Guide

## Quick Start

```bash
# Navigate to frontend directory
cd /Users/danielconnolly/Projects/Performia/worktrees/cc-frontend/commandcenter/frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at **http://localhost:3000**

## What Was Built

### File Count: 33 files, 1,390 lines of code

### Configuration Files (9)
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration (strict mode)
- `tsconfig.node.json` - TypeScript config for Vite
- `vite.config.ts` - Vite build tool configuration
- `tailwind.config.js` - Tailwind CSS theme
- `postcss.config.js` - PostCSS configuration
- `.eslintrc.cjs` - ESLint rules
- `.gitignore` - Git ignore patterns
- `Dockerfile` - Production container build

### Type Definitions (3)
- `types/repository.ts` - Repository interfaces
- `types/technology.ts` - Technology & domain types
- `types/research.ts` - Research entry types

### Services & Hooks (3)
- `services/api.ts` - Centralized API client (134 lines)
- `hooks/useRepositories.ts` - Repository CRUD operations
- `hooks/useTechnologies.ts` - Technology management

### Common Components (3)
- `components/common/Sidebar.tsx` - Navigation sidebar
- `components/common/Header.tsx` - Page header with title
- `components/common/LoadingSpinner.tsx` - Reusable spinner

### View Components (8)
- `Dashboard/DashboardView.tsx` - Main dashboard with stats
- `Dashboard/RepoSelector.tsx` - Repository selection grid
- `TechnologyRadar/RadarView.tsx` - Technology listing by domain
- `TechnologyRadar/TechnologyCard.tsx` - Individual tech card
- `Settings/SettingsView.tsx` - Settings page
- `Settings/RepositoryManager.tsx` - Repo management
- `KnowledgeBase/KnowledgeView.tsx` - Knowledge search
- `ResearchHub/ResearchView.tsx` - Research entries

### Core Files (4)
- `main.tsx` - Application entry point
- `App.tsx` - Main app with routing
- `index.css` - Global styles with Tailwind
- `index.html` - HTML template

## Architecture Highlights

### Routing (React Router 6)
- `/` - Dashboard
- `/radar` - Technology Radar
- `/research` - Research Hub
- `/knowledge` - Knowledge Base
- `/settings` - Settings

### API Integration
All API calls go through the centralized `api` service:
- Automatic auth token injection
- Error handling with interceptors
- Type-safe request/response
- Proxy to backend at localhost:8000

### State Management
- Custom hooks for data fetching
- Loading and error states
- Optimistic updates
- Automatic refetching

### Type Safety
- Strict TypeScript mode
- All props typed
- API responses typed
- Environment variables typed

## Next Steps

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development**
   ```bash
   npm run dev
   ```

3. **Verify Backend Connection**
   - Ensure backend is running at http://localhost:8000
   - Check API endpoints match frontend expectations

4. **Build for Production**
   ```bash
   npm run build
   ```

5. **Docker Deployment** (optional)
   ```bash
   docker build -t commandcenter-frontend .
   docker run -p 80:80 commandcenter-frontend
   ```

## Development Commands

- `npm run dev` - Start dev server (port 3000)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - TypeScript validation

## Environment Variables

Create `.env` from `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Tech Stack Summary

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.0.0 | UI framework |
| TypeScript | 5.3.0 | Type safety |
| Vite | 6.0.0 | Build tool |
| Tailwind CSS | 4.0.0 | Styling |
| React Router | 6.21.0 | Routing |
| Axios | 1.6.0 | HTTP client |
| Lucide React | 0.300.0 | Icons |
| Chart.js | 4.4.0 | Visualization |

## Commit Information

**Branch**: `feature/cc-frontend`
**Commit**: `19264c7`
**Message**: "feat(frontend): React scaffold with routing, components, and TypeScript"

All files committed and ready for development!

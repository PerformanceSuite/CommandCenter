# Command Center Frontend

Modern React 19 frontend for the Performia Command Center development hub.

## Tech Stack

- **React 19** - Latest React with concurrent features
- **TypeScript 5** - Type-safe development
- **Vite 6** - Lightning-fast build tool
- **Tailwind CSS 4** - Utility-first styling
- **React Router 6** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Modern icon library
- **Chart.js** - Data visualization

## Features

- **Dashboard** - Overview of repositories and technologies
- **Technology Radar** - Track and visualize technology adoption
- **Research Hub** - Manage research entries and findings
- **Knowledge Base** - Search and query knowledge
- **Settings** - Repository and system configuration

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Start development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

### Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
src/
├── components/
│   ├── common/          # Shared components
│   ├── Dashboard/       # Dashboard view
│   ├── TechnologyRadar/ # Tech radar view
│   ├── ResearchHub/     # Research management
│   ├── KnowledgeBase/   # Knowledge search
│   └── Settings/        # Settings view
├── hooks/               # Custom React hooks
├── services/            # API client
├── types/               # TypeScript definitions
├── App.tsx             # Main app component
└── main.tsx            # Entry point
```

## API Integration

The frontend connects to the backend API at the URL specified in `VITE_API_BASE_URL` environment variable (defaults to `http://localhost:8000`).

All API calls are handled through the centralized `api` service in `src/services/api.ts`.

## Docker

Build and run with Docker:

```bash
docker build -t commandcenter-frontend .
docker run -p 80:80 commandcenter-frontend
```

## License

Part of the Performia project.

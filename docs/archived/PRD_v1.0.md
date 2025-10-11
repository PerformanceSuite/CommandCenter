# **Performia R\&D Command Center: PRD & Technical Specification**

Last Updated: October 5, 2025  
Version: 1.0

## **1\. Product Requirements Document (PRD)**

### **1.1. Introduction & Vision**

**Product:** The Performia R\&D Command Center

**Vision:** To create a dedicated, locally-run "source of truth" application that empowers the Performia development team to efficiently track emerging technologies, manage research tasks, build a persistent knowledge base, and maintain a direct line of sight to the active codebase.

**Problem:** R\&D projects for complex systems like Performia involve tracking hundreds of rapidly evolving technologies, academic papers, and open-source projects. This information is often scattered across documents, bookmarks, and team messages, leading to knowledge gaps, duplicated effort, and a disconnect between research and development.

**Solution:** The R\&D Command Center is a full-stack, single-page application that runs locally on a developer's machine. It provides a centralized, interactive dashboard to manage the entire R\&D lifecycle, from initial discovery on a "Technology Radar" to in-depth analysis in a "Research Hub" and finally, to permanent storage in a searchable "Knowledge Base" (RAG).

### **1.2. Target Audience & Persona**

* **Persona:** Alex, the R\&D Lead  
* **Who:** A developer, product manager, or researcher responsible for guiding the technical strategy of the Performia project.  
* **Needs:** A single, reliable place to see the status of all research initiatives; a structured workflow for investigating new technologies; a way to ensure research findings are captured permanently and are easily accessible; a quick way to check the pulse of the active GitHub repository.  
* **Pain Points:** "I have a dozen browser tabs open with research papers." "Did we already look into this six months ago?" "I need to prepare a status update for leadership, but my notes are all over the place." "Is our research aligned with what's actually being built?"

### **1.3. Core User Stories**

| As... | I want to... | So that I can... |
| :---- | :---- | :---- |
| R\&D Lead | See a high-level dashboard with research progress and the latest GitHub commit | ...get a 30-second overview of the entire project's status. |
| R\&D Lead | Visually browse all tracked technologies, grouped by domain and status | ...quickly identify which technologies are promising and which need investigation. |
| R\&D Lead | Initiate a "research task" for a specific technology | ...begin a structured investigation using an AI-generated plan. |
| R\&D Lead | Upload a research document (PDF, TXT) to a specific task | ...have an AI analyze it and provide a summary grounded in that document's specific contents. |
| R\&D Lead | Document my findings and save the completed research to a knowledge base | ...create a permanent, searchable record of the decision-making process. |
| R\&D Lead | Search the entire knowledge base by keyword | ...quickly find past research and avoid re-doing work. |
| R\&D Lead | Configure the app with my personal GitHub token | ...securely connect the dashboard to our private repository. |

### **1.4. Feature Set Breakdown**

#### **Feature 1: The Dashboard (Home View)**

The application's landing page, providing a mission control overview.

* **Project Status Chart:** A doughnut chart visualizing the breakdown of all tracked technologies by their current status (Research, Beta, Ready).  
* **Key Metrics Widget:** At-a-glance numbers for "Total Technologies Tracked," "Active Research Tasks," etc.  
* **GitHub Sync Widget:** Displays the author, message, and date of the latest commit to the configured GitHub repository. Includes a link to the commit and a manual refresh button.

#### **Feature 2: Technology Radar**

An interactive view of all potential technologies.

* **Domain Grouping:** Technologies are visually grouped into logical domains (Core Engine, Experience, Immersive, etc.).  
* **Technology Cards:** Each technology is represented by a card showing its title, a brief description, and its current status.  
* **Status Badges:** Color-coded badges (e.g., Red for "Research," Amber for "Beta," Green for "Ready") provide instant visual cues.  
* **Action Button:** A button on "Research" status cards allows the user to initiate a Research Task, which transitions them to the Research Hub.

#### **Feature 3: Research Hub**

A dedicated workspace for investigating a single technology.

* **Task Focus:** The view is focused on a single, active technology task selected from the Radar.  
* **Document Ingestion:** A file uploader allows the user to select a local research document (.txt, .md). The file is uploaded to the backend for analysis.  
* **Grounded AI Analysis:** A button triggers a call to an AI (simulated Gemini API) that "reads" the uploaded document and generates a structured analysis (Summary, Alignment, Recommendation) based on its content.  
* **Notes & Findings:** A large text area for the user to add their own manual notes, observations, and links.  
* **Promote to Knowledge Base:** A final action button that takes the user's notes and the AI analysis, combines them, and saves the result as a new entry in the Knowledge Base.

#### **Feature 4: Knowledge Base (RAG)**

A simple, searchable repository of all completed research.

* **File-Based Storage:** Each entry is a single Markdown file stored on the local file system.  
* **Search Functionality:** A search bar allows users to filter the list of knowledge entries by keyword, searching both filenames and file content.  
* **Two-Pane View:** A master-detail interface with a list of all knowledge entries on the left and the content of the selected entry on the right.

#### **Feature 5: Settings**

A view for user-specific configuration.

* **GitHub Configuration:** Input fields for the user to provide the GitHub repository path (owner/repo) and their Personal Access Token (PAT).  
* **Local Storage:** Settings are saved in the browser's localStorage for persistence.

### **1.5. Success Metrics (Internal Tool)**

* **Adoption:** The tool is used weekly by the core R\&D team.  
* **Efficiency:** Time to document and store findings for a new technology is reduced by 50%.  
* **Knowledge Retention:** All major technology decisions made after the tool's adoption have a corresponding entry in the Knowledge Base.  
* **Clarity:** Leadership can understand the R\&D pipeline status at any time by viewing the dashboard.

## **2\. Technical Specification**

### **2.1. System Architecture**

The application is a **local-first, client-server monolith**.

* **Backend:** A single Node.js process using Express.js. It is responsible for serving the frontend, handling all API requests, interacting with the db.json file, and managing the file system for uploads and the knowledge base.  
* **Frontend:** A single-page application built with React. It runs entirely in the browser and communicates with the backend via HTTP requests. It does **not** use a build step (no JSX, Webpack, or Vite); React is loaded from a CDN.  
* **Data Flow:** The frontend requests data from the backend API. The backend reads from db.json or the file system and returns JSON data. User actions on the frontend trigger further API calls that instruct the backend to write data.

### **2.2. Technology Stack**

* **Backend:** Node.js (v18+), Express.js (v4+)  
* **Database:** LowDB (v7+) for JSON file manipulation  
* **File Uploads:** Multer (v1+)  
* **Frontend:** React (v18), ReactDOM (v18) \- loaded via ESM CDN  
* **Charting:** Chart.js (v4+) \- loaded via CDN  
* **Styling:** Tailwind CSS (v3+) \- configured via CDN script

### **2.3. File & Folder Structure**

CommandCenter/  
├── public/                \# All static frontend files served to the browser  
│   ├── App.js             \# The main React application code  
│   └── index.html         \# The HTML shell that loads the app  
├── rag\_knowledge\_base/    \# Auto-generated folder for markdown files  
├── uploaded\_research/     \# Auto-generated folder for uploaded documents  
├── .gitignore             \# Specifies files for Git to ignore  
├── db.json                \# The local JSON database  
├── package.json           \# Project metadata and dependencies  
├── README.md              \# Setup and usage instructions  
└── server.js              \# The backend Express server

### **2.4. Data Models**

#### **db.json Technology Object**

The technologies array in db.json will contain objects with this structure:

{  
  "id": "string",          // Unique identifier (e.g., "core-1")  
  "domain": "string",      // Category (e.g., "core-engine")  
  "title": "string",         // Display name (e.g., "Streaming Audio Transformers")  
  "relevance": "string",   // "high", "medium", or "low"  
  "status": "string",      // "research", "beta", or "ready"  
  "content": "string",     // A short description  
  "notes": "string",         // User-added notes, can be Markdown  
  "ragLink": "string | null" // The filename of the corresponding MD file in the RAG  
}

#### **rag\_knowledge\_base Markdown File**

Each file in this directory will have a structure like this:

\# R\&D Briefing: \[Technology Title\]

\[User-added notes and findings\]

\---  
\#\# AI Analysis Summary  
\[AI-generated analysis text\]  
Of course. Let's start completely fresh and build the definitive document from the ground up in this new canvas. My apologies for the previous frustrating attempts; this time, we will create the single, complete, and unambiguous blueprint you need.

This document is the **Performia R\&D Command Center: Product Requirements Document (PRD) & Technical Specification**. It contains everything required to understand and build the application, from the high-level vision down to the specific API endpoints and data structures.

Here is the complete and final specification in a single file.

### **2.5. API Endpoints (Server Contract)**

**`GET /api/data`**

* **Description:** Fetches the entire contents of the `db.json` file.  
* **Request Body:** None.  
* **Success Response (200):** The full JSON object from `db.json`.

**`POST /api/upload-research`**

* **Description:** Uploads a single file for a research task.  
* **Request Body:** `multipart/form-data` with a single field named `researchDoc`.  
* **Success Response (200):** `{"message": "File uploaded", "filename": "1665000000-paper.txt"}`

**`POST /api/generate-grounded-analysis`**

* **Description:** Triggers the simulated AI analysis of an uploaded document.  
* **Request Body:** `{"technology": {...}, "documentFilename": "1665000000-paper.txt"}`  
* **Success Response (200):** `{"analysis": "### AI-Generated Analysis..."}`

**`POST /api/add-to-rag`**

* **Description:** Finalizes research and creates a knowledge base entry.  
* **Request Body:** `{"id": "core-1", "title": "...", "notes": "..."}`  
* **Success Response (200):** `{"success": true, "technology": {...}}` (returns the updated technology object).

**`GET /api/rag-files`**

* **Description:** Retrieves all entries from the knowledge base.  
* **Request Body:** None.  
* **Success Response (200):** `[{"name": "file1.md", "content": "..."}, ...]`

**`POST /api/github-status`**

* **Description:** Fetches the latest commit from a GitHub repo.  
* **Request Body:** `{"repo": "owner/repo", "token": "ghp_..."}`  
* **Success Response (200):** `{"lastCommit": {...}}` (full commit object from GitHub API).

### **2.6. Frontend Component Breakdown**

* **`App.js`:** The root component. Manages view state (`dashboard`, `radar`, etc.), fetches all initial data, and passes data/callbacks down to child components.  
* **`Sidebar.js`:** Static navigation component. Changes the view state in the parent `App` component.  
* **`Dashboard.js`:** Renders the chart and widgets. Fetches its own GitHub data based on settings in `localStorage`.  
* **`TechnologyRadar.js`:** Renders the technology cards grouped by domain. Handles the "Start Research" action.  
* **`ResearchHub.js`:** The most complex component. Manages its own state for file uploads, AI analysis results, and user notes. Interacts with three different API endpoints (`/upload`, `/generate-analysis`, `/add-to-rag`).  
* **`KnowledgeBase.js`:** Manages search term state and displays the filtered list of RAG entries.  
* **`Settings.js`:** A simple form component that reads from and writes to `localStorage`.

### **2.7. Key Workflow Logic: Research Lifecycle**

1. **Discovery:** A technology exists in `db.json` with `status: "research"`.  
2. **Initiation:** User clicks "Start Research Task" on the Technology Radar. The `App` component sets `activeResearchTask` and changes the view to `researchHub`.  
3. **Grounding (Optional):** In the `ResearchHub`, the user uploads a document. The frontend sends it to `/api/upload-research`. The backend saves the file and returns its new, unique filename.  
4. **Analysis (Optional):** The user clicks "Generate Analysis." The frontend sends the technology object and the unique filename to `/api/generate-grounded-analysis`. The backend reads the file, constructs a prompt, simulates the AI call, and returns the analysis text.  
5. **Documentation:** The user adds their own notes in the textarea.  
6. **Finalization:** The user clicks "Finalize & Add to Knowledge Base." The frontend sends the technology ID, title, and the combined notes/analysis to `/api/add-to-rag`. The backend updates `db.json` (changing status to `beta` and adding the `ragLink`) and creates the final `.md` file in the knowledge base.  
7. **Completion:** The `App` component refreshes all its data, the task is cleared, and the user can see the updated status on the Radar and the new entry in the Knowledge Base.


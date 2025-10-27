Pull Request 1: DevOps Refactoring (Ready for Review)

  Branch: feature/devops-refactor
  Title: refactor(devops): Overhaul Docker, CI, and Dependencies

  Description:

    1 ### Summary
    2 This pull request addresses key findings from the technical review related to DevOps and project infrastructure.
      It introduces a more robust, secure, and efficient build and deployment process.
    3 
    4 ### Changes
    5 - **CI/CD Pipeline (`.github/workflows/ci.yml`):**
    6     - Hardened the CI workflow to fail builds on failed tests.
    7     - Introduced `requirements-dev.txt` to separate build-time and run-time dependencies.
    8 - **Docker (`backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`):**
    9     - Implemented multi-stage builds in both backend and frontend Dockerfiles to reduce final image size.
   10     - Refactored `docker-compose.yml` to be more DRY by using YAML anchors and aliases.
   11     - Standardized service names and container names.
   12 - **Dependencies (`backend/requirements.txt`):**
   13     - Replaced `psycopg2-binary` with `psycopg2` to avoid potential production issues.
   14     - Upgraded `PyGithub` to the latest version to patch a security vulnerability.
   15 - **Bug Fixes:**
   16     - Resolved multiple application startup errors related to missing dependencies and incorrect Python imports.
   17 
   18 ### Verification
   19 - The entire application stack builds and runs successfully using `docker compose up --build`.
   20 - The CI pipeline now correctly fails when tests fail.

  ---

  Pull Request 2: Backend Refactoring (Draft)

  Branch: feature/backend-refactor
  Title: refactor(backend): Fix DB Session Bug and Implement Repository Pattern

  Description:

    1 ### Summary
    2 This pull request addresses critical backend issues identified during the technical review. It fixes a potential
      data loss bug and refactors the data access layer for better maintainability.
    3 
    4 **Note:** This is a draft PR. The core logic is implemented, but local test verification was blocked by 
      persistent Python environment issues.
    5 
    6 ### Changes
    7 - **Data Integrity (`backend/app/database.py`):**
    8     - Refactored the `get_db` dependency to ensure the database session is committed *before* it is closed. This
      resolves a critical bug that could lead to silent data loss on exceptions.
    9 - **Repository Pattern (`backend/app/repositories/`):**
   10     - Created a generic `BaseRepository` to encapsulate common CRUD (Create, Read, Update, Delete) operations.
   11     - Refactored `RepositoryRepository`, `ResearchTaskRepository`, and `TechnologyRepository` to inherit from 
      the `BaseRepository`, significantly reducing code duplication.
   12 - **Testing Environment:**
   13     - Created `requirements-test.txt` to isolate the minimal dependencies required for running the test suite, 
      bypassing local compilation errors.
   14 
   15 ### Blockers
   16 - The `pytest` suite could not be run successfully due to persistent issues with compiling Python dependencies (
      `psycopg2`, `asyncpg`, `lxml`) on macOS with Python 3.13. Further investigation is required to establish a 
      stable local testing environment.
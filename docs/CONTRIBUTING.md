# Contributing to Command Center

Thank you for your interest in contributing to Command Center! This guide will help you get started with development and understand our contribution process.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Development Workflow](#development-workflow)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. By participating in this project, you agree to:

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Accept responsibility and apologize when needed
- Prioritize what's best for the community

Report unacceptable behavior to the project maintainers.

---

## Getting Started

### Before You Begin

1. **Search existing issues** - Your idea or bug may already be reported
2. **Check the roadmap** - See if your feature aligns with project direction
3. **Discuss major changes** - Open an issue to discuss significant changes before coding

### Ways to Contribute

- **Bug Reports** - Report issues you encounter
- **Feature Requests** - Suggest new features or improvements
- **Code Contributions** - Submit bug fixes or new features
- **Documentation** - Improve guides, API docs, or examples
- **Testing** - Help test new features or releases
- **Code Review** - Review pull requests

---

## Development Setup

### Prerequisites

- **Python 3.11+** - Backend development
- **Node.js 18+** - Frontend development
- **Docker & Docker Compose** - Container orchestration
- **Git** - Version control
- **PostgreSQL 16** - Database (via Docker)

### Initial Setup

1. **Fork the repository**

   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/CommandCenter.git
   cd CommandCenter

   # Add upstream remote
   git remote add upstream https://github.com/PerformanceSuite/CommandCenter.git
   ```

2. **Backend setup**

   ```bash
   cd backend

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies

   # Set up environment
   cp ../.env.template ../.env
   # Edit .env with your configuration
   ```

3. **Frontend setup**

   ```bash
   cd frontend

   # Install dependencies
   npm install

   # Set up environment
   cp .env.template .env.local
   # Edit .env.local if needed
   ```

4. **Database setup**

   ```bash
   # Start PostgreSQL via Docker
   docker-compose up -d postgres redis

   # Run migrations
   cd backend
   alembic upgrade head
   ```

5. **Verify setup**

   ```bash
   # Start backend (from backend directory)
   uvicorn app.main:app --reload

   # Start frontend (from frontend directory, new terminal)
   npm run dev

   # Access application
   # Frontend: http://localhost:3000
   # Backend API: http://localhost:8000
   # API Docs: http://localhost:8000/docs
   ```

---

## Project Structure

```
CommandCenter/
├── backend/                 # FastAPI backend
│   ├── alembic/            # Database migrations
│   ├── app/
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API endpoints
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utility functions
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # Database setup
│   │   └── main.py         # Application entry point
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layer
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Utility functions
│   │   ├── types/          # TypeScript types
│   │   └── App.tsx         # Main application
│   └── tests/              # Frontend tests
│
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── docker-compose.yml      # Docker orchestration
└── .env.template           # Environment template
```

---

## Coding Standards

### Python (Backend)

**Style Guide:** PEP 8 with some modifications

```python
# Use type hints
def get_repository(repository_id: int, db: AsyncSession) -> Repository:
    """
    Get repository by ID

    Args:
        repository_id: The repository ID
        db: Database session

    Returns:
        Repository object

    Raises:
        HTTPException: If repository not found
    """
    pass

# Use docstrings for all functions, classes, modules
# Prefer explicit over implicit
# Use async/await for I/O operations
```

**Code Formatting:**

```bash
# Install formatters
pip install black isort mypy

# Format code
black .
isort .

# Type check
mypy app/
```

**Linting:**

```bash
# Install linter
pip install ruff

# Run linter
ruff check .
```

### TypeScript/React (Frontend)

**Style Guide:** Airbnb style guide with TypeScript

```typescript
// Use TypeScript strict mode
// Define types for all props and state
interface RepositoryCardProps {
  repository: Repository;
  onSync: (id: number) => Promise<void>;
}

export const RepositoryCard: React.FC<RepositoryCardProps> = ({
  repository,
  onSync,
}) => {
  // Use functional components and hooks
  // Prefer const over let
  // Use descriptive variable names
};
```

**Code Formatting:**

```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

### General Guidelines

- **Naming Conventions:**
  - Python: `snake_case` for functions/variables, `PascalCase` for classes
  - TypeScript: `camelCase` for functions/variables, `PascalCase` for components/types
  - Files: Match the primary export (e.g., `RepositoryCard.tsx`, `repository_service.py`)

- **Comments:**
  - Explain "why", not "what"
  - Keep comments up-to-date
  - Use docstrings for public APIs

- **Error Handling:**
  - Use specific exception types
  - Provide helpful error messages
  - Log errors appropriately

---

## Development Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Create bugfix branch
git checkout -b fix/issue-description

# Create docs branch
git checkout -b docs/what-youre-documenting
```

**Branch Naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements
- `chore/` - Maintenance tasks

### Keep Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Update your main branch
git checkout main
git merge upstream/main

# Rebase your feature branch
git checkout feature/your-feature-name
git rebase main
```

### Running Development Servers

**Backend:**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm run dev
```

**Full Stack (Docker):**

```bash
docker-compose up --build
```

---

## Testing Guidelines

### Backend Testing

**Framework:** pytest

```python
# tests/test_repositories.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_repository(client: AsyncClient):
    """Test repository creation"""
    response = await client.post(
        "/api/v1/repositories",
        json={
            "owner": "test-owner",
            "name": "test-repo",
            "description": "Test repository"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "test-owner/test-repo"
```

**Run Tests:**

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_repositories.py::test_create_repository

# Run with verbose output
pytest -v
```

### Frontend Testing

**Frameworks:** Vitest, React Testing Library

```typescript
// src/components/__tests__/RepositoryCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { RepositoryCard } from '../RepositoryCard';

describe('RepositoryCard', () => {
  it('renders repository information', () => {
    const repository = {
      id: 1,
      full_name: 'test/repo',
      description: 'Test repository',
    };

    render(<RepositoryCard repository={repository} />);
    expect(screen.getByText('test/repo')).toBeInTheDocument();
  });
});
```

**Run Tests:**

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### Testing Requirements

- **Unit tests** for all new functions/methods
- **Integration tests** for API endpoints
- **Component tests** for React components
- **Maintain >80% coverage** for new code
- **Test edge cases** and error conditions

---

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Test additions or updates
- `chore`: Build process or auxiliary tool changes
- `perf`: Performance improvements

### Examples

```bash
# Feature
git commit -m "feat(repositories): add GitHub sync endpoint"

# Bug fix
git commit -m "fix(api): handle null values in repository metadata"

# Documentation
git commit -m "docs(api): add examples for authentication endpoints"

# Breaking change
git commit -m "feat(api)!: change repository schema structure

BREAKING CHANGE: Repository metadata field renamed to metadata_"
```

### Guidelines

- Use present tense: "add feature" not "added feature"
- Use imperative mood: "move cursor" not "moves cursor"
- Keep subject line under 72 characters
- Reference issues: "fix(api): resolve issue #123"
- Explain "why" in the body for complex changes

---

## Pull Request Process

### Before Submitting

1. **Update your branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**
   ```bash
   # Backend
   cd backend && pytest

   # Frontend
   cd frontend && npm test
   ```

3. **Lint and format**
   ```bash
   # Backend
   black . && isort . && ruff check .

   # Frontend
   npm run lint && npm run format
   ```

4. **Update documentation** if needed

### Creating Pull Request

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**
   - Use the PR template
   - Link related issues
   - Provide clear description
   - Add screenshots for UI changes

3. **PR Template**

   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Related Issues
   Fixes #123

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated
   - [ ] Tests pass locally

   ## Screenshots (if applicable)
   ```

### Review Process

1. **Automated checks** must pass (linting, tests, build)
2. **Code review** by at least one maintainer
3. **Address feedback** promptly
4. **Squash commits** if requested
5. **Maintainer merges** once approved

### After Merge

1. **Delete your branch**
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your fork**
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

---

## Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What should happen

**Screenshots**
If applicable

**Environment:**
- OS: [e.g., macOS 13.0]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 1.0.0]

**Additional context**
Any other information
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
Clear description of desired solution

**Describe alternatives you've considered**
Alternative solutions or features

**Additional context**
Mockups, examples, or references
```

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation improvement
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority: high` - High priority
- `priority: low` - Low priority
- `wontfix` - Won't be fixed

---

## Documentation

### What to Document

- **API changes** - Update API.md
- **New features** - Update README.md and feature docs
- **Configuration changes** - Update CONFIGURATION.md
- **Architecture changes** - Update ARCHITECTURE.md
- **Breaking changes** - Update CHANGELOG.md

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Keep examples up-to-date
- Use proper markdown formatting

### Where to Add Documentation

- **API Documentation:** `docs/API.md`
- **User Guides:** `docs/`
- **Code Comments:** Inline in source files
- **README:** High-level overview
- **Changelog:** Version history

---

## Community

### Getting Help

- **GitHub Discussions** - Ask questions, share ideas
- **GitHub Issues** - Report bugs, request features
- **Documentation** - Check docs first
- **Code Comments** - Read inline documentation

### Communication Guidelines

- Be respectful and professional
- Provide context and details
- Search before asking
- Help others when you can
- Follow up on your issues/PRs

---

## Development Tips

### Useful Commands

```bash
# Backend
make backend-shell    # Enter backend container
make backend-logs     # View backend logs
make db-migrate       # Run migrations
make db-shell         # PostgreSQL shell

# Frontend
make frontend-shell   # Enter frontend container
make frontend-logs    # View frontend logs

# Database
make db-reset         # Reset database
make db-backup        # Backup database
make db-restore       # Restore database

# Testing
make test             # Run all tests
make test-backend     # Backend tests only
make test-frontend    # Frontend tests only
```

### Debugging

**Backend:**
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use debugpy for VS Code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

**Frontend:**
```typescript
// Use browser DevTools
console.log('Debug info:', data);
debugger; // Breakpoint
```

### Performance

- **Backend:** Use async/await for I/O
- **Frontend:** Lazy load components, memoize expensive operations
- **Database:** Use indexes, optimize queries
- **API:** Implement caching, pagination

---

## Release Process

(For maintainers)

1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Tag version
7. Deploy to production

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

If you have questions not covered here:

1. Check existing documentation
2. Search GitHub issues
3. Ask in GitHub Discussions
4. Contact maintainers

Thank you for contributing to Command Center!

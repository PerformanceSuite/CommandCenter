# Contributing to CommandCenter

Thank you for contributing to CommandCenter! This guide will help you set up your development environment and understand our code quality standards.

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/PerformanceSuite/CommandCenter.git
   cd CommandCenter
   ```

2. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Set up backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

4. **Set up frontend**
   ```bash
   cd frontend
   npm install
   ```

5. **Start development environment**
   ```bash
   docker-compose up -d
   ```

## Code Quality Standards

### Python (Backend)

#### Formatting
We use **Black** for code formatting:
```bash
black app/
```
- Line length: 120 characters (configured)
- Pre-commit hook automatically formats code

#### Linting
We use **Flake8** for linting:
```bash
flake8 app/ \
  --max-line-length=120 \
  --exclude=__pycache__,migrations \
  --ignore=E203,W503,E501
```

**Rules:**
- ✅ No unused imports
- ✅ No undefined variables
- ✅ Proper exception handling (no bare `except:`)
- ✅ Boolean comparisons: Use `is True`/`is False`, not `== True`

#### Type Checking
We use **MyPy** for type checking:
```bash
mypy app/
```

**Configuration:** `backend/mypy.ini`
- Current baseline: 445 errors suppressed (see mypy.ini for details)
- **Goal:** Incrementally reduce suppressions
- All new code should have proper type hints
- See issues #78, #79, #80 for improvement tasks

**Type hints required:**
- All function parameters and return types
- Class attributes (use `Mapped[]` for SQLAlchemy models)
- Variables in complex expressions

**Example:**
```python
# Good
def get_user(user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

# Bad (missing types)
def get_user(user_id):
    return db.query(User).filter(User.id == user_id).first()
```

### JavaScript/TypeScript (Frontend)

#### Linting
We use **ESLint**:
```bash
npm run lint
```

#### Type Checking
We use **TypeScript**:
```bash
npm run type-check
```

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit:
- ✅ Black formatting
- ✅ Flake8 linting
- ✅ MyPy type checking
- ✅ Trailing whitespace removal
- ✅ YAML validation
- ✅ Large file detection

**To bypass hooks** (not recommended):
```bash
git commit --no-verify
```

## CI/CD Pipeline

All PRs must pass CI checks:
- ✅ Black formatting check
- ✅ Flake8 linting (0 errors required)
- ✅ MyPy type checking (configured baseline)
- ✅ Bandit security scanning
- ✅ Safety dependency scanning
- ✅ Backend tests (pytest)
- ✅ Frontend tests (Vitest)
- ✅ Docker build verification

## Making Changes

### Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks locally**
   ```bash
   # Backend
   black app/
   flake8 app/
   mypy app/
   pytest

   # Frontend
   npm run lint
   npm run type-check
   npm test
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: Add awesome feature"
   ```
   Pre-commit hooks will run automatically.

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   gh pr create
   ```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): Add user authentication endpoint
fix(ui): Resolve layout issue in dashboard
docs: Update API documentation
```

## Testing

### Backend Tests
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest -k test_name            # Run specific test
pytest --cov=app               # With coverage
```

### Frontend Tests
```bash
npm test                        # Run tests in watch mode
npm test -- --run              # Run once
npm test -- --coverage         # With coverage
```

## MyPy Error Suppressions

Our MyPy configuration (`backend/mypy.ini`) documents known type errors. When working on code with suppressions:

1. **Check mypy.ini** for documented issues in your file
2. **Fix errors** when possible instead of adding suppressions
3. **Document** why suppressions are needed (with comments)
4. **Update mypy.ini** when removing suppressions

**Priority for fixes:**
1. `call-arg` errors (potential runtime bugs)
2. `attr-defined` errors (incorrect attribute access)
3. `var-annotated` errors (missing type hints)

See issues for specific improvement tasks:
- Issue #78: Repository generic type handling
- Issue #79: Variable type annotations
- Issue #80: Service schema/signature mismatches

## Getting Help

- **Documentation:** Check `/docs` directory
- **Issues:** Search existing issues or create a new one
- **Discussions:** Use GitHub Discussions for questions
- **Code Review:** Request review from maintainers

## Code Review Process

All PRs require:
- ✅ Passing CI checks
- ✅ Code review approval
- ✅ No merge conflicts
- ✅ Updated documentation (if needed)
- ✅ Tests for new features

**Review focus:**
- Code correctness
- Test coverage
- Type safety
- Security considerations
- Performance implications

## License

By contributing, you agree that your contributions will be licensed under the project's license.

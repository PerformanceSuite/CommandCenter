# Pull Request

## Description

Brief description of the changes in this PR.

## Type of Change

Please delete options that are not relevant:

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test additions or updates
- [ ] Configuration/infrastructure changes

## Related Issues

Fixes #(issue number)
Closes #(issue number)
Related to #(issue number)

## Changes Made

Please describe the changes in detail:

### Backend Changes

- [ ] API endpoints added/modified
- [ ] Database models updated
- [ ] Services/business logic changes
- [ ] Dependencies updated

**Details:**
- ...

### Frontend Changes

- [ ] New components added
- [ ] Existing components modified
- [ ] Pages added/updated
- [ ] Styling changes
- [ ] Dependencies updated

**Details:**
- ...

### Database Changes

- [ ] New migrations created
- [ ] Schema changes
- [ ] Data migrations required

**Migration commands:**
```bash
alembic upgrade head
```

### Documentation Changes

- [ ] README updated
- [ ] API documentation updated
- [ ] Architecture documentation updated
- [ ] Deployment guide updated
- [ ] Code comments added
- [ ] Other documentation updated

## Testing

### Test Coverage

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] End-to-end tests added/updated
- [ ] Manual testing completed

### Testing Steps

Please describe the tests you ran to verify your changes:

1. Test case 1
2. Test case 2
3. Test case 3

### Test Results

```bash
# Backend tests
pytest --cov=app

# Frontend tests
npm test
```

**Coverage:** X%

## Screenshots

If applicable, add screenshots to demonstrate the changes:

### Before

![Before](url)

### After

![After](url)

## Breaking Changes

Does this PR introduce any breaking changes?

- [ ] Yes (please describe below)
- [ ] No

**If yes, describe the breaking changes and migration path:**

## Deployment Notes

Any special deployment considerations:

- [ ] Requires environment variable changes
- [ ] Requires database migrations
- [ ] Requires data backups before deployment
- [ ] Requires service restarts
- [ ] Other: ___________

**Environment variables to add/update:**
```bash
NEW_VAR=value
```

**Deployment steps:**
1. Step 1
2. Step 2

## Performance Impact

Does this change affect performance?

- [ ] Yes, improves performance
- [ ] Yes, may reduce performance
- [ ] No significant impact
- [ ] Not applicable

**If yes, please describe:**

## Security Considerations

Does this change affect security?

- [ ] Yes (please describe below)
- [ ] No

**If yes, describe the security implications:**

## Checklist

### Code Quality

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings or errors
- [ ] I have checked for and fixed any linting issues

### Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested the changes in a development environment

### Documentation

- [ ] I have updated the documentation accordingly
- [ ] I have updated the API documentation if applicable
- [ ] I have added/updated code comments where necessary

### Dependencies

- [ ] I have checked that no unnecessary dependencies were added
- [ ] All new dependencies are documented and justified
- [ ] I have updated requirements.txt or package.json if needed

### Database

- [ ] I have created database migrations if schema changed
- [ ] Migrations have been tested (up and down)
- [ ] I have considered backward compatibility

### Git

- [ ] My commits are clear and follow the conventional commit format
- [ ] I have rebased on the latest main branch
- [ ] I have resolved all merge conflicts

## Additional Notes

Any additional information that reviewers should know:

---

## Reviewer Checklist

For maintainers reviewing this PR:

- [ ] Code quality is acceptable
- [ ] Tests are comprehensive and passing
- [ ] Documentation is complete and accurate
- [ ] No security issues identified
- [ ] Performance impact is acceptable
- [ ] Breaking changes are properly documented
- [ ] Deployment plan is clear
- [ ] All CI/CD checks are passing

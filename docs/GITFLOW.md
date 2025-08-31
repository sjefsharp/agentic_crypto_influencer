# Gitflow Branching Strategy

This repository uses a modern Gitflow branching strategy for organized development and releases.

## Branch Structure

```
main (production)
├── develop (development)
│   ├── feature/* (feature branches)
│   ├── hotfix/* (hotfix branches)
│   └── release/* (release branches)
```

## Branches

### `main`

- **Purpose**: Production-ready code
- **Protection**: Strictly protected
- **Merge**: Only via Pull Requests from `develop` or `release/*` branches
- **Triggers**: Automated releases and deployments

### `develop`

- **Purpose**: Integration branch for features
- **Protection**: Moderate protection
- **Merge**: Features are merged into this branch
- **Triggers**: CI/CD pipelines for testing

### `feature/*`

- **Purpose**: Develop new features
- **Naming**: `feature/description-of-feature`
- **Source**: Always from `develop`
- **Merge**: Back to `develop` via Pull Request

### `hotfix/*`

- **Purpose**: Fix critical bugs in production
- **Naming**: `hotfix/description-of-fix`
- **Source**: From `main`
- **Merge**: To `main` AND `develop`

### `release/*`

- **Purpose**: Release preparation and testing
- **Naming**: `release/v1.2.3`
- **Source**: From `develop`
- **Merge**: To `main` and `develop`

## Workflow

### New Feature

```bash
# 1. Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/amazing-new-feature

# 2. Develop feature
git add .
git commit -m "feat: add amazing new feature"

# 3. Push and create PR
git push origin feature/amazing-new-feature

# 4. Create PR to develop
# PR is automatically tested via CI
```

### Release Process

```bash
# 1. Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v1.2.3

# 2. Final testing and version bump
# CI/CD pipelines run full test suite

# 3. Merge to main (triggers production deployment)
git checkout main
git merge release/v1.2.3

# 4. Tag release
git tag v1.2.3
git push origin main --tags

# 5. Merge back to develop
git checkout develop
git merge release/v1.2.3
```

### Hotfix Process

```bash
# 1. Create hotfix branch
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# 2. Fix the bug
git add .
git commit -m "fix: critical bug in production"

# 3. Merge to main
git checkout main
git merge hotfix/critical-bug-fix
git tag v1.2.4
git push origin main --tags

# 4. Merge to develop
git checkout develop
git merge hotfix/critical-bug-fix
git push origin develop
```

## Commit Convention

Use [Conventional Commits](https://conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code styling (no functionality changes)
- `refactor`: Code refactoring
- `test`: Add/update tests
- `chore`: Maintenance tasks

### Examples:

```
feat: add user authentication
fix: resolve memory leak in data processor
docs: update API documentation
refactor: simplify algorithm complexity
```

## Pull Request Guidelines

### PR Title

- Follow conventional commit format
- Be descriptive but concise

### PR Description

- Describe what was changed
- Link to related issues
- Mention breaking changes
- Update CHANGELOG.md if needed

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] Coverage >= 80%

## Branch Protection Rules

### `main` Branch

- ✅ Require PR reviews (minimum 1)
- ✅ Require status checks (CI, tests, security)
- ✅ Require branches to be up to date
- ✅ Restrict pushes
- ✅ Include administrators

### `develop` Branch

- ✅ Require PR reviews (minimum 1)
- ✅ Require status checks (CI, tests)
- ✅ Require branches to be up to date

### Feature Branches

- ✅ Require PR for merge to develop
- ✅ CI checks must pass
- ✅ Code review required

## Automation

### GitHub Actions

- **CI**: Tests, linting, security scans on every push/PR
- **CD**: Automated releases and deployments
- **Security**: Daily security scans
- **Dependencies**: Weekly dependency updates

### Pre-commit Hooks

- Code formatting (Ruff)
- Linting (Ruff, MyPy, Bandit)
- Testing (Pytest with coverage)

## Tools & Integrations

- **Poetry**: Dependency management
- **Ruff**: Fast Python linter & formatter
- **MyPy**: Static type checking
- **Bandit**: Security linting
- **Codecov**: Code coverage reporting
- **Dependabot**: Automated dependency updates

## Troubleshooting

### Branch not up to date

```bash
git checkout your-branch
git fetch origin
git rebase origin/develop
```

### Merge conflicts

```bash
git checkout your-branch
git fetch origin
git rebase origin/develop
# Resolve conflicts in editor
git add resolved-files
git rebase --continue
```

### PR checks failing

- Check test results
- Fix linting errors
- Ensure sufficient test coverage
- Update dependencies if needed

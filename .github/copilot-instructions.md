# GitHub Copilot Instructions

## Project Standards and Guidelines

### Development Environment

- **Use Poetry** as the primary package manager for all dependency management, virtual environment handling, and script execution
- Always use `poetry run` prefix for executing commands (e.g., `poetry run pytest`, `poetry run mypy`)
- Maintain dependencies in `pyproject.toml` with proper version constraints

### Code Quality and Testing

- **Maintain 80% minimum test coverage** at all times
- Write proper unit tests using **stubs and mocks** - never test against live/active modules
- Use `unittest.mock` for mocking external dependencies, APIs, and database connections
- Ensure tests are isolated and don't rely on external services (Redis, APIs, etc.)
- Apply `lazy_connect=True` for database/service connections to prevent real connections during testing
- Follow pytest best practices with proper fixture management

### Version Control Workflow

- **Always attempt to commit changes via git** after making modifications
- Use descriptive commit messages that explain the purpose of changes
- Stage files with `git add .` before committing
- Commit frequently with logical, atomic changes

### Code Standards

- Follow **mypy strict mode** requirements - all code must pass mypy type checking
- Use explicit type annotations for all function parameters and return values
- Avoid `Any` types where possible - use specific type hints
- Handle mypy errors systematically, one at a time
- Use `# type: ignore[error-code]` only as a last resort with specific error codes

### Documentation

- **All code, README files, and error messages must be in English**
- Review and update README.md whenever making significant changes to:
  - Project structure
  - Installation procedures
  - Usage instructions
  - API endpoints
  - Configuration requirements
- Keep documentation current with actual implementation

### Pre-commit Hooks

- Ensure all pre-commit hooks pass before considering work complete:
  - `mypy` - Type checking with strict mode
  - `ruff` - Linting and formatting
  - `bandit` - Security scanning
  - `pytest` - Test execution with coverage requirements
- Fix issues systematically rather than in bulk to avoid introducing new errors

### Testing Best Practices

- Mock external dependencies (RedisHandler, API clients, file systems)
- Use proper test isolation - no shared state between tests
- Test edge cases and error conditions
- Maintain test readability with clear arrange-act-assert structure
- Use descriptive test names that explain what is being tested

### Error Handling

- Provide informative error messages in English
- Log errors appropriately with context
- Handle exceptions gracefully with proper error types
- Include relevant debugging information in error messages

### File Organization

- Maintain clean separation between source code (`src/`) and tests (`tests/`)
- Follow consistent naming conventions
- Keep imports organized and remove unused imports
- Use proper module structure with `__init__.py` files

These instructions should be followed consistently to maintain high code quality and project standards.

# Agentic Crypto Influencer

Automate crypto influencer tasks with Python, X (Twitter) API, and Google GenAI.

## 🚀 Quick Start

1. **Clone the repository:**

   ```sh
   git clone https://github.com/your-username/agentic-crypto-influencer.git
   cd agentic-crypto-influencer
   ```

2. **Setup Gitflow (first time only):**

   ```sh
   # Create develop branch
   git checkout -b develop
   git push -u origin develop

   # Setup pre-commit hooks
   poetry run pre-commit install
   ```

3. **Install dependencies:**

   ```sh
   poetry install
   ```

4. **Configure environment:**

   ```sh
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run pre-commit setup:**

   ```sh
   poetry run pre-commit install
   ```

6. **Start development:**
   ```sh
   poetry run python src/graphflow/graphflow.py
   ```

## 🏗️ Development Workflow

This project uses **Gitflow** branching strategy. See [docs/GITFLOW.md](docs/GITFLOW.md) for detailed workflow instructions.

### Quick Gitflow Commands

```bash
# Start a new feature
git checkout develop
git pull origin develop
git checkout -b feature/amazing-feature

# Create a release
git checkout develop
git checkout -b release/v1.0.0

# Hotfix for production
git checkout main
git checkout -b hotfix/critical-fix
```

### CI/CD Status

| Workflow        | Status                                                                                                               | Description                      |
| --------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| 🔄 CI           | ![CI](https://github.com/your-username/agentic-crypto-influencer/workflows/CI/badge.svg)                             | Tests, linting, security scans   |
| 🚀 CD           | ![CD](https://github.com/your-username/agentic-crypto-influencer/workflows/CD/badge.svg)                             | Automated releases & deployments |
| 🔒 Security     | ![Security](https://github.com/your-username/agentic-crypto-influencer/workflows/Security/badge.svg)                 | Daily security scans             |
| 📦 Dependencies | ![Dependencies](https://github.com/your-username/agentic-crypto-influencer/workflows/Dependency%20Updates/badge.svg) | Weekly dependency updates        |

## 📋 Configuration

### Environment Variables Setup

1. **Copy the example file:**

   ```sh
   cp .env.example .env
   ```

2. **Fill in your API keys in `.env`:**

   - **X (Twitter) API**: Get credentials from [X Developer Portal](https://developer.x.com/)
   - **Google API**: Get credentials from [Google Cloud Console](https://console.cloud.google.com/)
   - **Bitvavo API**: Get credentials from [Bitvavo](https://bitvavo.com/)
   - **Redis**: Default is `redis://localhost:6379`

3. **Verify your configuration:**

   ```sh
   python check_env.py
   ```

4. **Important Security Notes:**
   - Never commit the `.env` file to version control
   - The `.env` file is already in `.gitignore`
   - Share `.env.example` with team members (contains placeholder values)
   - Each developer should create their own `.env` file

### Required API Keys

- `X_API_CLIENT_ID`, `X_API_CLIENT_SECRET`, `X_API_KEY`, `X_API_SECRET`
- `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`, `X_BEARER_TOKEN`
- `GOOGLE_API_KEY`, `GOOGLE_GENAI_API_KEY`, `GOOGLE_CSE_ID`
- `BITVAVO_API_KEY`, `BITVAVO_API_SECRET`
- `REDIS_URL` (optional, defaults to localhost)

## Testing

- Tests are located in the `tests/` directory.
- Run all tests with coverage:
  ```sh
  poetry run pytest --cov=src/agentic_crypto_influencer --cov-report=html
  ```
- Minimum coverage requirement: **80%**

## 🔧 Code Quality & Automation

### Pre-commit Hooks

This project uses pre-commit hooks for automated code quality checks:

```bash
# Install hooks
poetry run pre-commit install

# Run on all files
poetry run pre-commit run --all-files

# Run specific hook
poetry run pre-commit run pytest --all-files
```

**Included hooks:**

- **pytest**: Tests with coverage checking
- **ruff**: Fast Python linter & formatter
- **mypy**: Static type checking
- **bandit**: Security linting
- **safety**: Dependency vulnerability scanning

### GitHub Actions Workflows

| Workflow          | Trigger                     | Purpose                          |
| ----------------- | --------------------------- | -------------------------------- |
| **CI**            | Push/PR to `main`/`develop` | Tests, linting, security scans   |
| **CD**            | Release tags                | Automated releases & deployments |
| **Security**      | Daily + Push/PR             | Security vulnerability scans     |
| **Dependencies**  | Weekly                      | Automated dependency updates     |
| **PR Automation** | PR events                   | PR validation & labeling         |

### Quality Gates

- ✅ **Test Coverage**: ≥ 80%
- ✅ **Code Quality**: Ruff, MyPy, Bandit
- ✅ **Security**: Safety, CodeQL, Dependency Review
- ✅ **PR Reviews**: Required for protected branches
- ✅ **Conventional Commits**: Enforced via PR titles

## 🔒 Security

## Cron jobs

- See instructions in README and code for automatic posting.

## Logging

- Logs are written to stdout by default. Adjust logging in the tools for more control.

## 📦 PyPI Publishing

This project supports automated PyPI publishing through GitHub Actions. To set up publishing:

### Quick Setup

1. **Get PyPI API tokens:**

   - Test PyPI: https://test.pypi.org/manage/account/
   - Production PyPI: https://pypi.org/manage/account/
   - Create tokens with "Entire account" scope

2. **Configure Poetry:**

   ```bash
   # Configure Test PyPI (recommended first)
   poetry config repositories.testpypi https://test.pypi.org/legacy/
   poetry config pypi-token.testpypi YOUR_TEST_TOKEN

   # Configure Production PyPI
   poetry config pypi-token.pypi YOUR_PRODUCTION_TOKEN
   ```

3. **Test publishing:**

   ```bash
   # Test with Test PyPI first
   poetry publish -r testpypi

   # If successful, publish to production
   poetry publish
   ```

### Manual Setup

#### 1. Get PyPI API Token

- Go to [PyPI Account Settings](https://pypi.org/manage/account/)
- Navigate to "API tokens"
- Create a new token with "Entire account" scope
- **Save the token securely** (you won't see it again!)

#### 2. Configure GitHub Secrets

Choose one of these methods:

**Option A: GitHub Web Interface**

- Go to your repository → Settings → Secrets and variables → Actions
- Click "New repository secret"
- Name: `PYPI_API_TOKEN`
- Value: Your PyPI API token
- Click "Add secret"

**Option B: GitHub CLI**

```bash
gh auth login
gh secret set PYPI_API_TOKEN
# Enter your token when prompted
```

#### 3. Test the Setup

```bash
# Test with Test PyPI first (recommended)
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi YOUR_TEST_TOKEN
poetry publish -r testpypi

# If successful, configure for production
poetry config pypi-token.pypi YOUR_PRODUCTION_TOKEN
poetry publish
```

### Automated Publishing

Once secrets are configured, publishing happens automatically:

- **Trigger**: Push to `main` branch or manual workflow dispatch
- **Process**: Version bump → Build → Test → Publish to PyPI
- **Result**: Package available on [PyPI](https://pypi.org/)

### Publishing Workflows

| Workflow           | Trigger           | Action                         |
| ------------------ | ----------------- | ------------------------------ |
| **Release**        | Push to `main`    | Full release with PyPI publish |
| **Manual Release** | Workflow dispatch | Custom version bump + publish  |

### Security Best Practices

- 🔐 **Never commit tokens** to version control
- 🔄 **Rotate tokens** regularly
- 🧪 **Test on Test PyPI** before production
- 👥 **Use scoped tokens** when possible
- 📝 **Document token usage** for team members

## 🤝 Contributing

We welcome contributions! Please follow our Gitflow workflow and contribution guidelines.

### Development Process

1. **Choose the right branch type:**

   - `feature/*` for new features
   - `hotfix/*` for critical production fixes
   - `release/*` for release preparation

2. **Follow conventional commits:**

   ```bash
   git commit -m "feat: add user authentication"
   git commit -m "fix: resolve memory leak"
   git commit -m "docs: update API documentation"
   ```

3. **Create a Pull Request:**

   - Target the correct base branch (`develop` for features, `main` for hotfixes)
   - Fill out the PR template completely
   - Ensure all CI checks pass
   - Request review from maintainers

4. **Code Review Process:**
   - At least 1 approval required
   - All CI checks must pass
   - Coverage must be ≥ 80%
   - No critical security issues

### Branch Protection

| Branch      | Reviews | CI Required | Up-to-date  |
| ----------- | ------- | ----------- | ----------- |
| `main`      | ✅ 1+   | ✅ All      | ✅ Required |
| `develop`   | ✅ 1+   | ✅ Core     | ✅ Required |
| `feature/*` | ✅ 1+   | ✅ Core     | ✅ Required |

### Commit Types

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

### Getting Help

- 📖 **Documentation**: [docs/GITFLOW.md](docs/GITFLOW.md)
- 🐛 **Bug Reports**: Use [bug report template](.github/ISSUE_TEMPLATE/bug-report.md)
- ✨ **Feature Requests**: Use [feature request template](.github/ISSUE_TEMPLATE/feature-request.md)
- 💬 **Discussions**: GitHub Discussions for questions

---

Questions? Open an issue or contact the maintainer.

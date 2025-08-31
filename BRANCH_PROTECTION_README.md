# Branch Protection Setup

Dit document beschrijft hoe je branch protection rules kunt instellen voor dit Python project.

## Optie 1: Automatisch (Bash Script)

1. **GitHub Token verkrijgen:**
   - Ga naar https://github.com/settings/tokens
   - Genereer een nieuwe token met scopes: `repo`, `admin:repo_hook`
   - Kopieer de token

2. **Script uitvoeren:**
   ```bash
   export GITHUB_TOKEN=your_token_here
   ./setup_branch_protection.sh
   ```

## Optie 2: Handmatig via GitHub Web Interface

### Voor main branch:
1. Ga naar: https://github.com/sjefsharp/agentic_crypto_influencer/settings/branches
2. Klik op "Add rule"
3. Voer volgende instellingen in:

**Branch name pattern:** `main`

**Protect matching branches:**
- ✅ Require a pull request before merging
  - ✅ Require approvals (1)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - Status checks: `test`, `lint`, `security`
- ✅ Require linear history
- ✅ Include administrators
- ✅ Restrict pushes that create matching branches
- ✅ Allow force pushes: ❌ No
- ✅ Allow deletions: ❌ No

**Merge options:**
- ✅ Allow merge commits
- ✅ Allow squash merging  
- ✅ Allow rebase merging

### Voor develop branch:
Herhaal dezelfde stappen maar met branch name pattern: `develop`

## Toegepaste Rules

De branch protection rules zorgen voor:

1. **Code Review:** Elke PR moet minimaal 1 goedkeuring hebben
2. **CI/CD Checks:** Alle tests, linting en security checks moeten slagen
3. **Up-to-date Branches:** Branches moeten up-to-date zijn voordat ze gemerged kunnen worden
4. **Linear History:** Voorkomt merge commits die de geschiedenis complex maken
5. **Administrator Compliance:** Zelfs repository admins moeten zich aan de rules houden
6. **Security:** Voorkomt force pushes en deletions van protected branches

## Troubleshooting

Als het script niet werkt:
1. Controleer of je GitHub token de juiste scopes heeft
2. Controleer of je repository owner en naam correct zijn in het script
3. Probeer de handmatige setup via de web interface

## Status Checks

Zorg ervoor dat je GitHub Actions workflows de juiste namen hebben:
- `test` - voor unit tests
- `lint` - voor code linting  
- `security` - voor security scanning

Deze namen moeten overeenkomen met de status checks in de branch protection rules.

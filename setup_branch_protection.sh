#!/bin/bash

# GitHub Branch Protection Setup Script
# This script sets up branch protection rules for Python projects

echo "Setting up branch protection rules for main branch..."

# Get GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Please set GITHUB_TOKEN environment variable"
    echo "You can get a token from: https://github.com/settings/tokens"
    echo "Required scopes: repo, admin:repo_hook"
    exit 1
fi

# Repository details
OWNER="sjefsharp"
REPO="agentic_crypto_influencer"
BRANCH="main"

# Branch protection payload
PAYLOAD='{
  "required_status_checks": {
    "strict": true,
    "contexts": ["test", "lint", "security"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "dismissal_restrictions": {}
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_linear_history": true,
  "allow_merge_commit": true,
  "allow_squash_merge": true,
  "allow_rebase_merge": true
}'

# Make API call
echo "Applying branch protection to $BRANCH branch..."
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "$PAYLOAD" \
  "https://api.github.com/repos/$OWNER/$REPO/branches/$BRANCH/protection"

if [ $? -eq 0 ]; then
    echo "✅ Branch protection applied to $BRANCH"
else
    echo "❌ Failed to apply branch protection"
    exit 1
fi

# Also protect develop branch
BRANCH="develop"
echo "Applying branch protection to $BRANCH branch..."
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "$PAYLOAD" \
  "https://api.github.com/repos/$OWNER/$REPO/branches/$BRANCH/protection"

if [ $? -eq 0 ]; then
    echo "✅ Branch protection applied to $BRANCH"
else
    echo "❌ Failed to apply branch protection to $BRANCH"
fi

echo "Branch protection setup complete!"
echo ""
echo "Applied rules:"
echo "- Require PR reviews (1 reviewer)"
echo "- Require status checks to pass"
echo "- Require branches to be up to date"
echo "- Include administrators"
echo "- Require linear history"
echo "- Allow merge commits, squash, and rebase"

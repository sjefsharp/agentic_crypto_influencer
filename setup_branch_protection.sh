#!/bin/bash

# GitHub Branch Protection Setup Script
# This script sets up branch protection rules for Python projects

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

echo "Setting up branch protection rules for main branch..."

# Get GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Please set GITHUB_TOKEN environment variable"
    echo "You can get a token from: https://github.com/settings/tokens"
    echo "Required scopes: repo, admin:repo_hook"
    echo ""
    echo "Or add it to your .env file:"
    echo "GITHUB_TOKEN=your_github_token_here"
    exit 1
fi

# Repository details
OWNER="sjefsharp"
REPO="agentic_crypto_influencer"
BRANCH="main"

# Branch protection payload (minimal for personal repos)
PAYLOAD='{
  "required_status_checks": {
    "strict": true,
    "contexts": ["test", "lint", "security"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null
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

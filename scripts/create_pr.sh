#!/usr/bin/env bash
# Usage: ./scripts/create_pr.sh "feature/describe-change" "Short PR title"
set -e
BRANCH=${1:-feature/auto-changes}
TITLE=${2:-"Update prompt_qdrant_api and tests"}

echo "Creating branch $BRANCH"

git checkout -b "$BRANCH"

git add -A

git commit -m "$TITLE"

echo "Branch created and changes committed locally."

echo "To push and create a PR:" 

echo "  git push origin $BRANCH"

echo "Then open a PR on GitHub from $BRANCH into main/master with title:\n  $TITLE"

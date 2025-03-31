#!/bin/bash

# Install Git hooks script for CloudTrace
# This script links the pre-commit hook to the Git hooks directory

# Exit on error
set -e

echo "=== Installing Git hooks ==="

# Check if we're in the git repo
if [ ! -d .git ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Make the hooks executable
chmod +x .githooks/pre-commit

# Configure Git to use our hooks directory
git config core.hooksPath .githooks

echo "✓ Git hooks installed successfully"
echo ""
echo "The following hooks are now active:"
echo "- pre-commit: Runs code quality checks before each commit"
echo ""
echo "To bypass hooks temporarily, use git commit with --no-verify" 
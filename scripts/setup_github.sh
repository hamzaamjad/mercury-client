#!/bin/bash
# Setup script for connecting to GitHub repository

echo "Mercury Client - GitHub Setup"
echo "============================"
echo
echo "Please create a GitHub repository first at: https://github.com/new"
echo "Repository name: mercury-client"
echo
echo "After creating the repository, enter your GitHub username:"
read -p "GitHub username: " GITHUB_USER

# Add the remote
git remote add origin "https://github.com/${GITHUB_USER}/mercury-client.git"

# Verify remote was added
echo
echo "Remote added:"
git remote -v

echo
echo "To push your code to GitHub, run:"
echo "  git push -u origin main"
echo
echo "After pushing, your CI/CD pipeline will automatically run!"
echo "Check the Actions tab on GitHub to see the build status." 
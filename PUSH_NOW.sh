#!/bin/bash

echo "=============================================="
echo "Force Push Clean Git History"
echo "=============================================="
echo ""
echo "✅ All .md files (except README) removed from git history"
echo "✅ ROTATE_CREDENTIALS_NOW.md deleted"
echo "✅ .gitignore updated to prevent future .md commits"
echo ""
echo "Current commits to be pushed:"
git log --oneline origin/master..HEAD 2>/dev/null || git log --oneline | head -4
echo ""
echo "⚠️  WARNING: This will FORCE PUSH and rewrite history!"
echo ""
read -p "Ready to push? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted."
    exit 1
fi

echo ""
echo "🚀 Force pushing..."
git push --force origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Git history cleaned and pushed to GitHub"
    echo ""
    echo "⚠️  IMPORTANT: You still need to rotate Google OAuth credentials!"
    echo "   The credentials were exposed before we cleaned history."
    echo ""
else
    echo ""
    echo "❌ Push failed. You may need to authenticate first:"
    echo ""
    echo "Option 1 - GitHub CLI:"
    echo "  gh auth login"
    echo "  ./PUSH_NOW.sh"
    echo ""
    echo "Option 2 - SSH:"
    echo "  git remote set-url origin git@github.com:wanjau2/careerGenie.git"
    echo "  ./PUSH_NOW.sh"
    echo ""
    echo "Option 3 - Personal Access Token:"
    echo "  git remote set-url origin https://YOUR_TOKEN@github.com/wanjau2/careerGenie.git"
    echo "  ./PUSH_NOW.sh"
    echo ""
fi

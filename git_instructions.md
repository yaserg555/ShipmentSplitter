# Git Bash Instructions

I see you're already in the master branch. Here are the specific steps to fix the "src refspec main does not match any" error:

```bash
# Since you're already in the master branch, push to the master branch (not main)
git push -u origin master
```

If that still doesn't work, try these steps:

```bash
# 1. Make sure you've added the files
git add pdf_splitter.py requirements.txt README.md example.py .gitignore sample_shipment.csv git_instructions.md

# 2. Make sure you've committed the files
git commit -m "Initial commit: PDF Splitter by SKU"

# 3. Check your branch name
git branch

# 4. Push to the branch you're on (which appears to be master)
git push -u origin master
```

If you're still having issues, you might need to create the master branch on GitHub first:

1. Go to your GitHub repository: https://github.com/yaserg555/ShipmentSplitter
2. Click on the "main" branch dropdown (if it exists)
3. Type "master" in the search box
4. Click "Create branch: master from 'main'"

Then try pushing again:

```bash
git push -u origin master
```

Alternatively, you can rename your local branch to match GitHub's default:

```bash
# Rename your local master branch to main
git branch -m master main

# Then push to main
git push -u origin main

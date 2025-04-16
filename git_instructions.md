# Git Bash Instructions

## Changing Directory in Git Bash

In Git Bash, you can change directories using the `cd` command. However, Git Bash uses Unix-style paths with forward slashes (`/`) instead of Windows-style backslashes (`\`).

To navigate to your ShipmentSplitter directory:

```bash
# Navigate to the E: drive
cd /e/

# Navigate to the Developing directory
cd /e/Developing/

# Navigate to the ShipmentSplitter directory
cd /e/Developing/ShipmentSplitter/
```

You can also navigate directly to the ShipmentSplitter directory in one command:

```bash
cd /e/Developing/ShipmentSplitter/
```

## Git Commands to Initialize and Push to GitHub

Once you're in the ShipmentSplitter directory, you can run the following commands to initialize the repository and push to GitHub:

```bash
# Initialize the repository
git init

# Add all files
git add pdf_splitter.py requirements.txt README.md example.py .gitignore sample_shipment.csv git_instructions.md

# Commit the files
git commit -m "Initial commit: PDF Splitter by SKU"

# Add the GitHub repository as a remote
git remote add origin git@github.com:yaserg555/ShipmentSplitter.git

# Push the code to GitHub
git push -u origin master
```

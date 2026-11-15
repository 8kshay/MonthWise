# Decision log

## 2026-11-15 — Project folder
Decision: Project lives at C:\Users\Akshay\Desktop\APP project
Why: Akshay's choice
Approved by: Akshay

## 2026-11-15 — Push to GitHub, keep branch name master
Decision: Add remote origin https://github.com/8kshay/APP-Project.git (was empty) and push local branch master as is; no rename to main.
Why: No local change needed; a rename can still be done later if wanted.
Approved by: Akshay
Status (2026-11-15): remote added; first push failed (403: GitHub signed in as 7kshay, which has no write access to 8kshay/APP-Project). Not pushed yet.

## 2026-11-15 — Virtual environment
Decision: Create .venv in the project folder with `python -m venv .venv` (Python 3.14.6). No packages installed.
Why: Keeps any future approved packages (e.g. pytest) out of the main Python install.
Approved by: Akshay

## 2026-11-15 — GitHub CLI installed
Decision: Akshay installed GitHub CLI 2.104.0 via winget. Not signed in yet.
Why: Lets git sign in to GitHub through the GitHub CLI.
Approved by: Akshay (installed it directly)
Update: Akshay ran `gh auth login` and is signed in as 8kshay, with Git set to use gh for GitHub sign-in.

## 2026-11-15 — GitHub account
Decision: This project uses the 8kshay GitHub account only (never 7kshay or any other).
Why: Akshay's instruction
How: repo-only git setting credential.https://github.com.username = 8kshay. Git's sign-in still goes through Git Credential Manager (system setting `credential.helper manager`), not gh; gh is signed in as 8kshay separately.
Approved by: Akshay

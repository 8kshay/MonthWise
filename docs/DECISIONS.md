# Decision log

## 2026-11-15 — Project folder
Decision: Project lives at C:\Users\Akshay\Desktop\APP project
Why: Akshay's choice
Approved by: Akshay

## 2026-11-15 — Push to GitHub, keep branch name master
Decision: Add remote origin https://github.com/8kshay/APP-Project.git (was empty) and push local branch master as is; no rename to main.
Why: No local change needed; a rename can still be done later if wanted.
Approved by: Akshay
Status (2026-11-15): first push failed (403: Git signed in as 7kshay, which has no write access to 8kshay/APP-Project).
Resolved (2026-11-15): after `gh auth login` as 8kshay and the repo-only username setting, master was pushed successfully.

## 2026-11-15 — Virtual environment
Decision: Create .venv in the project folder with `python -m venv .venv` (Python 3.14.6). No packages installed.
Why: Keeps any future approved packages (e.g. pytest) out of the main Python install.
Approved by: Akshay

## 2026-11-15 — GitHub CLI installed
Decision: Akshay installed GitHub CLI 2.104.0 via winget.
Why: Lets git sign in to GitHub through the GitHub CLI.
Approved by: Akshay (installed it directly)
Update: Akshay ran `gh auth login` and is signed in as 8kshay. Git itself still signs in through Git Credential Manager, not gh.

## 2026-11-15 — GitHub account
Decision: This project uses the 8kshay GitHub account only (never 7kshay or any other).
Why: Akshay's instruction
How: repo-only git setting credential.https://github.com.username = 8kshay. Git's sign-in goes through Git Credential Manager (system setting `credential.helper manager`); gh is signed in as 8kshay separately.
Approved by: Akshay

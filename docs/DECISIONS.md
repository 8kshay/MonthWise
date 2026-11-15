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

## 2026-11-15 — The app: Monthwise expense tracker (single release, all features)
Decision: Build "Monthwise", an offline expense tracker, in one release (no staged versions). Currency: Indian Rupees (₹).
Features: add transactions (date, amount, debit/credit, category, note); transactions table with month filter, search, edit, delete; summary per month (in, out, net, per category, budget status); charts (category split for a month, monthly spending comparison); editable categories; monthly budgets per category; recurring transactions (monthly); CSV export and import; light/dark theme.
Layout: one window with tabs. Data in a SQLite file at %APPDATA%\Monthwise\monthwise.db so replacing the .exe never loses data.
Packages (installed into .venv only): sv-ttk (modern Windows 11 style theme), matplotlib (charts), pyinstaller (build Monthwise.exe). Tests use Python's built-in unittest (no pytest).
Why: Akshay's answers: expense tracking, simple to use, good looking, offline, must run as a .exe on another PC, everything in one go.
Approved by: Akshay
Notes: dates are typed and shown as DD-MM-YYYY; "Salary" was added to the starter categories for money in; amounts are stored as whole paise to avoid rounding errors.

## 2026-11-15 — Users: Demo and My data
Decision: A "User" dropdown at the top switches between two users, each with its own data file: Demo (generated sample data for showing the app, with a "Reset demo data" button in Settings → Data that regenerates 6 months up to today) and My data (starts blank). Only these two users for now. Theme and last-used user are app-wide (prefs.json). The existing monthwise.db (sample data plus Akshay's test entry) became the Demo user's data.
Why: Akshay wants a ready demo and a clean space to enter his own examples.
Approved by: Akshay (chose all recommended options)
Also: the month picker now drives the Add tab's totals, uses "‹ Prev" / "Next ›" buttons and the mouse wheel (Akshay reported it wasn't working).

## 2026-11-15 — Open issue: Smart App Control blocks the .exe
Finding: dist\Monthwise.exe builds correctly (all files verified inside it), but this PC has Windows Smart App Control turned On, and it blocked the unsigned .exe from starting ("An Application Control policy has blocked this file"). Other PCs with Smart App Control on will block it too.
Options (Akshay to decide):
1. Code-sign the .exe with a trusted certificate (paid; e.g. a code-signing certificate or Microsoft Trusted Signing). Works everywhere.
2. Turn Smart App Control off on the PC that runs it (Windows Security > App & browser control). Lowers protection; on some Windows versions it can't be turned back on without resetting Windows.
3. Run from source with Python on that PC (see README).
Status: open
Update (2026-11-15): Akshay chose a Desktop shortcut that runs the app from source (pythonw.exe main.py) for demos on this PC. The .exe is kept and still built by build.ps1; Smart App Control is left on; signing not decided.

## 2026-11-15 — Line chart: spending through the month
Decision: Charts tab gets a second page, "Through the month": a running total of money spent per day, with the chosen month (red) against the 3 months before it, in a marker-pen style on grid paper. Title uses the app's own font (Segoe UI).
Why: Akshay's request, based on a reference picture.
Approved by: Akshay

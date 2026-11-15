# Monthwise
An offline expense tracker for Windows. Amounts are in Indian Rupees (₹).

## What it does
- **Add**: record money out (debit) or money in (credit) with date, amount, category and a note. Enter saves.
- **Transactions**: every entry for the chosen month (or all months), search, sort by any column, edit, delete, export to CSV.
- **Summary**: money in, money spent, left over and transaction count, each compared with the previous month; spending per category against its monthly budget; the last 6 months side by side.
- **Charts**: a donut of where the month's money went, and spent vs received for the last 12 months.
- **Settings**: add, rename and delete categories; set monthly budgets; recurring entries (rent, salary, subscriptions) that add themselves each month; CSV export/import; where the data file lives.
- Light and dark theme (button at the top right). The month picker at the top drives every tab.

Data is saved in `%APPDATA%\Monthwise\monthwise.db`, so it survives replacing or moving the .exe.

## Run from source
```
.venv\Scripts\python.exe main.py
```
First-time setup on a new PC: `python -m venv .venv` then `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

## Tests
```
.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

## Build the .exe
```
powershell -ExecutionPolicy Bypass -File build.ps1
```
Runs the tests, then creates `dist\Monthwise.exe` (one file, ~40 MB, no Python needed on the other PC).

**Windows Smart App Control** blocks unsigned .exe files on PCs where it is turned on (it is on for the PC this was built on). See docs/DECISIONS.md for the options.

## Files
- `main.py`: starts the app
- `monthwise/`: `db.py` (saving/loading), `money.py`, `dates.py`, `csvio.py`, and `ui/` (one file per tab, plus theme and shared widgets)
- `tests/`: automated checks
- `assets/`: app icon (made by `tools/make_icon.py`)

See docs/DECISIONS.md for decisions.

"""All saving and loading. One SQLite file per user (see users.py for where they live)."""

import datetime as dt
import sqlite3
from pathlib import Path

from .dates import add_months, month_key, split_month

DEFAULT_CATEGORIES = ["Food", "Transport", "Rent", "Bills", "Shopping",
                      "Health", "Entertainment", "Salary", "Other"]
FALLBACK_CATEGORY = "Other"
KINDS = ("debit", "credit")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    name     TEXT PRIMARY KEY COLLATE NOCASE,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY,
    date         TEXT    NOT NULL,
    amount       INTEGER NOT NULL CHECK (amount > 0),
    kind         TEXT    NOT NULL CHECK (kind IN ('debit', 'credit')),
    category     TEXT    NOT NULL,
    note         TEXT    NOT NULL DEFAULT '',
    recurring_id INTEGER,
    created_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE TABLE IF NOT EXISTS budgets (
    category TEXT PRIMARY KEY COLLATE NOCASE,
    amount   INTEGER NOT NULL CHECK (amount > 0)
);
CREATE TABLE IF NOT EXISTS recurring (
    id           INTEGER PRIMARY KEY,
    day          INTEGER NOT NULL CHECK (day BETWEEN 1 AND 28),
    amount       INTEGER NOT NULL CHECK (amount > 0),
    kind         TEXT    NOT NULL CHECK (kind IN ('debit', 'credit')),
    category     TEXT    NOT NULL,
    note         TEXT    NOT NULL DEFAULT '',
    start_month  TEXT    NOT NULL,
    last_applied TEXT,
    active       INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _clean_name(name: str) -> str:
    cleaned = " ".join((name or "").split())
    if not cleaned:
        raise ValueError("Enter a category name.")
    if len(cleaned) > 40:
        raise ValueError("Category names can be at most 40 characters.")
    return cleaned


class Database:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.executescript(_SCHEMA)
            if self.conn.execute("PRAGMA user_version").fetchone()[0] == 0:
                self._insert_default_categories()
                self.conn.execute("PRAGMA user_version = 1")

    def _insert_default_categories(self):
        for position, name in enumerate(DEFAULT_CATEGORIES):
            self.conn.execute("INSERT OR IGNORE INTO categories(name, position) VALUES (?, ?)",
                              (name, position))

    def close(self):
        self.conn.close()

    def clear_all(self):
        """Remove every transaction, budget, recurring entry and custom category."""
        with self.conn:
            for table in ("transactions", "recurring", "budgets", "categories"):
                self.conn.execute(f"DELETE FROM {table}")
            self._insert_default_categories()

    # ---------- settings ----------
    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))

    # ---------- categories ----------
    def categories(self) -> list[str]:
        rows = self.conn.execute("SELECT name FROM categories ORDER BY position, name")
        return [r["name"] for r in rows]

    def _find_category(self, name):
        row = self.conn.execute(
            "SELECT name FROM categories WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
        return row["name"] if row else None

    def add_category(self, name) -> str:
        name = _clean_name(name)
        if self._find_category(name):
            raise ValueError(f"The category '{name}' already exists.")
        with self.conn:
            position = self.conn.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM categories").fetchone()[0]
            self.conn.execute("INSERT INTO categories(name, position) VALUES (?, ?)",
                              (name, position))
        return name

    def ensure_category(self, name) -> str:
        name = _clean_name(name)
        return self._find_category(name) or self.add_category(name)

    def rename_category(self, old, new) -> str:
        new = _clean_name(new)
        current = self._find_category(old)
        if not current:
            raise ValueError(f"The category '{old}' does not exist.")
        existing = self._find_category(new)
        if existing and existing.lower() != current.lower():
            raise ValueError(f"The category '{new}' already exists.")
        with self.conn:
            for table, column in (("categories", "name"), ("transactions", "category"),
                                  ("budgets", "category"), ("recurring", "category")):
                self.conn.execute(
                    f"UPDATE {table} SET {column} = ? WHERE {column} = ? COLLATE NOCASE",
                    (new, current))
        return new

    def category_usage(self, name) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE category = ? COLLATE NOCASE",
            (name,)).fetchone()[0]

    def delete_category(self, name):
        """Delete a category; its transactions and recurring entries move to 'Other'."""
        current = self._find_category(name)
        if not current:
            raise ValueError(f"The category '{name}' does not exist.")
        if current.lower() == FALLBACK_CATEGORY.lower():
            raise ValueError(f"'{FALLBACK_CATEGORY}' can't be deleted; it holds moved entries.")
        fallback = self.ensure_category(FALLBACK_CATEGORY)
        with self.conn:
            for table in ("transactions", "recurring"):
                self.conn.execute(
                    f"UPDATE {table} SET category = ? WHERE category = ? COLLATE NOCASE",
                    (fallback, current))
            self.conn.execute("DELETE FROM budgets WHERE category = ? COLLATE NOCASE", (current,))
            self.conn.execute("DELETE FROM categories WHERE name = ? COLLATE NOCASE", (current,))

    # ---------- transactions ----------
    def _validate(self, date, amount, kind, category):
        if not isinstance(date, dt.date):
            raise ValueError("Invalid date.")
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("The amount must be more than zero.")
        if kind not in KINDS:
            raise ValueError("Type must be debit or credit.")
        found = self._find_category(category)
        if not found:
            raise ValueError(f"Unknown category '{category}'.")
        return found

    def add_transaction(self, date, amount, kind, category, note="", recurring_id=None) -> int:
        category = self._validate(date, amount, kind, category)
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO transactions(date, amount, kind, category, note, recurring_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (date.isoformat(), amount, kind, category, (note or "").strip(), recurring_id))
        return cursor.lastrowid

    def update_transaction(self, tx_id, date, amount, kind, category, note=""):
        category = self._validate(date, amount, kind, category)
        with self.conn:
            self.conn.execute(
                "UPDATE transactions SET date = ?, amount = ?, kind = ?, category = ?, note = ? "
                "WHERE id = ?",
                (date.isoformat(), amount, kind, category, (note or "").strip(), tx_id))

    def delete_transaction(self, tx_id):
        with self.conn:
            self.conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))

    def get_transaction(self, tx_id):
        row = self.conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()
        return dict(row) if row else None

    def transactions(self, month=None, search="", limit=None) -> list[dict]:
        sql = "SELECT * FROM transactions WHERE 1 = 1"
        params = []
        if month:
            sql += " AND substr(date, 1, 7) = ?"
            params.append(month)
        if search.strip():
            sql += " AND (category LIKE ? OR note LIKE ?)"
            pattern = f"%{search.strip()}%"
            params += [pattern, pattern]
        sql += " ORDER BY date DESC, id DESC"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        return [dict(r) for r in self.conn.execute(sql, params)]

    def is_duplicate(self, date, amount, kind, category, note) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM transactions WHERE date = ? AND amount = ? AND kind = ? "
            "AND category = ? COLLATE NOCASE AND note = ? LIMIT 1",
            (date.isoformat(), amount, kind, category, (note or "").strip())).fetchone() is not None

    # ---------- reports ----------
    def month_totals(self, month) -> dict:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN kind = 'credit' THEN amount END), 0) AS income, "
            "       COALESCE(SUM(CASE WHEN kind = 'debit'  THEN amount END), 0) AS spent, "
            "       COUNT(*) AS count "
            "FROM transactions WHERE substr(date, 1, 7) = ?", (month,)).fetchone()
        return {"income": row["income"], "spent": row["spent"],
                "net": row["income"] - row["spent"], "count": row["count"]}

    def category_totals(self, month, kind="debit") -> list[tuple[str, int]]:
        rows = self.conn.execute(
            "SELECT category, SUM(amount) AS total FROM transactions "
            "WHERE substr(date, 1, 7) = ? AND kind = ? GROUP BY category ORDER BY total DESC",
            (month, kind))
        return [(r["category"], r["total"]) for r in rows]

    def monthly_totals(self, end_month, count=12) -> list[dict]:
        start = add_months(end_month, -(count - 1))
        rows = self.conn.execute(
            "SELECT substr(date, 1, 7) AS month, "
            "       SUM(CASE WHEN kind = 'credit' THEN amount ELSE 0 END) AS income, "
            "       SUM(CASE WHEN kind = 'debit'  THEN amount ELSE 0 END) AS spent "
            "FROM transactions WHERE substr(date, 1, 7) BETWEEN ? AND ? GROUP BY month",
            (start, end_month))
        found = {r["month"]: r for r in rows}
        result = []
        for i in range(count):
            key = add_months(start, i)
            row = found.get(key)
            income = row["income"] if row else 0
            spent = row["spent"] if row else 0
            result.append({"month": key, "income": income, "spent": spent,
                           "net": income - spent})
        return result

    def daily_spent(self, month) -> dict[int, int]:
        """Money out per day of the month: {day: paise}. Days with no spending are left out."""
        rows = self.conn.execute(
            "SELECT CAST(substr(date, 9, 2) AS INTEGER) AS day, SUM(amount) AS total "
            "FROM transactions WHERE substr(date, 1, 7) = ? AND kind = 'debit' GROUP BY day",
            (month,))
        return {r["day"]: r["total"] for r in rows}

    def months_with_data(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) AS month FROM transactions ORDER BY month DESC")
        return [r["month"] for r in rows]

    # ---------- budgets ----------
    def budgets(self) -> dict[str, int]:
        return {r["category"]: r["amount"]
                for r in self.conn.execute("SELECT category, amount FROM budgets")}

    def set_budget(self, category, amount):
        """Set a monthly spending limit for a category; amount None removes it."""
        found = self._find_category(category)
        if not found:
            raise ValueError(f"Unknown category '{category}'.")
        with self.conn:
            if amount is None:
                self.conn.execute("DELETE FROM budgets WHERE category = ? COLLATE NOCASE", (found,))
            else:
                if amount <= 0:
                    raise ValueError("The budget must be more than zero.")
                self.conn.execute(
                    "INSERT INTO budgets(category, amount) VALUES (?, ?) "
                    "ON CONFLICT(category) DO UPDATE SET amount = excluded.amount",
                    (found, amount))

    # ---------- recurring ----------
    def add_recurring(self, day, amount, kind, category, note, start_month) -> int:
        if not 1 <= int(day) <= 28:
            raise ValueError("The day must be between 1 and 28 (so it exists in every month).")
        category = self._validate(dt.date.today(), amount, kind, category)
        split_month(start_month)  # validates the format
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO recurring(day, amount, kind, category, note, start_month) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (int(day), amount, kind, category, (note or "").strip(), start_month))
        return cursor.lastrowid

    def recurring_rules(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM recurring ORDER BY day, id")]

    def set_recurring_active(self, rule_id, active: bool):
        with self.conn:
            self.conn.execute("UPDATE recurring SET active = ? WHERE id = ?",
                              (1 if active else 0, rule_id))

    def delete_recurring(self, rule_id):
        """Remove the rule. Entries it already created are kept."""
        with self.conn:
            self.conn.execute("DELETE FROM recurring WHERE id = ?", (rule_id,))

    def apply_recurring(self, today=None) -> int:
        """Create any recurring entries that are due up to today. Returns how many."""
        today = today or dt.date.today()
        current = month_key(today)
        created = 0
        with self.conn:
            rules = self.conn.execute("SELECT * FROM recurring WHERE active = 1").fetchall()
            for rule in rules:
                last = rule["last_applied"]
                month = add_months(last, 1) if last else rule["start_month"]
                while month <= current:
                    if month == current and today.day < rule["day"]:
                        break
                    year, mon = split_month(month)
                    self.conn.execute(
                        "INSERT INTO transactions(date, amount, kind, category, note, recurring_id) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (dt.date(year, mon, rule["day"]).isoformat(), rule["amount"],
                         rule["kind"], rule["category"], rule["note"], rule["id"]))
                    created += 1
                    last = month
                    month = add_months(month, 1)
                if last != rule["last_applied"]:
                    self.conn.execute("UPDATE recurring SET last_applied = ? WHERE id = ?",
                                      (last, rule["id"]))
        return created

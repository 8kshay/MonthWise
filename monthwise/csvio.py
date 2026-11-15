"""Export transactions to CSV and import them back (Excel opens these files)."""

import csv
from dataclasses import dataclass, field

from .dates import parse_date
from .money import parse_amount, to_plain

FIELDS = ["date", "type", "category", "amount", "note"]

_KIND_WORDS = {
    "debit": "debit", "dr": "debit", "out": "debit", "expense": "debit", "spent": "debit",
    "credit": "credit", "cr": "credit", "in": "credit", "income": "credit",
}


@dataclass
class ImportResult:
    imported: int = 0
    duplicates: int = 0
    errors: list = field(default_factory=list)


def export_csv(db, path, month=None) -> int:
    rows = list(reversed(db.transactions(month=month)))  # oldest first
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        for t in rows:
            writer.writerow([t["date"], t["kind"], t["category"], to_plain(t["amount"]), t["note"]])
    return len(rows)


def import_csv(db, path) -> ImportResult:
    """Import rows with columns date, amount and optionally type, category, note.

    Bad rows are skipped and reported; rows identical to an existing entry are skipped
    so importing the same file twice doesn't double-count.
    """
    result = ImportResult()
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            result.errors.append("The file is empty.")
            return result
        columns = {name.strip().lower(): name for name in reader.fieldnames if name}
        missing = [c for c in ("date", "amount") if c not in columns]
        if missing:
            result.errors.append("Missing column(s): " + ", ".join(missing)
                                 + ". The first row must name the columns: " + ", ".join(FIELDS))
            return result

        def cell(row, name):
            key = columns.get(name)
            return (row.get(key) or "").strip() if key else ""

        for line, row in enumerate(reader, start=2):
            try:
                date = parse_date(cell(row, "date"))
                amount = parse_amount(cell(row, "amount"))
                kind_text = cell(row, "type").lower() or "debit"
                kind = _KIND_WORDS.get(kind_text)
                if not kind:
                    raise ValueError(f"type '{kind_text}' should be debit or credit")
                category = db.ensure_category(cell(row, "category") or "Other")
                note = cell(row, "note")
            except ValueError as error:
                result.errors.append(f"Line {line}: {error}")
                continue
            if db.is_duplicate(date, amount, kind, category, note):
                result.duplicates += 1
                continue
            db.add_transaction(date, amount, kind, category, note)
            result.imported += 1
    return result

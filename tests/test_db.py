import datetime as dt
import os
import tempfile
import unittest

from monthwise.csvio import export_csv, import_csv
from monthwise.db import DEFAULT_CATEGORIES, Database

D = dt.date


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_default_categories(self):
        self.assertEqual(self.db.categories(), DEFAULT_CATEGORIES)

    def test_add_edit_delete_transaction(self):
        tx = self.db.add_transaction(D(2026, 11, 3), 50000, "debit", "food", " lunch ")
        saved = self.db.get_transaction(tx)
        self.assertEqual(saved["category"], "Food")  # matched case-insensitively
        self.assertEqual(saved["note"], "lunch")
        self.db.update_transaction(tx, D(2026, 11, 4), 60000, "debit", "Transport", "cab")
        self.assertEqual(self.db.get_transaction(tx)["amount"], 60000)
        self.db.delete_transaction(tx)
        self.assertIsNone(self.db.get_transaction(tx))

    def test_rejects_unknown_category_and_bad_kind(self):
        with self.assertRaises(ValueError):
            self.db.add_transaction(D(2026, 11, 3), 100, "debit", "Nope")
        with self.assertRaises(ValueError):
            self.db.add_transaction(D(2026, 11, 3), 100, "other", "Food")

    def test_totals_and_reports(self):
        self.db.add_transaction(D(2026, 10, 30), 100000, "debit", "Rent")
        self.db.add_transaction(D(2026, 11, 1), 5000000, "credit", "Salary")
        self.db.add_transaction(D(2026, 11, 2), 30000, "debit", "Food")
        self.db.add_transaction(D(2026, 11, 9), 20000, "debit", "Food")
        self.db.add_transaction(D(2026, 11, 9), 45000, "debit", "Bills")
        totals = self.db.month_totals("2026-11")
        self.assertEqual(totals, {"income": 5000000, "spent": 95000, "net": 4905000, "count": 4})
        self.assertEqual(self.db.category_totals("2026-11"), [("Food", 50000), ("Bills", 45000)])
        months = self.db.monthly_totals("2026-11", 3)
        self.assertEqual([m["month"] for m in months], ["2026-09", "2026-10", "2026-11"])
        self.assertEqual([m["spent"] for m in months], [0, 100000, 95000])
        self.assertEqual(self.db.months_with_data(), ["2026-11", "2026-10"])
        self.assertEqual(self.db.daily_spent("2026-11"), {2: 30000, 9: 65000})  # credits left out

    def test_search(self):
        self.db.add_transaction(D(2026, 11, 1), 100, "debit", "Food", "Pizza night")
        self.db.add_transaction(D(2026, 11, 2), 100, "debit", "Transport", "metro")
        self.assertEqual(len(self.db.transactions(search="pizza")), 1)
        self.assertEqual(len(self.db.transactions(search="transport")), 1)
        self.assertEqual(len(self.db.transactions(month="2026-10")), 0)

    def test_category_rename_and_delete(self):
        self.db.add_transaction(D(2026, 11, 1), 100, "debit", "Food")
        self.db.set_budget("Food", 500000)
        self.db.rename_category("Food", "Groceries")
        self.assertIn("Groceries", self.db.categories())
        self.assertEqual(self.db.budgets(), {"Groceries": 500000})
        self.assertEqual(self.db.transactions()[0]["category"], "Groceries")
        with self.assertRaises(ValueError):
            self.db.rename_category("Groceries", "rent")  # already exists
        self.db.delete_category("Groceries")
        self.assertEqual(self.db.transactions()[0]["category"], "Other")
        self.assertEqual(self.db.budgets(), {})
        with self.assertRaises(ValueError):
            self.db.delete_category("Other")
        with self.assertRaises(ValueError):
            self.db.add_category("  ")

    def test_budgets(self):
        self.db.set_budget("Food", 300000)
        self.db.set_budget("food", 400000)
        self.assertEqual(self.db.budgets(), {"Food": 400000})
        self.db.set_budget("Food", None)
        self.assertEqual(self.db.budgets(), {})

    def test_recurring(self):
        rule = self.db.add_recurring(5, 1500000, "debit", "Rent", "flat rent", "2026-09")
        # On 15 Nov: Sep, Oct and Nov are all due.
        self.assertEqual(self.db.apply_recurring(D(2026, 11, 15)), 3)
        self.assertEqual(self.db.apply_recurring(D(2026, 11, 15)), 0)  # no double entries
        dates = sorted(t["date"] for t in self.db.transactions())
        self.assertEqual(dates, ["2026-09-05", "2026-10-05", "2026-11-05"])
        self.db.set_recurring_active(rule, False)
        self.assertEqual(self.db.apply_recurring(D(2027, 1, 20)), 0)
        self.db.set_recurring_active(rule, True)
        self.assertEqual(self.db.apply_recurring(D(2027, 1, 4)), 1)  # Dec only; Jan not due yet
        with self.assertRaises(ValueError):
            self.db.add_recurring(31, 100, "debit", "Rent", "", "2026-11")

    def test_settings_and_file_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sub", "m.db")
            db = Database(path)
            db.set_setting("theme", "dark")
            db.add_transaction(D(2026, 11, 1), 100, "debit", "Food")
            db.close()
            db = Database(path)
            self.assertEqual(db.get_setting("theme"), "dark")
            self.assertEqual(len(db.transactions()), 1)
            self.assertEqual(db.categories(), DEFAULT_CATEGORIES)  # not re-added
            db.close()


class CsvTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.folder = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.db.close()
        self.folder.cleanup()

    def path(self, name):
        return os.path.join(self.folder.name, name)

    def test_round_trip_and_duplicates(self):
        self.db.add_transaction(D(2026, 11, 1), 12345, "debit", "Food", "tea, biscuits")
        self.db.add_transaction(D(2026, 11, 2), 5000000, "credit", "Salary")
        self.assertEqual(export_csv(self.db, self.path("out.csv")), 2)
        other = Database(":memory:")
        result = import_csv(other, self.path("out.csv"))
        self.assertEqual((result.imported, result.duplicates, result.errors), (2, 0, []))
        self.assertEqual(other.transactions()[1]["note"], "tea, biscuits")
        again = import_csv(other, self.path("out.csv"))
        self.assertEqual((again.imported, again.duplicates), (0, 2))
        other.close()

    def test_import_reports_bad_rows_and_creates_categories(self):
        with open(self.path("in.csv"), "w", encoding="utf-8") as handle:
            handle.write("Date,Amount,Type,Category,Note\n"
                         "15-11-2026,250,debit,Coffee,latte\n"
                         "not a date,10,debit,Food,\n"
                         "16-11-2026,-5,debit,Food,\n"
                         "17-11-2026,100,maybe,Food,\n"
                         "18-11-2026,1000,income,,\n")
        result = import_csv(self.db, self.path("in.csv"))
        self.assertEqual(result.imported, 2)
        self.assertEqual(len(result.errors), 3)
        self.assertTrue(result.errors[0].startswith("Line 3"))
        self.assertIn("Coffee", self.db.categories())
        self.assertEqual(self.db.month_totals("2026-11")["income"], 100000)

    def test_import_missing_columns(self):
        with open(self.path("bad.csv"), "w", encoding="utf-8") as handle:
            handle.write("when,how much\n1-1-2026,5\n")
        result = import_csv(self.db, self.path("bad.csv"))
        self.assertEqual(result.imported, 0)
        self.assertIn("Missing column", result.errors[0])


if __name__ == "__main__":
    unittest.main()

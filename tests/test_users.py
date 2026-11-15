import datetime as dt
import os
import tempfile
import unittest

from monthwise import demo
from monthwise.db import Database
from monthwise.users import UserStore


class UserStoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.folder.cleanup()

    def test_demo_gets_sample_data_and_mine_starts_blank(self):
        store = UserStore(self.folder.name)
        self.assertEqual(store.last_user(), "demo")
        demo_db = store.open("demo")
        self.assertGreater(len(demo_db.transactions()), 100)
        self.assertEqual(len(demo_db.recurring_rules()), 4)
        self.assertTrue(demo_db.budgets())
        count = len(demo_db.transactions())
        demo_db.close()
        demo_db = store.open("demo")  # not generated twice
        self.assertEqual(len(demo_db.transactions()), count)
        demo_db.close()

        mine = store.open("mine")
        self.assertEqual(mine.transactions(), [])
        self.assertEqual(mine.recurring_rules(), [])
        mine.close()
        self.assertEqual(UserStore(self.folder.name).last_user(), "mine")

    def test_prefs_survive_restart_and_bad_user_is_ignored(self):
        store = UserStore(self.folder.name)
        store.set_pref("theme", "dark")
        store.set_pref("user", "someone-else")
        again = UserStore(self.folder.name)
        self.assertEqual(again.get_pref("theme"), "dark")
        self.assertEqual(again.last_user(), "demo")
        with self.assertRaises(ValueError):
            again.path("someone-else")

    def test_old_single_file_becomes_demo(self):
        old = Database(os.path.join(self.folder.name, "monthwise.db"))
        old.add_transaction(dt.date(2026, 11, 1), 100000, "debit", "Food", "kept")
        old.set_setting("theme", "dark")
        old.close()
        store = UserStore(self.folder.name)
        self.assertFalse(os.path.exists(os.path.join(self.folder.name, "monthwise.db")))
        db = store.open("demo")
        notes = [t["note"] for t in db.transactions()]
        self.assertEqual(notes, ["kept"])  # existing data kept, no sample data mixed in
        self.assertEqual(store.get_pref("theme"), "dark")
        db.close()


class DemoDataTests(unittest.TestCase):
    def test_generate_covers_six_months_up_to_today(self):
        db = Database(":memory:")
        today = dt.date(2026, 11, 15)
        demo.generate(db, today)
        months = db.months_with_data()
        self.assertEqual(months[0], "2026-11")
        self.assertEqual(months[-1], "2026-06")
        self.assertTrue(all(t["date"] <= "2026-11-15" for t in db.transactions()))
        self.assertEqual(db.month_totals("2026-10")["income"] >= 8500000, True)
        db.close()

    def test_reset_replaces_everything(self):
        db = Database(":memory:")
        demo.generate(db, dt.date(2026, 11, 15))
        db.add_category("Pets")
        db.add_transaction(dt.date(2026, 11, 2), 500, "debit", "Pets", "mine")
        demo.reset(db, dt.date(2027, 3, 10))
        self.assertNotIn("Pets", db.categories())
        self.assertEqual(db.months_with_data()[0], "2027-03")
        self.assertEqual(db.months_with_data()[-1], "2026-10")
        self.assertEqual(len(db.recurring_rules()), 4)
        db.close()


if __name__ == "__main__":
    unittest.main()

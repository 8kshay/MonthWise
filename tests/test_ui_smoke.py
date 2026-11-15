"""Opens the real window (hidden) and drives it the way a user would."""

import datetime as dt
import os
import tempfile
import unittest

from monthwise.dates import add_months, format_date, month_key
from monthwise.users import UserStore


class UiSmokeTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.store = UserStore(self.folder.name)
        self.store.set_pref("user", "mine")  # start on the blank user
        from monthwise.ui.app import MonthwiseApp
        self.app = MonthwiseApp(self.store)
        self.app.withdraw()
        self.db = self.app.db

    def tearDown(self):
        self.app.db.close()
        self.app.destroy()
        self.folder.cleanup()

    def visit_all_tabs(self):
        for index in range(len(self.app.tabs)):
            self.app.notebook.select(index)
            self.app.update()

    def test_add_through_form_and_browse_everything(self):
        add_tab = self.app.tabs[0]
        form = add_tab.form
        form.amount.set("1,250.50")
        form.category.set("Food")
        form.note.set("Groceries")
        add_tab.save()
        txs = self.db.transactions()
        self.assertEqual(len(txs), 1)
        self.assertEqual((txs[0]["amount"], txs[0]["note"]), (125050, "Groceries"))
        self.assertEqual(form.amount.get(), "")  # cleared for the next entry

        form.amount.set("abc")
        add_tab.save()
        self.assertIn("number", add_tab.status.cget("text"))
        self.assertEqual(len(self.db.transactions()), 1)

        form.kind.set("credit")
        form.amount.set("50000")
        form.category.set("Salary")
        form.date.set(format_date(dt.date.today()))
        add_tab.save()
        self.assertEqual(self.db.month_totals(month_key(dt.date.today()))["income"], 5000000)

        self.db.set_budget("Food", 100000)
        self.db.add_recurring(1, 900000, "debit", "Rent", "rent", month_key(dt.date.today()))
        self.db.apply_recurring()
        self.app.refresh_all()
        self.visit_all_tabs()

        transactions = self.app.tabs[1]
        self.assertEqual(len(transactions.table.tree.get_children()), 3)
        transactions.search.set("groc")
        self.app.update()
        self.assertEqual(len(transactions.table.tree.get_children()), 1)
        transactions.table.sort_by("amount")

        summary = self.app.tabs[2]
        rows = {summary.categories.tree.set(i, "category"): summary.categories.tree.item(i, "tags")
                for i in summary.categories.tree.get_children()}
        self.assertIn("over", rows["Food"])  # ₹1,250.50 spent against a ₹1,000 budget

        self.app.month.set(add_months(self.app.month.get(), -1))
        self.visit_all_tabs()
        self.app.toggle_theme()
        self.visit_all_tabs()
        self.assertEqual(self.store.get_pref("theme"), "dark")
        self.app.toggle_theme()

    def test_month_picker_moves_every_tab(self):
        this_month = month_key(dt.date.today())
        last_month = add_months(this_month, -1)
        self.db.add_transaction(dt.date.fromisoformat(f"{last_month}-10"), 77700, "debit",
                                "Food", "last month")
        picker = self.app.month_picker
        self.assertEqual(picker.today_button.instate(["disabled"]), True)

        picker.prev_button.invoke()  # on the Add tab
        self.app.update()
        self.assertEqual(self.app.month.get(), last_month)
        add_tab = self.app.tabs[0]
        self.assertEqual(add_tab.stat_labels["spent"].cget("text"), "₹777.00")
        self.assertNotIn("so far", add_tab.month_caption.cget("text"))
        self.assertTrue(picker.today_button.instate(["!disabled"]))

        self.app.notebook.select(1)
        self.app.update()
        self.assertEqual(len(self.app.tabs[1].table.tree.get_children()), 1)

        picker.next_button.invoke()
        self.app.update()
        self.assertEqual(self.app.month.get(), this_month)
        self.assertEqual(len(self.app.tabs[1].table.tree.get_children()), 0)

        picker.event_generate("<MouseWheel>", delta=120)  # wheel up = earlier month
        self.app.update()
        self.assertEqual(self.app.month.get(), last_month)
        picker.today_button.invoke()
        self.assertEqual(self.app.month.get(), this_month)

    def test_switch_users(self):
        self.assertEqual(self.app.user, "mine")
        self.assertEqual(self.app.db.transactions(), [])
        self.assertIn("My data", self.app.title())
        self.app.user_var.set("Demo")
        self.app._user_chosen()
        self.assertEqual(self.app.user, "demo")
        self.assertGreater(len(self.app.db.transactions()), 100)
        self.visit_all_tabs()
        self.app.switch_user("mine")
        self.assertEqual(self.app.db.transactions(), [])
        self.assertEqual(self.store.last_user(), "mine")

    def test_dialogs_collect_values(self):
        from monthwise.ui.settings_tab import _parse_budget
        from monthwise.ui.widgets import RecurringDialog, TextDialog, TransactionDialog
        tx_id = self.db.add_transaction(dt.date(2026, 11, 2), 9950, "debit", "Food", "tea")
        dialog = TransactionDialog(self.app, self.db.categories(), self.db.get_transaction(tx_id))
        values = dialog.collect()
        self.assertEqual((values["amount"], values["date"], values["note"]),
                         (9950, dt.date(2026, 11, 2), "tea"))
        dialog.destroy()

        dialog = RecurringDialog(self.app, self.db.categories(), "2026-11")
        dialog.form.amount.set("22000")
        dialog.day.set("5")
        values = dialog.collect()
        self.assertEqual((values["day"], values["amount"], values["start_month"]),
                         (5, 2200000, "2026-11"))
        self.db.add_recurring(**values)
        dialog.destroy()

        dialog = TextDialog(self.app, "Budget", "Amount", initial="1500", parse=_parse_budget)
        self.assertEqual(dialog.collect(), 150000)
        dialog.value.set("")
        self.assertIsNone(dialog.collect())
        dialog.destroy()


if __name__ == "__main__":
    unittest.main()

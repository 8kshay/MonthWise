"""Settings tab: categories & budgets, recurring entries, data (import/export/location)."""

import os
from tkinter import filedialog, messagebox, ttk

from ..csvio import FIELDS, export_csv, import_csv
from ..dates import month_label
from ..money import format_inr, parse_amount, to_plain
from . import theme
from .widgets import PAD, RecurringDialog, Table, TextDialog


def _parse_budget(text):
    text = text.strip()
    return None if text in ("", "0") else parse_amount(text)


class SettingsTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=PAD)
        self.app = app
        inner = ttk.Notebook(self)
        inner.pack(fill="both", expand=True)
        inner.add(self._categories_page(inner), text="  Categories & budgets  ")
        inner.add(self._recurring_page(inner), text="  Recurring  ")
        inner.add(self._data_page(inner), text="  Data  ")

    # ---------- categories ----------
    def _categories_page(self, parent):
        page = ttk.Frame(parent, padding=PAD)
        ttk.Label(page, text="A budget is a monthly spending limit for a category. The Summary "
                             "tab shows how much of it is left.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 10))
        body = ttk.Frame(page)
        body.pack(fill="both", expand=True)
        self.cat_table = Table(body, [("name", "Category", 200, "w"),
                                      ("budget", "Monthly budget", 150, "e"),
                                      ("used", "Transactions", 110, "e")], height=12)
        self.cat_table.pack(side="left", fill="both", expand=True)
        self.cat_table.tree.bind("<Double-1>", lambda _e: self.set_budget())
        buttons = ttk.Frame(body, padding=(PAD, 0, 0, 0))
        buttons.pack(side="left", fill="y")
        for text, command, style in (("Add category…", self.add_category, "Accent.TButton"),
                                     ("Rename…", self.rename_category, "TButton"),
                                     ("Delete", self.delete_category, "TButton"),
                                     ("Set budget…", self.set_budget, "TButton"),
                                     ("Remove budget", self.clear_budget, "TButton")):
            ttk.Button(buttons, text=text, command=command, style=style,
                       width=16).pack(fill="x", pady=(0, 8))
        return page

    def _selected_category(self):
        name = self.cat_table.selected()
        if not name:
            messagebox.showinfo("Nothing selected", "Click a category in the list first.",
                                parent=self)
        return name

    def _run(self, action):
        try:
            action()
        except ValueError as error:
            messagebox.showerror("Can't do that", str(error), parent=self)
            return
        self.app.refresh_all()

    def add_category(self):
        name = TextDialog(self, "Add category", "Category name", ok_text="Add").show()
        if name is not None:
            self._run(lambda: self.app.db.add_category(name))

    def rename_category(self):
        old = self._selected_category()
        if not old:
            return
        new = TextDialog(self, "Rename category", f"New name for '{old}'", initial=old).show()
        if new is not None and new != old:
            self._run(lambda: self.app.db.rename_category(old, new))

    def delete_category(self):
        name = self._selected_category()
        if not name:
            return
        used = self.app.db.category_usage(name)
        extra = f"\n\nIts {used} transaction(s) will move to 'Other'." if used else ""
        if messagebox.askyesno("Delete category", f"Delete the category '{name}'?{extra}",
                               icon="warning", parent=self):
            self._run(lambda: self.app.db.delete_category(name))

    def set_budget(self):
        name = self._selected_category()
        if not name:
            return
        current = self.app.db.budgets().get(name)
        amount = TextDialog(self, "Monthly budget",
                            f"Monthly budget for '{name}' (₹). Leave empty to remove.",
                            initial=to_plain(current) if current else "",
                            parse=_parse_budget).show()
        if amount is not None or current:
            self._run(lambda: self.app.db.set_budget(name, amount))

    def clear_budget(self):
        name = self._selected_category()
        if name:
            self._run(lambda: self.app.db.set_budget(name, None))

    # ---------- recurring ----------
    def _recurring_page(self, parent):
        page = ttk.Frame(parent, padding=PAD)
        ttk.Label(page, text="Recurring entries (rent, salary, subscriptions) are added "
                             "automatically on their day each month when you open Monthwise.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 10))
        body = ttk.Frame(page)
        body.pack(fill="both", expand=True)
        self.rec_table = Table(body, [("day", "Day", 60, "e"), ("type", "Type", 80, "w"),
                                      ("category", "Category", 140, "w"),
                                      ("amount", "Amount", 120, "e"), ("note", "Note", 200, "w"),
                                      ("status", "Status", 130, "w")], height=12)
        self.rec_table.pack(side="left", fill="both", expand=True)
        buttons = ttk.Frame(body, padding=(PAD, 0, 0, 0))
        buttons.pack(side="left", fill="y")
        for text, command, style in (("Add recurring…", self.add_recurring, "Accent.TButton"),
                                     ("Pause / resume", self.toggle_recurring, "TButton"),
                                     ("Delete", self.delete_recurring, "TButton")):
            ttk.Button(buttons, text=text, command=command, style=style,
                       width=16).pack(fill="x", pady=(0, 8))
        return page

    def _selected_rule(self):
        iid = self.rec_table.selected()
        if not iid:
            messagebox.showinfo("Nothing selected", "Click a recurring entry first.", parent=self)
            return None
        return int(iid)

    def add_recurring(self):
        values = RecurringDialog(self, self.app.db.categories(), self.app.month.get()).show()
        if not values:
            return

        def create():
            self.app.db.add_recurring(**values)
            created = self.app.db.apply_recurring()
            if created:
                messagebox.showinfo("Recurring entry added",
                                    f"Added {created} entr{'y' if created == 1 else 'ies'} that "
                                    "were already due.", parent=self)
        self._run(create)

    def toggle_recurring(self):
        rule_id = self._selected_rule()
        if rule_id is None:
            return
        rule = next(r for r in self.app.db.recurring_rules() if r["id"] == rule_id)
        self._run(lambda: (self.app.db.set_recurring_active(rule_id, not rule["active"]),
                           self.app.db.apply_recurring()))

    def delete_recurring(self):
        rule_id = self._selected_rule()
        if rule_id is None:
            return
        if messagebox.askyesno("Delete recurring entry",
                               "Stop this recurring entry?\n\nEntries it already added stay "
                               "in your transactions.", icon="warning", parent=self):
            self._run(lambda: self.app.db.delete_recurring(rule_id))

    # ---------- data ----------
    def _data_page(self, parent):
        page = ttk.Frame(parent, padding=PAD)
        ttk.Label(page, text="Backup and move your data", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(page, text="Export makes a CSV file you can open in Excel or keep as a backup. "
                             "Import reads a CSV with the columns: " + ", ".join(FIELDS)
                             + ". Rows that already exist are skipped.",
                  style="Muted.TLabel", wraplength=760, justify="left").pack(anchor="w",
                                                                             pady=(4, 12))
        row = ttk.Frame(page)
        row.pack(anchor="w")
        ttk.Button(row, text="Export everything…", style="Accent.TButton",
                   command=self.export_all).pack(side="left")
        ttk.Button(row, text="Import from CSV…", command=self.import_file).pack(side="left",
                                                                                   padx=8)
        ttk.Separator(page).pack(fill="x", pady=PAD)
        ttk.Label(page, text="Where your data is saved", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(page, text=self.app.db.path, style="Muted.TLabel").pack(anchor="w", pady=(4, 8))
        ttk.Label(page, text="This file stays when you replace or move Monthwise.exe. "
                             "Copy it to keep a full backup.",
                  style="Muted.TLabel").pack(anchor="w")
        ttk.Button(page, text="Open data folder", command=self.open_folder).pack(anchor="w",
                                                                                pady=(10, 0))
        return page

    def export_all(self):
        path = filedialog.asksaveasfilename(parent=self, title="Export everything",
                                            defaultextension=".csv",
                                            initialfile="monthwise-all.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                count = export_csv(self.app.db, path)
            except OSError as error:
                messagebox.showerror("Export failed", str(error), parent=self)
                return
            messagebox.showinfo("Exported", f"Saved {count} transactions to\n{path}", parent=self)

    def import_file(self):
        path = filedialog.askopenfilename(parent=self, title="Import from CSV",
                                          filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            result = import_csv(self.app.db, path)
        except (OSError, UnicodeDecodeError) as error:
            messagebox.showerror("Import failed", f"Couldn't read the file:\n{error}", parent=self)
            return
        self.app.refresh_all()
        message = f"Imported {result.imported} transaction(s)."
        if result.duplicates:
            message += f"\nSkipped {result.duplicates} already in Monthwise."
        if result.errors:
            shown = "\n".join(result.errors[:10])
            more = f"\n…and {len(result.errors) - 10} more." if len(result.errors) > 10 else ""
            message += f"\n\nSkipped {len(result.errors)} row(s) with problems:\n{shown}{more}"
        (messagebox.showwarning if result.errors else messagebox.showinfo)(
            "Import finished", message, parent=self)

    def open_folder(self):
        os.startfile(os.path.dirname(self.app.db.path))

    # ---------- refresh ----------
    def refresh(self):
        db = self.app.db
        p = theme.colors(self.app.mode)
        budgets = db.budgets()
        rows = []
        for position, name in enumerate(db.categories()):
            budget = budgets.get(name)
            used = db.category_usage(name)
            rows.append((name, (name, format_inr(budget) if budget else "—", used),
                         {"name": position, "budget": budget or 0, "used": used}, ()))
        self.cat_table.fill(rows)

        rules = []
        for r in db.recurring_rules():
            status = "Active" if r["active"] else "Paused"
            if r["last_applied"]:
                status += f" · last {month_label(r['last_applied'], long=False)}"
            credit = r["kind"] == "credit"
            rules.append((r["id"], (r["day"], "Credit" if credit else "Debit", r["category"],
                                    format_inr(r["amount"]), r["note"], status),
                          {"day": r["day"], "type": r["kind"], "category": r["category"].lower(),
                           "amount": r["amount"], "note": r["note"].lower(), "status": status},
                          () if r["active"] else ("paused",)))
        self.rec_table.fill(rules)
        self.rec_table.tree.tag_configure("paused", foreground=p["muted"])

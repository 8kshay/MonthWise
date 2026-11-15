"""Transactions tab: browse, search, edit, delete, export."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..csvio import export_csv
from ..dates import format_date, month_label
from ..money import format_inr
from . import theme
from .widgets import PAD, Table, TransactionDialog


class TransactionsTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=PAD)
        self.app = app
        self.search = tk.StringVar()
        self.all_months = tk.BooleanVar(value=False)

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 12))
        ttk.Label(bar, text="Search").pack(side="left")
        entry = ttk.Entry(bar, textvariable=self.search, width=28)
        entry.pack(side="left", padx=(8, 12))
        ttk.Checkbutton(bar, text="All months", variable=self.all_months,
                        command=self.refresh).pack(side="left")
        ttk.Button(bar, text="Export to CSV…", command=self.export).pack(side="right")
        ttk.Button(bar, text="Delete", command=self.delete).pack(side="right", padx=8)
        ttk.Button(bar, text="Edit", command=self.edit).pack(side="right")
        ttk.Button(bar, text="Add…", style="Accent.TButton",
                   command=self.add).pack(side="right", padx=8)
        self.search.trace_add("write", lambda *_: self.refresh())

        self.footer = ttk.Label(self, style="Muted.TLabel")
        self.footer.pack(side="bottom", fill="x", pady=(10, 0))

        self.table = Table(self, [("date", "Date", 110, "w"), ("type", "Type", 90, "w"),
                                  ("category", "Category", 150, "w"),
                                  ("amount", "Amount", 140, "e"), ("note", "Note", 320, "w")],
                           height=16)
        self.table.pack(fill="both", expand=True)
        self.table.tree.bind("<Double-1>", lambda _e: self.edit())
        self.table.tree.bind("<Delete>", lambda _e: self.delete())

    def _month(self):
        return None if self.all_months.get() else self.app.month.get()

    def refresh(self):
        p = theme.colors(self.app.mode)
        txs = self.app.db.transactions(month=self._month(), search=self.search.get())
        rows = []
        income = spent = 0
        for t in txs:
            credit = t["kind"] == "credit"
            if credit:
                income += t["amount"]
            else:
                spent += t["amount"]
            sign = "+" if credit else "−"
            rows.append((t["id"],
                         (format_date(t["date"]), "Credit" if credit else "Debit", t["category"],
                          f"{sign}{format_inr(t['amount'])}", t["note"]),
                         {"date": (t["date"], t["id"]), "type": t["kind"],
                          "category": t["category"].lower(),
                          "amount": t["amount"] if credit else -t["amount"],
                          "note": t["note"].lower()},
                         (t["kind"],)))
        self.table.fill(rows)
        self.table.tree.tag_configure("credit", foreground=p["positive"])
        scope = "all months" if self.all_months.get() else month_label(self.app.month.get())
        count = len(rows)
        self.footer.configure(
            text=f"{count} transaction{'s' if count != 1 else ''} in {scope}   ·   "
                 f"In {format_inr(income)}   ·   Out {format_inr(spent)}   ·   "
                 f"Net {format_inr(income - spent)}")

    def _selected_id(self):
        iid = self.table.selected()
        if not iid:
            messagebox.showinfo("Nothing selected", "Click a transaction in the list first.",
                                parent=self)
            return None
        return int(iid)

    def add(self):
        values = TransactionDialog(self, self.app.db.categories()).show()
        if values:
            self.app.db.add_transaction(**values)
            self.app.refresh_all()

    def edit(self):
        tx_id = self._selected_id()
        if tx_id is None:
            return
        tx = self.app.db.get_transaction(tx_id)
        values = TransactionDialog(self, self.app.db.categories(), tx).show()
        if values:
            self.app.db.update_transaction(tx_id, **values)
            self.app.refresh_all()

    def delete(self):
        tx_id = self._selected_id()
        if tx_id is None:
            return
        tx = self.app.db.get_transaction(tx_id)
        if messagebox.askyesno(
                "Delete transaction",
                f"Delete {format_inr(tx['amount'])} · {tx['category']} on "
                f"{format_date(tx['date'])}?\n\nThis can't be undone.",
                icon="warning", parent=self):
            self.app.db.delete_transaction(tx_id)
            self.app.refresh_all()

    def export(self):
        month = self._month()
        name = f"monthwise-{month or 'all'}.csv"
        path = filedialog.asksaveasfilename(parent=self, title="Export to CSV",
                                            defaultextension=".csv", initialfile=name,
                                            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            count = export_csv(self.app.db, path, month=month)
        except OSError as error:
            messagebox.showerror("Export failed", str(error), parent=self)
            return
        messagebox.showinfo("Exported", f"Saved {count} transactions to\n{path}", parent=self)

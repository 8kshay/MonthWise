"""Add tab: quick entry form plus recent entries."""

import datetime as dt
from tkinter import ttk

from ..dates import format_date, month_key, month_label
from ..money import format_inr
from . import theme
from .widgets import PAD, Table, TransactionForm


class AddTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=PAD)
        self.app = app
        self.columnconfigure(0, weight=3, uniform="cols")
        self.columnconfigure(1, weight=2, uniform="cols")
        self.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(self, text=" New transaction ", padding=PAD)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, PAD))
        self.form = TransactionForm(left, app.db.categories())
        self.form.pack(fill="x")
        actions = ttk.Frame(left)
        actions.pack(fill="x", pady=(PAD, 0))
        ttk.Button(actions, text="Save transaction", style="Accent.TButton",
                   command=self.save).pack(side="left")
        ttk.Label(actions, text="or press Enter", style="Muted.TLabel").pack(side="left", padx=10)
        self.status = ttk.Label(left, text="")
        self.status.pack(fill="x", pady=(12, 0))

        ttk.Separator(left).pack(fill="x", pady=PAD)
        self.month_caption = ttk.Label(left, style="Heading.TLabel")
        self.month_caption.pack(anchor="w")
        stats = ttk.Frame(left)
        stats.pack(fill="x", pady=(8, 0))
        self.stat_labels = {}
        for i, (key, caption) in enumerate((("spent", "Spent"), ("income", "Received"),
                                            ("net", "Left over"))):
            stats.columnconfigure(i, weight=1)
            box = ttk.Frame(stats)
            box.grid(row=0, column=i, sticky="w")
            ttk.Label(box, text=caption, style="StatCaption.TLabel").pack(anchor="w")
            label = ttk.Label(box, style="Heading.TLabel")
            label.pack(anchor="w")
            self.stat_labels[key] = label

        right = ttk.LabelFrame(self, text=" Latest entries (all months) ", padding=PAD)
        right.grid(row=0, column=1, sticky="nsew")
        self.recent = Table(right, [("date", "Date", 95, "w"), ("category", "Category", 110, "w"),
                                    ("amount", "Amount", 110, "e")], height=14)
        self.recent.pack(fill="both", expand=True)
        self.empty_note = ttk.Label(right, style="Muted.TLabel", wraplength=320, justify="left",
                                    text="No entries yet. Fill in the form on the left and press "
                                         "Save; your entries appear here.")

        for widget in (self, left):
            widget.bind("<Return>", lambda _e: self.save())
        for child in self.form.winfo_children():
            child.bind("<Return>", lambda _e: self.save(), add="+")
            for grandchild in child.winfo_children():
                grandchild.bind("<Return>", lambda _e: self.save(), add="+")

    def save(self):
        try:
            values = self.form.values()
            self.app.db.add_transaction(**values)
        except ValueError as error:
            theme.style_label(self.status, "Negative.TLabel", text=str(error))
            return
        sign = "+" if values["kind"] == "credit" else "−"
        theme.style_label(
            self.status, "Positive.TLabel",
            text=f"Saved {sign}{format_inr(values['amount'])} · {values['category']} "
                 f"· {format_date(values['date'])}")
        self.form.clear()
        self.app.refresh_all()

    def refresh(self):
        db = self.app.db
        self.form.set_categories(db.categories())
        month = self.app.month.get()  # follows the month picker at the top
        so_far = " so far" if month == month_key(dt.date.today()) else ""
        self.month_caption.configure(text=f"{month_label(month)}{so_far}")
        totals = db.month_totals(month)
        p = theme.colors(self.app.mode)
        for key, label in self.stat_labels.items():
            style = "Heading.TLabel"
            if key == "net":
                style = ("HeadingPositive.TLabel" if totals["net"] >= 0
                         else "HeadingNegative.TLabel")
            theme.style_label(label, style, text=format_inr(totals[key]))
        rows = []
        for t in db.transactions(limit=25):
            sign = "+" if t["kind"] == "credit" else "−"
            rows.append((t["id"], (format_date(t["date"]), t["category"],
                                   f"{sign}{format_inr(t['amount'])}"),
                         {"date": (t["date"], t["id"]), "category": t["category"].lower(),
                          "amount": t["amount"] if t["kind"] == "credit" else -t["amount"]},
                         (t["kind"],)))
        self.recent.fill(rows)
        self.recent.tree.tag_configure("credit", foreground=p["positive"])
        if rows:
            self.empty_note.pack_forget()
        else:
            self.empty_note.pack(anchor="w", pady=(0, 10), before=self.recent)

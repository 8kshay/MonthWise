"""Reusable pieces: month picker, transaction form, dialogs, sortable table."""

import datetime as dt
import tkinter as tk
from tkinter import messagebox, ttk

from ..dates import add_months, format_date, month_key, month_label, parse_date
from ..money import RUPEE, parse_amount, to_plain
from . import theme

PAD = 16


class MonthPicker(ttk.Frame):
    """[‹ Prev]  November 2026  [Next ›]  [This month]   (mouse wheel over it also works)"""

    def __init__(self, master, month_var: tk.StringVar):
        super().__init__(master)
        self.month_var = month_var
        self.prev_button = ttk.Button(self, text="‹  Prev", command=lambda: self.shift(-1))
        self.prev_button.pack(side="left")
        self.label = ttk.Label(self, style="Month.TLabel", width=15, anchor="center")
        self.label.pack(side="left", padx=6)
        self.next_button = ttk.Button(self, text="Next  ›", command=lambda: self.shift(1))
        self.next_button.pack(side="left")
        self.today_button = ttk.Button(self, text="This month", command=self.today)
        self.today_button.pack(side="left", padx=(10, 0))
        for widget in (self, self.label, self.prev_button, self.next_button):
            widget.bind("<MouseWheel>", self._wheel)
        month_var.trace_add("write", lambda *_: self._show())
        self._show()

    def _wheel(self, event):
        self.shift(1 if event.delta < 0 else -1)  # scroll down = later month
        return "break"

    def _show(self):
        key = self.month_var.get()
        self.label.configure(text=month_label(key))
        if key == month_key(dt.date.today()):
            self.today_button.state(["disabled"])
        else:
            self.today_button.state(["!disabled"])

    def shift(self, n):
        self.month_var.set(add_months(self.month_var.get(), n))

    def today(self):
        self.month_var.set(month_key(dt.date.today()))


class TransactionForm(ttk.Frame):
    """Fields for one transaction. values() validates and raises ValueError."""

    def __init__(self, master, categories):
        super().__init__(master)
        self.kind = tk.StringVar(value="debit")
        self.amount = tk.StringVar()
        self.date = tk.StringVar(value=format_date(dt.date.today()))
        self.category = tk.StringVar()
        self.note = tk.StringVar()
        self.columnconfigure(1, weight=1)

        def label(row, text):
            ttk.Label(self, text=text).grid(row=row, column=0, sticky="w", pady=8, padx=(0, 16))

        label(0, "Type")
        kinds = ttk.Frame(self)
        kinds.grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(kinds, text="Money out (debit)", value="debit",
                        variable=self.kind).pack(side="left", padx=(0, 18))
        ttk.Radiobutton(kinds, text="Money in (credit)", value="credit",
                        variable=self.kind).pack(side="left")

        label(1, f"Amount ({RUPEE})")
        self.amount_entry = ttk.Entry(self, textvariable=self.amount, width=18)
        self.amount_entry.grid(row=1, column=1, sticky="w")

        label(2, "Date")
        dates = ttk.Frame(self)
        dates.grid(row=2, column=1, sticky="w")
        ttk.Entry(dates, textvariable=self.date, width=14).pack(side="left")
        ttk.Button(dates, text="Today", command=lambda: self.set_date(0)).pack(side="left", padx=(8, 4))
        ttk.Button(dates, text="Yesterday", command=lambda: self.set_date(-1)).pack(side="left")
        ttk.Label(dates, text="DD-MM-YYYY", style="Muted.TLabel").pack(side="left", padx=10)

        label(3, "Category")
        self.category_box = ttk.Combobox(self, textvariable=self.category, state="readonly", width=24)
        self.category_box.grid(row=3, column=1, sticky="w")

        label(4, "Note")
        ttk.Entry(self, textvariable=self.note).grid(row=4, column=1, sticky="ew")

        self.set_categories(categories)

    def set_date(self, offset_days):
        self.date.set(format_date(dt.date.today() + dt.timedelta(days=offset_days)))

    def set_categories(self, categories):
        self.category_box.configure(values=categories)
        if self.category.get() not in categories and categories:
            self.category.set(categories[0])

    def values(self) -> dict:
        amount = parse_amount(self.amount.get())
        date = parse_date(self.date.get())
        if not self.category.get():
            raise ValueError("Choose a category.")
        return {"date": date, "amount": amount, "kind": self.kind.get(),
                "category": self.category.get(), "note": self.note.get().strip()}

    def load(self, tx: dict):
        self.kind.set(tx["kind"])
        self.amount.set(to_plain(tx["amount"]))
        self.date.set(format_date(tx["date"]))
        self.category.set(tx["category"])
        self.note.set(tx["note"])

    def clear(self):
        """Ready for the next entry; keeps type, date and category for fast typing."""
        self.amount.set("")
        self.note.set("")
        self.amount_entry.focus_set()


class Dialog(tk.Toplevel):
    """Modal window centred on its parent. Subclasses fill self.body and set self.result."""

    def __init__(self, parent, title, ok_text="Save"):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.result = None
        outer = ttk.Frame(self, padding=PAD)
        outer.pack(fill="both", expand=True)
        self.body = ttk.Frame(outer)
        self.body.pack(fill="both", expand=True)
        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=(PAD, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text=ok_text, style="Accent.TButton",
                   command=self._ok).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _e: self._ok())
        self.bind("<Escape>", lambda _e: self.destroy())

    def show(self):
        theme.recolor(self)
        self.update_idletasks()
        top = self.master.winfo_toplevel()
        x = top.winfo_rootx() + (top.winfo_width() - self.winfo_reqwidth()) // 2
        y = top.winfo_rooty() + (top.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.deiconify()
        self.grab_set()
        self.wait_window()
        return self.result

    def _ok(self):
        try:
            self.result = self.collect()
        except ValueError as error:
            messagebox.showerror("Check the details", str(error), parent=self)
            return
        self.destroy()

    def collect(self):
        raise NotImplementedError


class TransactionDialog(Dialog):
    def __init__(self, parent, categories, tx=None):
        super().__init__(parent, "Edit transaction" if tx else "Add transaction")
        self.form = TransactionForm(self.body, categories)
        self.form.pack(fill="both", expand=True)
        if tx:
            self.form.load(tx)

    def collect(self):
        return self.form.values()


class TextDialog(Dialog):
    """Ask for one value; `parse` turns the text into the result or raises ValueError."""

    def __init__(self, parent, title, prompt, initial="", parse=None, ok_text="Save"):
        super().__init__(parent, title, ok_text)
        self.parse = parse or (lambda text: text.strip())
        ttk.Label(self.body, text=prompt).pack(anchor="w", pady=(0, 8))
        self.value = tk.StringVar(value=initial)
        entry = ttk.Entry(self.body, textvariable=self.value, width=34)
        entry.pack(fill="x")
        entry.focus_set()
        entry.select_range(0, "end")

    def collect(self):
        return self.parse(self.value.get())


class RecurringDialog(Dialog):
    def __init__(self, parent, categories, start_month):
        super().__init__(parent, "Add recurring entry", ok_text="Add")
        self.start_month = start_month
        self.form = TransactionForm(self.body, categories)
        # Swap the date row for a day-of-month choice.
        for child in self.form.grid_slaves(row=2):
            child.grid_forget()
        ttk.Label(self.form, text="Day of month").grid(row=2, column=0, sticky="w", pady=8)
        days = ttk.Frame(self.form)
        days.grid(row=2, column=1, sticky="w")
        self.day = tk.StringVar(value="1")
        ttk.Spinbox(days, from_=1, to=28, textvariable=self.day, width=5,
                    state="readonly").pack(side="left")
        ttk.Label(days, text=f"every month, starting {month_label(start_month)}",
                  style="Muted.TLabel").pack(side="left", padx=10)
        self.form.pack(fill="both", expand=True)

    def collect(self):
        values = {"amount": parse_amount(self.form.amount.get()), "kind": self.form.kind.get(),
                  "category": self.form.category.get(), "note": self.form.note.get().strip()}
        if not values["category"]:
            raise ValueError("Choose a category.")
        values["day"] = int(self.day.get())
        values["start_month"] = self.start_month
        return values


class Table(ttk.Frame):
    """Treeview with a scrollbar and click-to-sort headings."""

    def __init__(self, master, columns, height=12):
        super().__init__(master)
        self.columns = columns  # list of (id, heading, width, anchor)
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show="headings",
                                 height=height, selectmode="browse")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.sort_keys = {}
        self._sorted = (None, False)
        for col, heading, width, anchor in columns:
            self.tree.heading(col, text=heading, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=width, minwidth=50, anchor=anchor, stretch=True)

    def fill(self, rows):
        """rows: list of (iid, values tuple, sort_values dict, tags)."""
        self.tree.delete(*self.tree.get_children())
        self.sort_keys = {}
        for iid, values, sort_values, tags in rows:
            self.tree.insert("", "end", iid=str(iid), values=values, tags=tags)
            self.sort_keys[str(iid)] = sort_values

    def selected(self):
        selection = self.tree.selection()
        return selection[0] if selection else None

    def sort_by(self, col):
        last_col, reverse = self._sorted
        reverse = not reverse if last_col == col else False
        items = list(self.tree.get_children())
        items.sort(key=lambda iid: self.sort_keys.get(iid, {}).get(col, ""), reverse=reverse)
        for index, iid in enumerate(items):
            self.tree.move(iid, "", index)
        self._sorted = (col, reverse)

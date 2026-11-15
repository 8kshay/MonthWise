"""Summary tab: month totals, comparison with last month, categories vs budgets, recent months."""

from tkinter import ttk

from ..dates import add_months, month_label
from ..money import format_inr
from . import theme
from .widgets import PAD, Table


class SummaryTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=PAD)
        self.app = app
        self.columnconfigure(0, weight=3, uniform="cols")
        self.columnconfigure(1, weight=2, uniform="cols")
        self.rowconfigure(1, weight=1)

        cards = ttk.Frame(self)
        cards.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, PAD))
        self.cards = {}
        for i, (key, caption) in enumerate((("income", "Money in"), ("spent", "Money spent"),
                                            ("net", "Left over"), ("count", "Transactions"))):
            cards.columnconfigure(i, weight=1, uniform="cards")
            box = ttk.LabelFrame(cards, text=f" {caption} ", padding=(PAD, 10))
            box.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            value = ttk.Label(box, style="StatValue.TLabel")
            value.pack(anchor="w")
            change = ttk.Label(box, style="Muted.TLabel")
            change.pack(anchor="w")
            self.cards[key] = (value, change)

        left = ttk.LabelFrame(self, text=" Spending by category ", padding=PAD)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, PAD))
        self.categories = Table(left, [("category", "Category", 140, "w"),
                                       ("spent", "Spent", 120, "e"), ("share", "Share", 70, "e"),
                                       ("budget", "Budget", 120, "e"),
                                       ("left", "Budget left", 130, "e")], height=10)
        self.categories.pack(fill="both", expand=True)
        self.budget_note = ttk.Label(left, style="Muted.TLabel",
                                     text="Set monthly budgets in Settings → Categories & budgets.")
        self.budget_note.pack(anchor="w", pady=(8, 0))

        right = ttk.LabelFrame(self, text=" Compare months ", padding=PAD)
        right.grid(row=1, column=1, sticky="nsew")
        self.months = Table(right, [("month", "Month", 85, "w"), ("income", "In", 85, "e"),
                                    ("spent", "Spent", 85, "e"), ("net", "Left over", 85, "e")],
                            height=10)
        self.months.pack(fill="both", expand=True)
        self.average = ttk.Label(right, style="Muted.TLabel")
        self.average.pack(anchor="w", pady=(8, 0))

    def refresh(self):
        db = self.app.db
        p = theme.colors(self.app.mode)
        month = self.app.month.get()
        previous = add_months(month, -1)
        now, before = db.month_totals(month), db.month_totals(previous)

        for key, (value, change) in self.cards.items():
            if key == "count":
                theme.style_label(value, "StatValue.TLabel", text=str(now["count"]))
                theme.style_label(change, "Muted.TLabel",
                                  text=f"{before['count']} in {month_label(previous, long=False)}")
                continue
            style = "StatValue.TLabel"
            if key == "net":
                style = "StatPositive.TLabel" if now["net"] >= 0 else "StatNegative.TLabel"
            theme.style_label(value, style, text=format_inr(now[key], decimals=False))
            text, change_style = self._change(key, now[key], before[key], previous)
            theme.style_label(change, change_style, text=text)

        spent_total = now["spent"]
        budgets = db.budgets()
        spent_by = dict(db.category_totals(month))
        names = list(spent_by) + [c for c in budgets if c not in spent_by]
        rows = []
        for name in names:
            spent = spent_by.get(name, 0)
            budget = budgets.get(name)
            share = spent / spent_total * 100 if spent_total else 0
            left = None if budget is None else budget - spent
            if left is None:
                left_text = "—"
            elif left >= 0:
                left_text = format_inr(left)
            else:
                left_text = f"{format_inr(-left)} over"
            tags = ("over",) if left is not None and left < 0 else ()
            rows.append((name, (name, format_inr(spent), f"{share:.0f}%",
                                format_inr(budget) if budget else "—", left_text),
                         {"category": name.lower(), "spent": spent, "share": share,
                          "budget": budget or 0, "left": left if left is not None else 10**15},
                         tags))
        self.categories.fill(rows)
        self.categories.tree.tag_configure("over", foreground=p["negative"])
        self.budget_note.configure(
            text="No spending this month yet." if not rows else
            "Set monthly budgets in Settings → Categories & budgets.")

        history = db.monthly_totals(month, 6)
        month_rows = []
        for m in reversed(history):
            month_rows.append((m["month"], (month_label(m["month"], long=False),
                                            format_inr(m["income"], decimals=False),
                                            format_inr(m["spent"], decimals=False),
                                            format_inr(m["net"], decimals=False)),
                               {"month": m["month"], "income": m["income"], "spent": m["spent"],
                                "net": m["net"]},
                               ("current",) if m["month"] == month else ()))
        self.months.fill(month_rows)
        self.months.tree.tag_configure("current", foreground=p["accent"])
        active = [m["spent"] for m in history if m["spent"] or m["income"]]
        if active:
            avg = sum(active) // len(active)
            self.average.configure(
                text=f"Average spent over {len(active)} active month(s): {format_inr(avg, False)}")
        else:
            self.average.configure(text="No data in the last 6 months.")

    @staticmethod
    def _change(key, now, before, previous):
        label = month_label(previous, long=False)
        if before == 0:
            return (f"Nothing in {label}" if now else "—"), "Muted.TLabel"
        diff = now - before
        pct = abs(diff) / abs(before) * 100
        arrow = "▲" if diff > 0 else "▼" if diff < 0 else "●"
        good = diff <= 0 if key == "spent" else diff >= 0
        style = "Muted.TLabel" if diff == 0 else ("Positive.TLabel" if good else "Negative.TLabel")
        pct_text = "<1%" if 0 < pct < 1 else f"{pct:.0f}%"
        return f"{arrow} {pct_text} vs {label}", style

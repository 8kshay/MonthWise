"""Charts tab: category split for the month and month-by-month comparison."""

from tkinter import ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from ..dates import MONTH_ABBR, month_label, split_month  # noqa: E402
from ..money import format_compact, format_inr  # noqa: E402
from . import theme  # noqa: E402
from .widgets import PAD  # noqa: E402

matplotlib.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]


class ChartsTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=PAD)
        self.app = app
        self.figure = Figure(figsize=(11, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh(self):
        db = self.app.db
        p = theme.colors(self.app.mode)
        month = self.app.month.get()
        fig = self.figure
        fig.clear()
        fig.set_facecolor(p["bg"])
        self.canvas.get_tk_widget().configure(background=p["bg"], highlightthickness=0)
        grid = fig.add_gridspec(2, 2, width_ratios=[2, 3], height_ratios=[3, 1.25],
                                wspace=0.28, hspace=0.05)
        fig.subplots_adjust(left=0.03, right=0.98, top=0.86, bottom=0.1)

        # --- Donut: where the money went this month ---
        ax = fig.add_subplot(grid[0, 0])
        key_ax = fig.add_subplot(grid[1, 0])
        key_ax.axis("off")
        ax.set_facecolor(p["bg"])
        totals = db.category_totals(month)
        fig.text(0.03, 0.94, f"Spending by category · {month_label(month)}",
                 color=p["fg"], fontsize=12, ha="left", va="center")
        if totals:
            if len(totals) > 8:
                totals = totals[:7] + [("Others", sum(v for _, v in totals[7:]))]
            values = [v for _, v in totals]
            spent = sum(values)
            wedges, _ = ax.pie(values, colors=theme.SERIES[:len(values)], startangle=90,
                               counterclock=False,
                               wedgeprops={"width": 0.38, "edgecolor": p["bg"], "linewidth": 2})
            ax.text(0, 0.08, format_compact(spent), ha="center", va="center",
                    fontsize=17, fontweight="bold", color=p["fg"])
            ax.text(0, -0.16, "spent", ha="center", va="center", fontsize=10, color=p["muted"])
            labels = [f"{name}  {format_inr(v, decimals=False)}  ({v / spent * 100:.0f}%)"
                      for name, v in totals]
            legend = key_ax.legend(wedges, labels, loc="upper center", frameon=False,
                                   fontsize=8.5, ncol=2, columnspacing=1.2, handlelength=1.2)
            for text in legend.get_texts():
                text.set_color(p["fg"])
            ax.set_aspect("equal")
        else:
            ax.axis("off")
            ax.text(0.5, 0.5, "No spending recorded\nfor this month yet",
                    ha="center", va="center", color=p["muted"], fontsize=11,
                    transform=ax.transAxes)

        # --- Bars: last 12 months, spent vs received ---
        bx = fig.add_subplot(grid[:, 1])
        history = db.monthly_totals(month, 12)
        labels = []
        for m in history:
            year, mon = split_month(m["month"])
            labels.append(MONTH_ABBR[mon - 1] + ("\n" + str(year) if mon == 1 or m is history[0]
                                                  else ""))
        xs = range(len(history))
        width = 0.38
        spent_colors = [p["highlight"] if m["month"] == month else p["spent"] for m in history]
        bx.bar([x - width / 2 for x in xs], [m["spent"] for m in history], width,
               color=spent_colors, label="Spent", zorder=3)
        bx.bar([x + width / 2 for x in xs], [m["income"] for m in history], width,
               color=p["income"], alpha=0.85, label="Received", zorder=3)
        bx.set_xticks(list(xs))
        bx.set_xticklabels(labels, fontsize=8.5, color=p["muted"])
        bx.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: format_compact(int(v))))
        bx.tick_params(axis="y", colors=p["muted"], labelsize=9)
        bx.tick_params(axis="x", length=0)
        bx.grid(axis="y", color=p["grid"], linewidth=0.8, zorder=0)
        bx.set_facecolor(p["bg"])
        for side in ("top", "right", "left"):
            bx.spines[side].set_visible(False)
        bx.spines["bottom"].set_color(p["grid"])
        fig.text(bx.get_position().x0, 0.94, "Month by month · last 12 months",
                 color=p["fg"], fontsize=12, ha="left", va="center")
        legend = bx.legend(frameon=False, fontsize=9, loc="lower left",
                           bbox_to_anchor=(0, 1.0), ncol=2)
        for text in legend.get_texts():
            text.set_color(p["fg"])
        if not any(m["spent"] or m["income"] for m in history):
            bx.text(0.5, 0.5, "No data yet", ha="center", va="center",
                    color=p["muted"], transform=bx.transAxes)

        self.canvas.draw_idle()

"""Charts tab: Overview (category split + month by month) and Through the month (line chart)."""

import calendar
import datetime as dt
from tkinter import ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import AutoMinorLocator, FuncFormatter, MultipleLocator  # noqa: E402

from ..dates import MONTH_ABBR, add_months, month_key, month_label, split_month  # noqa: E402
from ..money import format_compact, format_inr  # noqa: E402
from . import theme  # noqa: E402
from .widgets import PAD  # noqa: E402

matplotlib.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]

# Marker-pen colours for the line chart: chosen month first, then the 3 before it.
PEN = {"light": ["#e8302f", "#3fb33f", "#2ea3e0", "#f2c618"],
       "dark": ["#ff6b6b", "#69db7c", "#4dabf7", "#ffd43b"]}
PAPER = {"light": {"paper": "#fdfdfb", "major": "#cfe2f2", "minor": "#e6f0f9"},
         "dark": {"paper": "#1c1c1c", "major": "#2d3b47", "minor": "#242c33"}}
COMPARE_MONTHS = 4
TITLE_FONT = [theme.FONT_BOLD, theme.FONT, "DejaVu Sans"]  # same font as the rest of the app


def _spaced(text):
    """'LINE CHART' -> 'L I N E   C H A R T' for the wide-lettered title look."""
    return "   ".join(" ".join(word) for word in text.upper().split())


class ChartsTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=PAD)
        self.app = app
        self.pages = ttk.Notebook(self)
        self.pages.pack(fill="both", expand=True)
        self.figure, self.canvas = self._add_page("  Overview  ")
        self.trend_figure, self.trend_canvas = self._add_page("  Through the month  ")
        self.pages.bind("<<NotebookTabChanged>>", lambda _e: self.refresh())

    def _add_page(self, title):
        page = ttk.Frame(self.pages, padding=(0, 8, 0, 0))
        self.pages.add(page, text=title)
        figure = Figure(figsize=(11, 5), dpi=100)
        canvas = FigureCanvasTkAgg(figure, master=page)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        return figure, canvas

    def refresh(self):
        if self.pages.index(self.pages.select()) == 0:
            self._draw_overview()
        else:
            self._draw_trend()

    def _draw_trend(self):
        """Running total of money spent through the month, one marker-pen line per month."""
        db = self.app.db
        mode = self.app.mode
        p = theme.colors(mode)
        paper = PAPER.get(mode, PAPER["light"])
        pens = PEN.get(mode, PEN["light"])
        chosen = self.app.month.get()
        today = dt.date.today()
        current = month_key(today)

        fig = self.trend_figure
        fig.clear()
        fig.set_facecolor(paper["paper"])
        self.trend_canvas.get_tk_widget().configure(background=paper["paper"],
                                                    highlightthickness=0)
        fig.subplots_adjust(left=0.07, right=0.9, top=0.78, bottom=0.12)
        fig.text(0.5, 0.94, _spaced("Spending through the month"), ha="center", va="center",
                 fontsize=16, color=p["fg"], family=TITLE_FONT)
        fig.add_artist(Line2D([0.36, 0.64], [0.893, 0.893], color=pens[0], linewidth=2.2,
                              solid_capstyle="round"))
        fig.text(0.5, 0.85, f"Running total of money spent, day by day · "
                             f"{month_label(chosen)} against the {COMPARE_MONTHS - 1} months "
                             "before it",
                 ha="center", va="center", fontsize=9.5, color=p["muted"])

        ax = fig.add_subplot(111)
        ax.set_facecolor(paper["paper"])
        ax.set_xlim(0.3, 31.7)
        ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.yaxis.set_minor_locator(AutoMinorLocator(4))
        ax.grid(which="major", color=paper["major"], linewidth=1.1)
        ax.grid(which="minor", color=paper["minor"], linewidth=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(which="both", length=0, colors=p["muted"], labelsize=9)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: format_compact(int(v))))
        ax.set_xlabel("Day of the month", color=p["muted"], fontsize=9.5)
        for spine in ax.spines.values():
            spine.set_visible(False)

        handles, top = [], 0
        for index in reversed(range(COMPARE_MONTHS)):  # oldest first so the chosen month is on top
            month = add_months(chosen, -index)
            if month > current:
                continue
            year, mon = split_month(month)
            days_in_month = calendar.monthrange(year, mon)[1]
            last_day = today.day if month == current else days_in_month
            daily = db.daily_spent(month)
            running, xs, ys = 0, [], []
            for day in range(1, last_day + 1):
                running += daily.get(day, 0)
                xs.append(day)
                ys.append(running)
            if not running:
                continue
            top = max(top, running)
            chosen_line = index == 0
            colour = pens[index]
            line, = ax.plot(xs, ys, color=colour, linewidth=6 if chosen_line else 4.5,
                            alpha=1 if chosen_line else 0.8, solid_capstyle="round",
                            solid_joinstyle="round", zorder=4 if chosen_line else 3)
            line.set_sketch_params(scale=1.1, length=90, randomness=14)  # hand-drawn wobble
            dots = sorted({d for d in (1, 8, 15, 22, last_day) if d <= last_day})
            ax.scatter(dots, [ys[d - 1] for d in dots], s=230 if chosen_line else 160,
                       color=colour, alpha=1 if chosen_line else 0.85,
                       edgecolors=paper["paper"], linewidths=1.5, zorder=5 if chosen_line else 3)
            if chosen_line:
                ax.annotate(format_compact(running), (xs[-1], ys[-1]), xytext=(14, 0),
                            textcoords="offset points", va="center", fontsize=11,
                            fontweight="bold", color=p["fg"], annotation_clip=False)
            so_far = " so far" if month == current else ""
            label = f"{month_label(month, long=False)}  ·  {format_inr(running, False)}{so_far}"
            handles.append(Line2D([], [], color=colour, linewidth=5, marker="o", markersize=9,
                                  label=label))

        if not handles:
            ax.text(0.5, 0.5, "No spending recorded in these months yet", ha="center",
                    va="center", color=p["muted"], fontsize=11, transform=ax.transAxes)
            ax.set_ylim(0, 1)
            ax.set_yticks([])
        else:
            ax.set_ylim(0, top * 1.08)
            legend = ax.legend(handles=list(reversed(handles)), loc="upper left", frameon=False,
                               fontsize=9.5, handlelength=2.2, borderaxespad=0.6)
            for text in legend.get_texts():
                text.set_color(p["fg"])
        self.trend_canvas.draw_idle()

    def _draw_overview(self):
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

"""Look and feel: Sun Valley (Windows 11 style) theme plus Monthwise's own text styles."""

from tkinter import ttk

import sv_ttk

FONT = "Segoe UI"
FONT_BOLD = "Segoe UI Semibold"

PALETTE = {
    "light": {"bg": "#fafafa", "fg": "#1c1c1c", "muted": "#6b6b6b", "grid": "#e6e6e6",
              "accent": "#005fb8", "positive": "#0f7b0f", "negative": "#c42b1c",
              "income": "#2e9e5b", "spent": "#3b7dd8", "highlight": "#e8590c"},
    "dark": {"bg": "#1c1c1c", "fg": "#f3f3f3", "muted": "#a3a3a3", "grid": "#353535",
             "accent": "#57c8ff", "positive": "#6ccb5f", "negative": "#ff99a4",
             "income": "#5fd38d", "spent": "#6ea8ff", "highlight": "#ffa94d"},
}

# Category colours for charts (readable on light and dark backgrounds).
SERIES = ["#3b7dd8", "#e8590c", "#2e9e5b", "#ae3ec9", "#f59f00", "#1098ad",
          "#d6336c", "#74b816", "#7048e8", "#868e96"]


# Sun Valley ignores label text colours set through styles, so labels are coloured
# directly; this maps each label style to its palette colour.
STYLE_COLORS = {
    "Subtitle.TLabel": "muted", "Muted.TLabel": "muted", "StatCaption.TLabel": "muted",
    "Positive.TLabel": "positive", "Negative.TLabel": "negative",
    "HeadingPositive.TLabel": "positive", "HeadingNegative.TLabel": "negative",
    "StatPositive.TLabel": "positive", "StatNegative.TLabel": "negative",
}
_current = {"mode": "light"}


def colors(mode: str) -> dict:
    return PALETTE.get(mode, PALETTE["light"])


def _foreground(style: str) -> str:
    role = STYLE_COLORS.get(style)
    return colors(_current["mode"])[role] if role else ""


def style_label(label, style: str, **options):
    """Change a label's style (and so its colour)."""
    label.configure(style=style, foreground=_foreground(style), **options)


def recolor(widget):
    """Re-apply label colours to a widget and everything inside it."""
    if isinstance(widget, ttk.Label):
        widget.configure(foreground=_foreground(str(widget.cget("style"))))
    for child in widget.winfo_children():
        recolor(child)


def apply(root, mode: str):
    _current["mode"] = mode
    sv_ttk.set_theme(mode, root)
    p = colors(mode)
    style = ttk.Style(root)
    style.configure(".", font=(FONT, 10))
    style.configure("Title.TLabel", font=(FONT_BOLD, 20))
    style.configure("Subtitle.TLabel", font=(FONT, 10), foreground=p["muted"])
    style.configure("Heading.TLabel", font=(FONT_BOLD, 13))
    style.configure("Month.TLabel", font=(FONT_BOLD, 13))
    style.configure("Muted.TLabel", foreground=p["muted"])
    style.configure("StatCaption.TLabel", font=(FONT, 10), foreground=p["muted"])
    style.configure("StatValue.TLabel", font=(FONT_BOLD, 22))
    style.configure("StatPositive.TLabel", font=(FONT_BOLD, 22), foreground=p["positive"])
    style.configure("StatNegative.TLabel", font=(FONT_BOLD, 22), foreground=p["negative"])
    style.configure("Positive.TLabel", foreground=p["positive"])
    style.configure("Negative.TLabel", foreground=p["negative"])
    style.configure("HeadingPositive.TLabel", font=(FONT_BOLD, 13), foreground=p["positive"])
    style.configure("HeadingNegative.TLabel", font=(FONT_BOLD, 13), foreground=p["negative"])
    style.configure("Treeview", rowheight=30)
    style.configure("Treeview.Heading", font=(FONT_BOLD, 9))
    root.configure(background=p["bg"])
    recolor(root)

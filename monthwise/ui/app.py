"""Main window: header with month picker and theme switch, then the tabs."""

import datetime as dt
import sys
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from .. import APP_NAME, __version__
from ..dates import month_key
from ..paths import resource_path
from ..users import USERS, UserStore
from . import theme
from .add_tab import AddTab
from .charts_tab import ChartsTab
from .settings_tab import SettingsTab
from .summary_tab import SummaryTab
from .transactions_tab import TransactionsTab
from .widgets import PAD, MonthPicker


class MonthwiseApp(tk.Tk):
    def __init__(self, store: UserStore):
        super().__init__(className=APP_NAME)
        self.store = store
        self.user = store.last_user()
        self.db = store.open(self.user)
        self.withdraw()
        self.geometry("1180x760")
        self.minsize(980, 640)
        self._set_icon()
        self.mode = store.get_pref("theme", "light")
        theme.apply(self, self.mode)

        self.month = tk.StringVar(value=month_key(dt.date.today()))

        header = ttk.Frame(self, padding=(PAD + 4, PAD, PAD + 4, 4))
        header.pack(fill="x")
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text="Your money, month by month",
                  style="Subtitle.TLabel").pack(anchor="w")
        self.theme_button = ttk.Button(header, command=self.toggle_theme, width=12)
        self.theme_button.pack(side="right")
        self.month_picker = MonthPicker(header, self.month)
        self.month_picker.pack(side="right", padx=(0, 24))
        users = ttk.Frame(header)
        users.pack(side="right", padx=(0, 24))
        ttk.Label(users, text="User").pack(side="left", padx=(0, 8))
        self.user_var = tk.StringVar(value=USERS[self.user])
        self.user_box = ttk.Combobox(users, textvariable=self.user_var, state="readonly",
                                     width=10, values=list(USERS.values()))
        self.user_box.pack(side="left")
        self.user_box.bind("<<ComboboxSelected>>", self._user_chosen)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=PAD, pady=(8, PAD))
        self.tabs = []
        for cls, label in ((AddTab, "Add"), (TransactionsTab, "Transactions"),
                           (SummaryTab, "Summary"), (ChartsTab, "Charts"),
                           (SettingsTab, "Settings")):
            tab = cls(self.notebook, self)
            self.notebook.add(tab, text=f"  {label}  ")
            self.tabs.append(tab)
        self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self.refresh_current())

        self._dirty = set()
        self.month.trace_add("write", lambda *_: self.refresh_all())
        self.bind_all("<Control-Tab>", self._next_tab)

        theme.recolor(self)
        self._update_theme_button()
        self._update_title()
        self.refresh_all()
        self.deiconify()
        self._apply_recurring()

    def _update_title(self):
        self.title(f"{APP_NAME} — {USERS[self.user]}")

    def _apply_recurring(self):
        created = self.db.apply_recurring()
        if created:
            self.refresh_all()
            self.after(400, lambda: messagebox.showinfo(
                APP_NAME, f"Added {created} recurring entr{'y' if created == 1 else 'ies'} "
                          "that came due.", parent=self))

    def _user_chosen(self, _event=None):
        label = self.user_var.get()
        user = next(key for key, name in USERS.items() if name == label)
        self.user_box.selection_clear()
        self.switch_user(user)

    def switch_user(self, user):
        if user == self.user:
            return
        new_db = self.store.open(user)
        self.db.close()
        self.db, self.user = new_db, user
        self.user_var.set(USERS[user])
        self._update_title()
        self.refresh_all()
        self._apply_recurring()

    def _set_icon(self):
        ico = resource_path("assets", "monthwise.ico")
        png = resource_path("assets", "monthwise.png")
        try:
            if ico.exists():
                self.iconbitmap(default=str(ico))
            if png.exists():
                self._icon_image = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._icon_image)
        except tk.TclError:
            pass

    def _next_tab(self, _event):
        tabs = self.notebook.tabs()
        index = tabs.index(self.notebook.select())
        self.notebook.select(tabs[(index + 1) % len(tabs)])
        return "break"

    def refresh_all(self):
        """Mark every tab out of date; redraw the visible one now, others when opened."""
        self._dirty = set(range(len(self.tabs)))
        self.refresh_current()

    def refresh_current(self):
        index = self.notebook.index(self.notebook.select())
        if index in self._dirty:
            self._dirty.discard(index)
            self.tabs[index].refresh()

    def toggle_theme(self):
        self.mode = "dark" if self.mode == "light" else "light"
        self.store.set_pref("theme", self.mode)
        theme.apply(self, self.mode)
        self._update_theme_button()
        self.refresh_all()

    def _update_theme_button(self):
        self.theme_button.configure(
            text="☾  Dark" if self.mode == "light" else "☀  Light")

    def report_callback_exception(self, exc, value, tb):
        details = "".join(traceback.format_exception(exc, value, tb))
        print(details, file=sys.stderr)
        messagebox.showerror(f"{APP_NAME} hit a problem",
                             f"Something went wrong:\n\n{value}\n\nYour saved data is safe.",
                             parent=self)


def _windows_setup():
    if sys.platform != "win32":
        return
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # sharp text on high-DPI screens
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"Monthwise.App.{__version__}")  # own taskbar icon
    except (AttributeError, OSError):
        pass


def run():
    _windows_setup()
    try:
        store = UserStore()
        app = MonthwiseApp(store)
    except Exception as error:  # noqa: BLE001 - show any startup failure to the user
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_NAME, f"Couldn't open your data file:\n\n{error}")
        root.destroy()
        return
    try:
        app.mainloop()
    finally:
        app.db.close()

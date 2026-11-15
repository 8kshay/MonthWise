"""The two users (Demo and My data), each with its own data file, plus app-wide preferences.

Files live in %APPDATA%\\Monthwise\\: demo.db, mine.db and prefs.json.
"""

import json
import os
from pathlib import Path

from . import demo
from .db import Database

USERS = {"demo": "Demo", "mine": "My data"}
DEFAULT_USER = "demo"
LEGACY_FILE = "monthwise.db"  # single data file used before users existed


def data_dir() -> Path:
    override = os.environ.get("MONTHWISE_DATA_DIR")
    if override:
        return Path(override)
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "Monthwise"


class UserStore:
    def __init__(self, folder=None):
        self.folder = Path(folder) if folder else data_dir()
        self.folder.mkdir(parents=True, exist_ok=True)
        self.prefs_file = self.folder / "prefs.json"
        self.prefs = self._load_prefs()
        self._migrate_legacy()

    # ---------- preferences (shared by both users) ----------
    def _load_prefs(self) -> dict:
        try:
            return json.loads(self.prefs_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def get_pref(self, key, default=None):
        return self.prefs.get(key, default)

    def set_pref(self, key, value):
        self.prefs[key] = value
        self.prefs_file.write_text(json.dumps(self.prefs, indent=2), encoding="utf-8")

    # ---------- users ----------
    def path(self, user) -> Path:
        if user not in USERS:
            raise ValueError(f"Unknown user '{user}'.")
        return self.folder / f"{user}.db"

    def last_user(self) -> str:
        user = self.get_pref("user", DEFAULT_USER)
        return user if user in USERS else DEFAULT_USER

    def open(self, user) -> Database:
        """Open a user's data. The Demo user gets sample data the first time."""
        db = Database(self.path(user))
        if user == "demo" and db.get_setting("demo_generated") is None \
                and not db.transactions(limit=1):
            demo.generate(db)
        self.set_pref("user", user)
        return db

    def _migrate_legacy(self):
        """Older versions kept one monthwise.db; it becomes the Demo user's data."""
        legacy = self.folder / LEGACY_FILE
        if not legacy.exists() or self.path("demo").exists():
            return
        old = Database(legacy)
        theme = old.get_setting("theme")
        old.close()
        legacy.rename(self.path("demo"))
        if theme and "theme" not in self.prefs:
            self.set_pref("theme", theme)

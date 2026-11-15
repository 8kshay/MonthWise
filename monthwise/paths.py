"""Find bundled files both when run from source and from the PyInstaller .exe."""

import sys
from pathlib import Path


def resource_path(*parts) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base.joinpath(*parts)

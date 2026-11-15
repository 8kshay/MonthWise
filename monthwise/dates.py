"""Date and month helpers. Months are stored as 'YYYY-MM' keys."""

import datetime as dt

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_FULL = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]

_INPUT_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d",
                  "%d-%m-%y", "%d/%m/%y")


def month_key(day: dt.date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def split_month(key: str) -> tuple[int, int]:
    year, month = key.split("-")
    return int(year), int(month)


def add_months(key: str, n: int) -> str:
    year, month = split_month(key)
    index = year * 12 + (month - 1) + n
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def month_label(key: str, long: bool = True) -> str:
    year, month = split_month(key)
    names = MONTH_FULL if long else MONTH_ABBR
    return f"{names[month - 1]} {year}"


def parse_date(text: str) -> dt.date:
    """Read a date typed by the user (DD-MM-YYYY preferred)."""
    value = (text or "").strip()
    for fmt in _INPUT_FORMATS:
        try:
            parsed = dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
        if parsed.year >= 1900:
            return parsed
    raise ValueError("Enter the date as DD-MM-YYYY, for example 15-11-2026.")


def format_date(day) -> str:
    """Show a date as DD-MM-YYYY. Accepts a date or an ISO string."""
    if isinstance(day, str):
        day = dt.date.fromisoformat(day)
    return day.strftime("%d-%m-%Y")

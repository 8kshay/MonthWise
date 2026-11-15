"""Money helpers. Amounts are stored as whole paise (int) to avoid rounding errors."""

from decimal import Decimal, InvalidOperation

MAX_PAISE = 100_000_000_000  # ₹100 crore per transaction is plenty
RUPEE = "₹"


def parse_amount(text) -> int:
    """Turn user text like '1,250.50' or '₹99' into paise. Raises ValueError."""
    value = "" if text is None else str(text).strip()
    value = value.replace(RUPEE, "").replace(",", "").replace(" ", "")
    if value.lower().startswith("rs."):
        value = value[3:]
    elif value.lower().startswith("rs"):
        value = value[2:]
    if not value:
        raise ValueError("Enter an amount.")
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ValueError("The amount must be a number, for example 250 or 99.50.") from None
    if not number.is_finite():
        raise ValueError("The amount must be a number, for example 250 or 99.50.")
    if number <= 0:
        raise ValueError("The amount must be more than zero.")
    rounded = number.quantize(Decimal("0.01"))
    if rounded != number:
        raise ValueError("Use at most 2 decimal places (paise).")
    paise = int(rounded * 100)
    if paise > MAX_PAISE:
        raise ValueError("That amount is too large.")
    return paise


def _group_indian(rupees: int) -> str:
    digits = str(rupees)
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups + [tail])


def format_inr(paise: int, decimals: bool = True) -> str:
    """₹1,23,456.78 (Indian digit grouping)."""
    paise = int(paise)
    sign = "-" if paise < 0 else ""
    rupees, rest = divmod(abs(paise), 100)
    text = f"{sign}{RUPEE}{_group_indian(rupees)}"
    return f"{text}.{rest:02d}" if decimals else text


def format_compact(paise: int) -> str:
    """Short labels for charts: ₹950, ₹12.5k, ₹1.2L, ₹3.4Cr."""
    sign = "-" if paise < 0 else ""
    rupees = abs(paise) / 100
    for limit, suffix in ((1e7, "Cr"), (1e5, "L"), (1e3, "k")):
        if rupees >= limit:
            text = f"{rupees / limit:.1f}".rstrip("0").rstrip(".")
            return f"{sign}{RUPEE}{text}{suffix}"
    return f"{sign}{RUPEE}{rupees:.0f}"


def to_plain(paise: int) -> str:
    """'1234.50', used for CSV files so spreadsheets read it as a number."""
    sign = "-" if paise < 0 else ""
    rupees, rest = divmod(abs(int(paise)), 100)
    return f"{sign}{rupees}.{rest:02d}"

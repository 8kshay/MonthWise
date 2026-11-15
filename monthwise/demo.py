"""Made-up sample data for the Demo user: 6 months ending this month."""

import datetime as dt
import random

from .dates import add_months, month_key, split_month

# (category, notes, min ₹, max ₹, times per month)
SPENDING = [
    ("Food", ["Swiggy", "Zomato", "BigBasket groceries", "Chai & snacks", "Dinner out",
              "Vegetables", "Milk & bread"], 80, 1800, 12),
    ("Transport", ["Uber", "Ola auto", "Metro recharge", "Petrol", "Rapido"], 60, 2500, 6),
    ("Shopping", ["Amazon", "Myntra", "Flipkart", "D-Mart", "Shoes"], 300, 4500, 3),
    ("Bills", ["Electricity bill", "Gas cylinder", "Water bill"], 400, 2200, 2),
    ("Health", ["Pharmacy", "Doctor visit", "Gym"], 150, 1800, 1),
    ("Entertainment", ["Movie tickets", "BookMyShow", "Bowling"], 250, 1500, 1),
]

RECURRING = [  # (day, paise, kind, category, note)
    (1, 85000_00, "credit", "Salary", "Monthly salary"),
    (5, 22000_00, "debit", "Rent", "Flat rent"),
    (10, 999_00, "debit", "Bills", "Mobile & internet"),
    (15, 649_00, "debit", "Entertainment", "Netflix"),
]

BUDGETS = {"Food": 15000_00, "Shopping": 8000_00, "Entertainment": 3000_00}

MONTHS = 6


def generate(db, today=None, seed=None):
    """Fill an empty database with realistic sample data."""
    today = today or dt.date.today()
    rng = random.Random(seed if seed is not None else today.toordinal())
    current = month_key(today)
    start = add_months(current, -(MONTHS - 1))
    for i in range(MONTHS):
        month = add_months(start, i)
        year, mon = split_month(month)
        last_day = today.day if month == current else 28
        for category, notes, low, high, times in SPENDING:
            for _ in range(times + rng.randint(-1, 2)):
                db.add_transaction(dt.date(year, mon, rng.randint(1, last_day)),
                                   rng.randint(low, high) * 100, "debit", category,
                                   rng.choice(notes))
        if rng.random() < 0.5:
            db.add_transaction(dt.date(year, mon, rng.randint(1, last_day)),
                               rng.choice([1500, 2500, 5000]) * 100, "credit", "Other",
                               rng.choice(["Cashback", "Freelance work", "Refund"]))
    for day, amount, kind, category, note in RECURRING:
        db.add_recurring(day, amount, kind, category, note, start)
    db.apply_recurring(today)
    for category, amount in BUDGETS.items():
        db.set_budget(category, amount)
    db.set_setting("demo_generated", today.isoformat())


def reset(db, today=None):
    """Throw away everything in this database and generate fresh sample data."""
    db.clear_all()
    generate(db, today)

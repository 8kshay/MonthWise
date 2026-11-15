import datetime as dt
import unittest

from monthwise.dates import add_months, format_date, month_label, parse_date
from monthwise.money import format_compact, format_inr, parse_amount, to_plain


class MoneyTests(unittest.TestCase):
    def test_parse_amount(self):
        self.assertEqual(parse_amount("250"), 25000)
        self.assertEqual(parse_amount("99.5"), 9950)
        self.assertEqual(parse_amount("₹1,25,000.75"), 12500075)
        self.assertEqual(parse_amount(" Rs. 40 "), 4000)

    def test_parse_amount_rejects_bad_input(self):
        for bad in ("", "abc", "0", "-5", "1.005", "NaN", "inf", "1e20"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_amount(bad)

    def test_format_inr_uses_indian_grouping(self):
        self.assertEqual(format_inr(0), "₹0.00")
        self.assertEqual(format_inr(99900), "₹999.00")
        self.assertEqual(format_inr(12345678), "₹1,23,456.78")
        self.assertEqual(format_inr(1234567800), "₹1,23,45,678.00")
        self.assertEqual(format_inr(-150000, decimals=False), "-₹1,500")

    def test_compact_and_plain(self):
        self.assertEqual(format_compact(95000), "₹950")
        self.assertEqual(format_compact(1250000), "₹12.5k")
        self.assertEqual(format_compact(12000000), "₹1.2L")
        self.assertEqual(format_compact(300000000), "₹30L")
        self.assertEqual(format_compact(3000000000), "₹3Cr")
        self.assertEqual(to_plain(123450), "1234.50")


class DateTests(unittest.TestCase):
    def test_parse_date_formats(self):
        expected = dt.date(2026, 11, 15)
        for text in ("15-11-2026", "15/11/2026", "2026-11-15", "15.11.2026", "15-11-26"):
            with self.subTest(text=text):
                self.assertEqual(parse_date(text), expected)

    def test_parse_date_rejects_bad_input(self):
        for bad in ("", "31-02-2026", "tomorrow", "2026/15/11"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_date(bad)

    def test_months(self):
        self.assertEqual(add_months("2026-11", 2), "2027-01")
        self.assertEqual(add_months("2026-01", -1), "2025-12")
        self.assertEqual(month_label("2026-11"), "November 2026")
        self.assertEqual(month_label("2026-11", long=False), "Nov 2026")
        self.assertEqual(format_date("2026-11-05"), "05-11-2026")


if __name__ == "__main__":
    unittest.main()

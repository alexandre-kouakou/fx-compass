CURRENCIES = [
    # code, name, symbol, in_ecb
    ("USD", "US Dollar", "$", True),
    ("EUR", "Euro", "€", True),
    ("GBP", "British Pound", "£", True),
    ("JPY", "Japanese Yen", "¥", True),
    ("INR", "Indian Rupee", "₹", True),
    ("AED", "UAE Dirham", "د.إ", False),
    ("CHF", "Swiss Franc", "CHF", True),
    ("CNY", "Chinese Yuan", "¥", True),
    ("AUD", "Australian Dollar", "A$", True),
    ("CAD", "Canadian Dollar", "C$", True),
]
CODES = [c[0] for c in CURRENCIES]
# Currencies Frankfurter/ECB quotes against EUR (EUR itself is always 1).
ECB_SYMBOLS = [c[0] for c in CURRENCIES if c[3] and c[0] != "EUR"]

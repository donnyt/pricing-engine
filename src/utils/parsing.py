from typing import Any


def parse_float(val: Any, absolute: bool = False) -> float:
    """
    Convert the value to a float. Remove commas from strings and return absolute value if specified.
    Returns 0.0 if conversion fails.
    """
    try:
        num = float(str(val).replace(",", ""))
        return abs(num) if absolute else num
    except Exception:
        return 0.0


def parse_int(val: Any) -> int:
    """
    Convert the value to an integer after removing commas. Returns 0 if conversion fails.
    """
    try:
        return int(str(val).replace(",", ""))
    except Exception:
        return 0


def parse_pct(val: Any) -> float:
    """
    Convert a percentage string or numeric value to a float in the range [0,100].
    Example: "75%" -> 75.0, 0.75 -> 75.0.
    """
    try:
        if isinstance(val, str) and "%" in val:
            return float(val.replace("%", "").strip())
        num = float(val)
        # If the number is less than 1, assume it's a decimal and convert to percentage
        if num < 1.0:
            return num * 100
        return num
    except Exception:
        return 0.0


def pct_to_decimal(pct: float) -> float:
    """
    Convert a percentage value to decimal (0-1 range).
    Example: 75.0 -> 0.75.
    """
    return pct / 100.0


def decimal_to_pct(decimal: float) -> float:
    """
    Convert a decimal value to percentage (0-100 range).
    Example: 0.75 -> 75.0.
    """
    return decimal * 100.0


def format_price_int(val: float) -> str:
    """
    Format a number as an integer with thousands separators and no decimal points.
    """
    return f"{int(val):,}"

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
    Convert a percentage string or numeric value to a float in the range [0,1].
    Example: "75%" -> 0.75.
    """
    try:
        if isinstance(val, str) and "%" in val:
            return float(val.replace("%", "").strip()) / 100
        return float(val)
    except Exception:
        return 0.0


def format_price_int(val: float) -> str:
    """
    Format a number as an integer with thousands separators and no decimal points.
    """
    return f"{int(val):,}"

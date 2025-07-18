from typing import Any, Optional

try:
    from src.utils.error_handler import safe_parse, create_error_context
    from src.exceptions import ParsingException
except ImportError:
    # Fallback for when running the script directly
    from utils.error_handler import safe_parse, create_error_context
    from exceptions import ParsingException


def parse_float(
    val: Any, absolute: bool = False, context: Optional[dict] = None
) -> float:
    """
    Convert the value to a float. Remove commas from strings and return absolute value if specified.
    Returns 0.0 if conversion fails.

    Args:
        val: Value to parse
        absolute: Whether to return absolute value
        context: Optional error context for better error reporting

    Returns:
        Parsed float value or 0.0 if parsing fails
    """
    if context is None:
        context = create_error_context("parse_float", additional_info={"value": val})

    def _parse_float_internal(v: Any) -> float:
        return float(str(v).replace(",", ""))

    parsed = safe_parse(_parse_float_internal, val, "float", context, default=0.0)
    return abs(parsed) if absolute else parsed


def parse_int(val: Any, context: Optional[dict] = None) -> int:
    """
    Convert the value to an integer after removing commas. Returns 0 if conversion fails.

    Args:
        val: Value to parse
        context: Optional error context for better error reporting

    Returns:
        Parsed integer value or 0 if parsing fails
    """
    if context is None:
        context = create_error_context("parse_int", additional_info={"value": val})

    def _parse_int_internal(v: Any) -> int:
        # Convert to float first to handle decimal strings, then to int
        return int(float(str(v).replace(",", "")))

    return safe_parse(_parse_int_internal, val, "integer", context, default=0)


def parse_pct(val: Any, context: Optional[dict] = None) -> float:
    """
    Convert a percentage string or numeric value to a float in the range [0,100].
    Example: "75%" -> 75.0, 0.75 -> 75.0.

    Args:
        val: Value to parse
        context: Optional error context for better error reporting

    Returns:
        Parsed percentage value or 0.0 if parsing fails
    """
    if context is None:
        context = create_error_context("parse_pct", additional_info={"value": val})

    def _parse_pct_internal(v: Any) -> float:
        if isinstance(v, str) and "%" in v:
            return float(v.replace("%", "").strip())
        num = float(v)
        # If the number is less than 1, assume it's a decimal and convert to percentage
        if num < 1.0:
            return num * 100
        return num

    return safe_parse(_parse_pct_internal, val, "percentage", context, default=0.0)


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
    Returns "Not set" if the value is None.
    """
    if val is None:
        return "Not set"
    return f"{int(val):,}"

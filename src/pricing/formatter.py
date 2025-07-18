"""
Response Formatter Service

This module handles formatting pricing data for different output formats,
following the Single Responsibility Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.pricing.models import PricingCLIOutput


class ResponseFormatterInterface(ABC):
    """Abstract interface for response formatting following Interface Segregation Principle."""

    @abstractmethod
    def format_pricing_response(self, pricing_data: PricingCLIOutput) -> str:
        """Format pricing data for the specific output format."""
        pass


class GoogleChatFormatter(ResponseFormatterInterface):
    """
    Formats pricing data for Google Chat plain text output.

    Follows Single Responsibility Principle - only handles Google Chat formatting.
    """

    def format_pricing_response(self, pricing_data: PricingCLIOutput) -> str:
        """
        Format pricing data as plain text for Google Chat.

        Args:
            pricing_data: Pricing data to format

        Returns:
            Formatted plain text string
        """
        location = pricing_data.building_name
        published_price = pricing_data.published_price
        recommended_price = pricing_data.recommended_price
        breakeven_price = pricing_data.breakeven_price
        sold_price_per_po_seat_actual = pricing_data.sold_price_per_po_seat_actual
        occupancy_pct = pricing_data.occupancy_pct
        losing_money = pricing_data.losing_money
        llm_reasoning = pricing_data.llm_reasoning
        manual_override = pricing_data.manual_override

        # Format prices with thousands separators
        def format_price(price: Optional[float], nearest: int = 1) -> str:
            if price is None:
                return "Not set"
            import math

            return f"{int(round(price / nearest) * nearest):,}"

        breakeven_target_pct = pricing_data.target_breakeven_occupancy_pct
        breakeven_actual_pct = pricing_data.actual_breakeven_occupancy_pct

        # Add smart target indicator
        target_indicator = (
            " (Smart Target)" if pricing_data.is_smart_target else " (Static Target)"
        )

        # Build plain text response
        lines = [
            f"\U0001f3e2 {location.title()}",
            "=" * (len(location) + 4),
            "",
            f"Latest Occupancy: {occupancy_pct:.1f}%",
            (
                f"Actual Breakeven Occupancy: {breakeven_actual_pct:.1f}%"
                if breakeven_actual_pct is not None
                else "Actual Breakeven Occupancy: Not available"
            ),
            f"Sold Price/Seat (Actual): {format_price(sold_price_per_po_seat_actual, 10000)}",
            "",
            f"Target Breakeven Occupancy: {breakeven_target_pct:.1f}%{target_indicator}",
            (
                f"Published Price: {format_price(published_price)} (Valid from Jul 2025)"
                if published_price is not None
                else "Published Price: Not set"
            ),
            f"Recommended Price: {format_price(recommended_price)}",
            f"Bottom Price: {format_price(breakeven_price, 50000)}",
            "",
        ]

        # Add loss warning if applicable
        if losing_money:
            lines.extend(["⚠️  WARNING: Location is currently losing money ⚠️", ""])

        # Add manual override info if present
        if manual_override:
            lines.extend(
                [
                    "Manual Override Applied:",
                    f"  • Overridden by: {manual_override.overridden_by}",
                    f"  • Reason: {manual_override.reason}",
                    f"  • Original price: {format_price(manual_override.original_price)}",
                    "",
                ]
            )

        # Add LLM reasoning if available and meaningful
        if llm_reasoning and not llm_reasoning.startswith("[LLM reasoning unavailable"):
            lines.extend(["Reasoning:", "-" * 10, llm_reasoning, ""])

        return "\n".join(lines)


class APIFormatter(ResponseFormatterInterface):
    """
    Formats pricing data for API JSON output.

    Follows Single Responsibility Principle - only handles API formatting.
    """

    def format_pricing_response(self, pricing_data: PricingCLIOutput) -> Dict[str, Any]:
        """
        Format pricing data as JSON for API responses.

        Args:
            pricing_data: Pricing data to format

        Returns:
            Formatted dictionary for JSON serialization
        """
        return pricing_data.model_dump()


# Factory for getting formatters
def get_formatter(formatter_type: str) -> ResponseFormatterInterface:
    """
    Factory function to get the appropriate formatter.

    Follows Open/Closed Principle - easy to add new formatters without modifying existing code.

    Args:
        formatter_type: Type of formatter ('google_chat' or 'api')

    Returns:
        Appropriate formatter instance

    Raises:
        ValueError: If formatter type is not supported
    """
    formatters = {"google_chat": GoogleChatFormatter(), "api": APIFormatter()}

    if formatter_type not in formatters:
        raise ValueError(f"Unsupported formatter type: {formatter_type}")

    return formatters[formatter_type]

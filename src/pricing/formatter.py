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
        occupancy_pct = pricing_data.occupancy_pct
        breakeven_pct = pricing_data.breakeven_occupancy_pct
        losing_money = pricing_data.losing_money
        llm_reasoning = pricing_data.llm_reasoning
        manual_override = pricing_data.manual_override

        # Format prices with thousands separators
        def format_price(price: Optional[float]) -> str:
            if price is None:
                return "Not set"
            return f"{price:,.0f}"

        # Build plain text response
        lines = [
            f"🏢 {location.title()}",
            "=" * (len(location) + 4),
            "",
            f"Published Price: {format_price(published_price)}",
            f"Recommended Price: {format_price(recommended_price)}",
            f"Current Occupancy: {occupancy_pct:.1f}%",
            f"Breakeven Occupancy: {breakeven_pct:.1f}%",
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

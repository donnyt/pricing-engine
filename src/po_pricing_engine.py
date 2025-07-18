import yaml
from typing import Any, Dict
import os
from pydantic import BaseModel, Field
from src.utils.parsing import parse_float, parse_int, parse_pct
from src.pricing.models import (
    DynamicPricingTier,
    LocationData,
    PricingRules,
    PricingResult,
    ManualOverrideInfo,
    PricingCLIOutput,
)
from src.pricing.rules import build_rules
from src.pricing.calculator import PricingCalculator

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/pricing_rules.yaml")


def load_pricing_rules(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Load pricing rules from the YAML config file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_merged_pricing_data(target_date: str = None, target_location: str = None):
    """
    Load and merge data from both monthly expense data and daily occupancy data.

    This function is now a thin wrapper around DataLoaderService for backward compatibility.
    Consider using DataLoaderService directly for new code.

    Args:
        target_date: Date in 'YYYY-MM-DD' format. If None, uses today's date.
        target_location: Specific location to load data for. If None, loads all locations.

    Returns:
        DataFrame with merged data for pricing calculations.
    """
    from src.data.loader import DataLoaderService

    data_loader = DataLoaderService()
    return data_loader.load_merged_pricing_data(
        target_date, target_location, auto_fetch=True
    )


# Sample usage (for demonstration/testing)
if __name__ == "__main__":
    import pandas as pd

    config = load_pricing_rules()

    # Load merged data
    df = load_merged_pricing_data()

    if df.empty:
        print("No data available for pricing calculations.")
        exit(1)

    calculator = PricingCalculator(config)
    for idx, row in df.iterrows():
        loc = row.get("building_name")
        if not loc:
            continue
        if loc.strip().lower() == "holding":
            continue
        total_po_seats = parse_int(row.get("total_po_seats"))
        if total_po_seats == 0:
            continue

        # Use daily occupancy data if available, fallback to monthly
        daily_occupancy = row.get("po_seats_occupied_actual_pct")
        monthly_occupancy = row.get("po_seats_actual_occupied_pct")

        # Prefer daily occupancy data, fallback to monthly
        occupancy_pct = (
            parse_float(daily_occupancy)
            if daily_occupancy is not None
            else parse_float(monthly_occupancy)
        )

        try:
            location_data = LocationData(
                name=loc,
                exp_total_po_expense_amount=parse_float(
                    row.get("exp_total_po_expense_amount"), absolute=True
                ),
                avg_exp_total_po_expense_amount=parse_float(
                    row.get("avg_exp_total_po_expense_amount"), absolute=True
                ),
                po_seats_occupied_actual_pct=occupancy_pct,
                po_seats_occupied_pct=parse_float(row.get("po_seats_occupied_pct")),
                total_po_seats=total_po_seats,
            )
            pricing_result = calculator.calculate_pricing(location_data)
            print(
                f"{loc}: Breakeven = {pricing_result.breakeven_price:.2f}, Base = {pricing_result.base_price:.2f}, Final after margin = {pricing_result.price_with_margin:.2f}, Clamped = {pricing_result.final_price:.2f}"
            )
        except Exception as e:
            print(f"{loc}: Error calculating price: {e}")

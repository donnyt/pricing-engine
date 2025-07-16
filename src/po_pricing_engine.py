import yaml
from typing import Any, Dict
import os
from pydantic import BaseModel, Field
from utils.parsing import parse_float, parse_int, parse_pct
from pricing.models import (
    get_location_rules,
    DynamicPricingTier,
    LocationData,
    PricingRules,
    PricingResult,
    ManualOverrideInfo,
    PricingCLIOutput,
)
from pricing.calculator import PricingCalculator

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/pricing_rules.yaml")


def load_pricing_rules(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Load pricing rules from the YAML config file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# Sample usage (for demonstration/testing)
if __name__ == "__main__":
    from src.sqlite_storage import load_from_sqlite
    import pandas as pd

    config = load_pricing_rules()
    try:
        df = load_from_sqlite("pnl_sms_by_month")
        print(f"Loaded {len(df)} rows from SQLite table 'pnl_sms_by_month'.")
    except Exception as e:
        print(f"Error loading data from SQLite: {e}")
        df = pd.DataFrame()

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
        try:
            location_data = LocationData(
                name=loc,
                exp_total_po_expense_amount=parse_float(
                    row.get("exp_total_po_expense_amount"), absolute=True
                ),
                avg_exp_total_po_expense_amount=parse_float(
                    row.get("avg_exp_total_po_expense_amount"), absolute=True
                ),
                po_seats_actual_occupied_pct=parse_float(
                    row.get("po_seats_actual_occupied_pct")
                ),
                po_seats_occupied_pct=parse_float(row.get("po_seats_occupied_pct")),
                total_po_seats=total_po_seats,
            )
            pricing_result = calculator.calculate_pricing(location_data)
            print(
                f"{loc}: Breakeven = {pricing_result.breakeven_price:.2f}, Base = {pricing_result.base_price:.2f}, Final after margin = {pricing_result.price_with_margin:.2f}, Clamped = {pricing_result.final_price:.2f}"
            )
        except Exception as e:
            print(f"{loc}: Error calculating price: {e}")

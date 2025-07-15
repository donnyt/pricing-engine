import yaml
from typing import Any, Dict, Optional, List
import os
from pydantic import BaseModel, Field

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config/pricing_rules.yaml")


def load_pricing_rules(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Load pricing rules from the YAML config file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_location_rules(location: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve pricing rules for a given location, falling back to global margin_of_safety if not set.
    Returns a dict with keys: min_price, max_price, margin_of_safety, dynamic_pricing_tiers, target_breakeven_occupancy.
    """
    loc_rules = config.get("locations", {}).get(location, {})
    margin_of_safety = loc_rules.get("margin_of_safety", config.get("margin_of_safety"))
    min_price = loc_rules.get("min_price")
    max_price = loc_rules.get("max_price")
    tiers = config.get("dynamic_pricing_tiers", [])
    target_breakeven_occupancy = loc_rules.get("target_breakeven_occupancy")
    return {
        "min_price": min_price,
        "max_price": max_price,
        "margin_of_safety": margin_of_safety,
        "dynamic_pricing_tiers": tiers,
        "target_breakeven_occupancy": target_breakeven_occupancy,
    }


class DynamicPricingTier(BaseModel):
    min_occupancy: float
    max_occupancy: float
    multiplier: float


class LocationData(BaseModel):
    name: str
    exp_total_po_expense_amount: float
    po_seats_actual_occupied_pct: float
    total_po_seats: int
    # Add other fields as needed


class PricingRules(BaseModel):
    min_price: Optional[float]
    max_price: Optional[float]
    margin_of_safety: float
    dynamic_pricing_tiers: List[DynamicPricingTier]


class PricingResult(BaseModel):
    location: str
    recommended_price: float
    manual_override: Optional[Dict[str, Any]] = None
    latest_occupancy: float
    breakeven_occupancy_pct: float
    is_losing_money: bool
    reasoning: Optional[str]


def calculate_breakeven_price_per_pax(
    location_data: LocationData, target_breakeven_occupancy: float
) -> float:
    """
    Calculate the target breakeven price per pax for a location.
    Formula: breakeven_price = total_expense / (total_seats * target_breakeven_occupancy)
    Result is rounded to the nearest 50,000.
    """
    if location_data.total_po_seats == 0 or target_breakeven_occupancy == 0:
        raise ValueError(
            "Total PO seats and target breakeven occupancy must be greater than zero."
        )
    raw_price = location_data.exp_total_po_expense_amount / (
        location_data.total_po_seats * target_breakeven_occupancy
    )
    # Round to nearest 50,000
    rounded_price = round(raw_price / 50000) * 50000
    return rounded_price


def get_dynamic_pricing_multiplier(
    occupancy_pct: float, tiers: List[DynamicPricingTier]
) -> float:
    """
    Get the dynamic pricing multiplier for a given occupancy percentage.
    """
    for tier in tiers:
        if tier.min_occupancy < occupancy_pct <= tier.max_occupancy:
            return tier.multiplier
    # Fallback: if not matched, return 1.0
    return 1.0


def apply_dynamic_pricing(
    breakeven_price: float, occupancy_pct: float, tiers: List[DynamicPricingTier]
) -> float:
    """
    Apply the dynamic pricing multiplier to the breakeven price and round to nearest 50,000.
    """
    multiplier = get_dynamic_pricing_multiplier(occupancy_pct, tiers)
    base_price = breakeven_price * multiplier
    return round(base_price / 50000) * 50000


def apply_margin_of_safety(base_price: float, margin_of_safety: float) -> float:
    """
    Apply the margin of safety to the base price and round to nearest 50,000.
    """
    price_with_margin = base_price * (1 + margin_of_safety)
    return round(price_with_margin / 50000) * 50000


def enforce_min_max_price(
    price: float, min_price: Optional[float], max_price: Optional[float]
) -> float:
    """
    Enforce min and max price boundaries. If min or max is None, ignore that bound.
    """
    if min_price is not None and price < min_price:
        return min_price
    if max_price is not None and price > max_price:
        return max_price
    return price


# Sample usage (for demonstration/testing)
if __name__ == "__main__":
    from src.sqlite_storage import load_from_sqlite
    import pandas as pd

    config = load_pricing_rules()
    # Load all Zoho data for May 2025 from SQLite
    try:
        df = load_from_sqlite("pnl_sms_by_month")
        print(f"Loaded {len(df)} rows from SQLite table 'pnl_sms_by_month'.")
    except Exception as e:
        print(f"Error loading data from SQLite: {e}")
        df = pd.DataFrame()

    # Map each row to LocationData and run the pricing pipeline
    for idx, row in df.iterrows():
        loc = row.get("building_name")
        if not loc:
            print(f"Row {idx}: No location name found, skipping.")
            continue
        rules_dict = get_location_rules(loc, config)
        rules = PricingRules(
            min_price=rules_dict["min_price"],
            max_price=rules_dict["max_price"],
            margin_of_safety=rules_dict["margin_of_safety"],
            dynamic_pricing_tiers=[
                DynamicPricingTier(**tier)
                for tier in rules_dict["dynamic_pricing_tiers"]
            ],
        )
        try:

            def parse_float(val, absolute=False):
                try:
                    num = float(str(val).replace(",", ""))
                    return abs(num) if absolute else num
                except Exception:
                    return 0.0

            def parse_int(val):
                try:
                    return int(str(val).replace(",", ""))
                except Exception:
                    return 0

            location_data = LocationData(
                name=loc,
                exp_total_po_expense_amount=parse_float(
                    row["exp_total_po_expense_amount"], absolute=True
                ),
                po_seats_actual_occupied_pct=parse_float(
                    row["po_seats_actual_occupied_pct"]
                ),
                total_po_seats=parse_int(row["total_po_seats"]),
            )
            print(
                f"{loc}: config target_breakeven_occupancy = {rules_dict.get('target_breakeven_occupancy')}"
            )
            # Use target_breakeven_occupancy from config if available, else default to 0.7
            target_breakeven_occupancy = rules_dict.get("target_breakeven_occupancy")
            if target_breakeven_occupancy is None:
                target_breakeven_occupancy = 0.7
            print(
                f"{loc}: expense={location_data.exp_total_po_expense_amount}, seats={location_data.total_po_seats}, occupancy={target_breakeven_occupancy}"
            )
            breakeven_price = calculate_breakeven_price_per_pax(
                location_data, target_breakeven_occupancy
            )
            base_price = apply_dynamic_pricing(
                breakeven_price,
                location_data.po_seats_actual_occupied_pct,
                rules.dynamic_pricing_tiers,
            )
            final_price = apply_margin_of_safety(base_price, rules.margin_of_safety)
            clamped_price = enforce_min_max_price(
                final_price, rules.min_price, rules.max_price
            )
            print(
                f"{loc}: Breakeven = {breakeven_price:.2f}, Base = {base_price:.2f}, Final after margin = {final_price:.2f}, Clamped = {clamped_price:.2f}"
            )
        except Exception as e:
            print(f"{loc}: Error calculating price: {e}")

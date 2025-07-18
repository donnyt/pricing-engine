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
    import pandas as pd
    from datetime import date, datetime, timedelta

    """
    Load and merge data from both monthly expense data and daily occupancy data.
    Optimized to load only necessary data:
    - 3 months of expense data for averaging
    - Daily occupancy data for specific location and date

    Args:
        target_date: Date in 'YYYY-MM-DD' format. If None, uses today's date.
        target_location: Specific location to load data for. If None, loads all locations.

    Returns:
        DataFrame with merged data for pricing calculations.
    """
    from src.sqlite_storage import load_from_sqlite

    # Use today's date if not specified
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    # Parse target date to get year and month
    target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
    target_year = target_datetime.year
    target_month = target_datetime.month

    # Calculate 3 months prior for expense averaging
    three_months_ago = target_datetime - timedelta(days=90)
    start_year = three_months_ago.year
    start_month = three_months_ago.month

    try:
        # Load monthly expense data for the last 3 months
        monthly_df = load_from_sqlite("pnl_sms_by_month")

        # Filter to last 3 months
        monthly_df = monthly_df[
            ((monthly_df["year"] == target_year) & (monthly_df["month"] >= start_month))
            | (
                (monthly_df["year"] == start_year)
                & (monthly_df["month"] >= start_month)
            )
        ]

        # Filter by location if specified
        if target_location:
            monthly_df = monthly_df[
                monthly_df["building_name"].str.lower() == target_location.lower()
            ]

        print(
            f"Loaded {len(monthly_df)} rows from monthly expense data (last 3 months)."
        )
    except Exception as e:
        print(f"Error loading monthly expense data: {e}")
        monthly_df = pd.DataFrame()

    try:
        # Load daily occupancy data for target date and location
        daily_df = load_from_sqlite("private_office_occupancies_by_building")

        # Filter to target date
        if not daily_df.empty and "date" in daily_df.columns:
            daily_df = daily_df[daily_df["date"] == target_date]

            # Filter by location if specified
            if target_location:
                daily_df = daily_df[
                    daily_df["building_name"].str.lower() == target_location.lower()
                ]

            print(
                f"Loaded {len(daily_df)} rows from daily occupancy data for {target_date}."
            )

            # Check if today's data exists, if not fetch from Zoho
            if daily_df.empty:
                print(
                    f"No daily occupancy data found for {target_date}. Fetching from Zoho Analytics..."
                )
                try:
                    from src.zoho_integration import (
                        upsert_private_office_occupancies_by_building,
                    )

                    upsert_private_office_occupancies_by_building(target_date)
                    print(
                        f"Successfully fetched and saved daily occupancy data for {target_date}."
                    )
                    # Reload the filtered data after fetching
                    daily_df = load_from_sqlite(
                        "private_office_occupancies_by_building"
                    )
                    daily_df = daily_df[daily_df["date"] == target_date]
                    if target_location:
                        daily_df = daily_df[
                            daily_df["building_name"].str.lower()
                            == target_location.lower()
                        ]
                    print(f"Reloaded {len(daily_df)} rows from daily occupancy data.")
                except Exception as e:
                    print(f"Error fetching daily occupancy data from Zoho: {e}")
                    print("Continuing with available data...")
    except Exception as e:
        print(f"Error loading daily occupancy data: {e}")
        daily_df = pd.DataFrame()

    # Merge the dataframes on building_name
    if not monthly_df.empty and not daily_df.empty:
        merged_df = pd.merge(
            monthly_df,
            daily_df,
            on="building_name",
            how="left",
            suffixes=("_monthly", "_daily"),
        )
        print(f"Merged data contains {len(merged_df)} rows.")
        return merged_df
    elif not monthly_df.empty:
        print("Using only monthly data (no daily occupancy data available).")
        return monthly_df
    else:
        print("No data available from either table.")
        return pd.DataFrame()


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

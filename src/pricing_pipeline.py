from typing import List
import pandas as pd
from src.pricing.models import (
    PricingRules,
    DynamicPricingTier,
    LocationData,
    PricingCLIOutput,
)
from src.pricing.rules import build_rules
from src.utils.parsing import parse_float, parse_int, parse_pct
from src.pricing.calculator import PricingCalculator
from src.sqlite_storage import get_published_price
from src.llm_reasoning import generate_llm_reasoning
from src.po_pricing_engine import load_merged_pricing_data
from src.data.loader import DataLoaderService


def run_pricing_pipeline(
    input_df: pd.DataFrame = None,
    config: dict = None,
    target_year: int = None,
    target_month: int = None,
    target_date: str = None,
    verbose: bool = False,
    auto_fetch: bool = True,
    target_location: str = None,
) -> List[PricingCLIOutput]:
    """
    Process the input data using pricing rules and return a list of PricingCLIOutput.
    Updated to use daily occupancy data from private_office_occupancies_by_building table.

    Args:
        input_df: Optional DataFrame. If None, will load merged data from both tables.
        config: Pricing configuration dictionary.
        target_year: Target year for monthly data (default: current year).
        target_month: Target month for monthly data (default: current month).
        target_date: Target date for daily occupancy data in 'YYYY-MM-DD' format (default: today).
        verbose: Whether to include LLM reasoning in output.
        auto_fetch: Whether to automatically fetch daily occupancy data from Zoho if not available (default: True).
    """
    import datetime

    outputs: List[PricingCLIOutput] = []

    # Load merged data if not provided
    if input_df is None:
        # Default target_date to today if not provided
        if target_date is None:
            target_date = datetime.date.today().strftime("%Y-%m-%d")
        # If target_year and target_month are provided but not target_date, ignore them (target_date takes precedence)
        # Use DataLoaderService for consistent data loading
        data_loader = DataLoaderService()
        input_df = data_loader.load_merged_pricing_data(
            target_date, target_location, auto_fetch
        )

    if input_df.empty:
        return outputs

    # Default to current year/month if not provided
    now = datetime.datetime.now()
    if target_year is None:
        target_year = now.year
    if target_month is None:
        target_month = now.month

    # Normalize building names to avoid trailing spaces or invisible characters
    input_df["building_name"] = input_df["building_name"].astype(str).str.strip()

    calculator = PricingCalculator(config)

    # Process only unique locations to avoid duplicates
    processed_locations = set()

    for _, row in input_df.iterrows():
        loc = str(row["building_name"]).strip()

        # Skip if we've already processed this location
        if loc in processed_locations:
            continue
        processed_locations.add(loc)

        total_po_seats = parse_int(row.get("total_po_seats"))

        if not loc:
            continue
        if str(loc).strip().lower() == "holding":
            continue
        if total_po_seats == 0:
            continue

        # Calculate 7-day average occupancy for this location
        if "po_seats_occupied_actual_pct" in input_df.columns:
            location_daily_data = input_df[
                (input_df["building_name"] == loc)
                & (input_df["po_seats_occupied_actual_pct"].notna())
            ]
        else:
            # If the column doesn't exist, use empty DataFrame
            location_daily_data = pd.DataFrame()

        # Use daily occupancy data if available, fallback to monthly
        if not location_daily_data.empty:
            # Calculate 7-day average occupancy
            daily_occupancies = []
            for occ in location_daily_data["po_seats_occupied_actual_pct"]:
                parsed = parse_pct(occ)
                if parsed is not None:
                    daily_occupancies.append(parsed)
                else:
                    print(
                        f"Warning: Could not parse po_seats_occupied_actual_pct value '{occ}' for location {loc}"
                    )
            if daily_occupancies:
                occupancy_pct = round(
                    sum(daily_occupancies) / len(daily_occupancies), 1
                )
                data_source = "7-day average"
                # Count unique dates to get actual number of days
                unique_dates = location_daily_data["date"].nunique()
                daily_occupancy = f"{unique_dates} days avg"
            else:
                # Fallback to single day data with column fallback logic
                occupancy_pct = _get_occupancy_with_fallback(row)
                data_source = "single day"
                daily_occupancy = row.get("po_seats_occupied_actual_pct")
        else:
            # Fallback to single day data with column fallback logic
            occupancy_pct = _get_occupancy_with_fallback(row)
            if occupancy_pct is not None:
                occupancy_pct = round(occupancy_pct, 1)
            data_source = "single day"
            daily_occupancy = row.get("po_seats_occupied_actual_pct")

        monthly_occupancy = row.get("po_seats_actual_occupied_pct")

        # Fallback to monthly if no daily data available
        if occupancy_pct is None:
            occupancy_pct = _get_occupancy_with_fallback(row)
            if occupancy_pct is not None:
                occupancy_pct = round(occupancy_pct, 1)
            data_source = "monthly"
            if occupancy_pct is None:
                print(
                    f"Warning: No occupancy data available for {loc} (row: {row.to_dict()})"
                )
                continue

        # Debug output for Pacific Place
        if loc.lower() == "pacific place":
            # Calculate the date range for the 7-day average
            from datetime import datetime, timedelta

            if row.get("date"):
                end_date = row.get("date")
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    start_dt = end_dt - timedelta(
                        days=(location_daily_data["date"].nunique() - 1)
                    )
                    date_range_str = f"({start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')})"
                except Exception:
                    date_range_str = ""
            else:
                date_range_str = ""
            print("\n-------------------------------")
            print("\U0001f3e2 Pacific Place Occupancy Data")
            print("-------------------------------")
            print(
                f"• 7-Day Average Daily Occupancy: {daily_occupancy} {date_range_str}"
            )
            print(f"• Monthly Occupancy (Actual):    {monthly_occupancy}")
            if occupancy_pct is not None:
                print(
                    f"• Final Occupancy Used:          {occupancy_pct:.1f}%   \u2190 (used for pricing calculation)"
                )
            else:
                print(f"• Final Occupancy Used:          None")
            print(f"• Data Source:                   {data_source}")
            print("-------------------------------")

        if occupancy_pct is None:
            print(f"Warning: No occupancy data available for {loc}")
            continue

        # Calculate 3-month average expense for this location
        location_monthly_data = input_df[
            (input_df["building_name"] == loc)
            & (input_df["year"] == target_year)
            & (
                input_df["month"].isin(
                    [target_month - 2, target_month - 1, target_month]
                )
            )
        ]

        if location_monthly_data.empty:
            # Fallback to current month if no 3-month data available
            avg_exp = abs(parse_float(row.get("exp_total_po_expense_amount")))
        else:
            # Calculate 3-month average
            expenses = [
                abs(parse_float(exp))
                for exp in location_monthly_data["exp_total_po_expense_amount"]
            ]
            avg_exp = sum(expenses) / len(expenses)

        # Fetch published price for this location/month
        published_price = get_published_price(loc, target_year, target_month)

        location_data = LocationData(
            name=loc,
            exp_total_po_expense_amount=parse_float(
                row.get("exp_total_po_expense_amount"), absolute=True
            ),
            avg_exp_total_po_expense_amount=avg_exp,
            po_seats_occupied_actual_pct=occupancy_pct,
            po_seats_occupied_pct=parse_float(row.get("po_seats_occupied_pct")),
            total_po_seats=total_po_seats,
            published_price=published_price,
        )

        try:
            pricing_result = calculator.calculate_pricing(location_data)

            # Prepare context for LLM reasoning
            llm_context = {
                "location": loc,
                "recommended_price": pricing_result.final_price,
                "occupancy_pct": location_data.po_seats_occupied_actual_pct,
                "breakeven_occupancy_pct": pricing_result.breakeven_occupancy_pct,
                "published_price": location_data.published_price,
            }

            llm_reasoning = generate_llm_reasoning(llm_context) if verbose else None

            output = PricingCLIOutput(
                building_name=loc,
                occupancy_pct=round(location_data.po_seats_occupied_actual_pct, 2),
                breakeven_occupancy_pct=round(
                    pricing_result.breakeven_occupancy_pct, 2
                ),
                dynamic_multiplier=pricing_result.dynamic_multiplier,
                recommended_price=pricing_result.final_price,
                losing_money=pricing_result.losing_money,
                manual_override=None,
                llm_reasoning=llm_reasoning,
                published_price=location_data.published_price,
            )
            outputs.append(output)
        except Exception as e:
            print(
                f"ERROR: Calculation failed for location '{loc}' (row: {row.to_dict()}): {e}"
            )

    return outputs


def _get_occupancy_with_fallback(row):
    """
    Get occupancy percentage with fallback logic for different column names.

    Args:
        row: DataFrame row containing occupancy data

    Returns:
        float: Parsed occupancy percentage or None if not available
    """
    # Try different column names in order of preference
    columns_to_try = [
        "po_seats_occupied_actual_pct",
        "po_seats_actual_occupied_pct",
        "po_seats_occupied_pct",
    ]

    for col in columns_to_try:
        if col in row and row[col] is not None:
            parsed = parse_pct(row[col])
            if parsed is not None:
                return parsed

    return None

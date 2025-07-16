from typing import List
import pandas as pd
from pricing.models import (
    get_location_rules,
    PricingRules,
    DynamicPricingTier,
    LocationData,
    PricingCLIOutput,
)
from utils.parsing import parse_float, parse_int, parse_pct
from pricing.calculator import PricingCalculator
from sqlite_storage import get_published_price
from llm_reasoning import generate_llm_reasoning


def run_pricing_pipeline(
    input_df: pd.DataFrame,
    config: dict,
    target_year: int = None,
    target_month: int = None,
    verbose: bool = False,
) -> List[PricingCLIOutput]:
    """
    Process the input data using pricing rules and return a list of PricingCLIOutput.
    Only process the target year and month (default: current year/month).
    For each location and target month, use the latest occupancy, but average the previous 3 months' expenses for calculation.
    """
    import datetime

    outputs: List[PricingCLIOutput] = []
    if input_df.empty:
        return outputs
    # Ensure year and month columns are present and sorted
    if "year" not in input_df.columns or "month" not in input_df.columns:
        raise ValueError("Input data must have 'year' and 'month' columns.")
    input_df = input_df.sort_values(["building_name", "year", "month"])
    # Normalize building names to avoid trailing spaces or invisible characters
    input_df["building_name"] = input_df["building_name"].astype(str).str.strip()
    # Ensure year and month columns are int for filtering
    input_df["year"] = input_df["year"].astype(int)
    input_df["month"] = input_df["month"].astype(int)
    # Default to current year/month if not provided
    now = datetime.datetime.now()
    if target_year is None:
        target_year = now.year
    if target_month is None:
        target_month = now.month
    # Group by location and month, then filter to target month
    grouped = input_df.groupby(["building_name", "year", "month"]).first().reset_index()
    grouped = grouped[
        (grouped["year"] == target_year) & (grouped["month"] == target_month)
    ]
    calculator = PricingCalculator(config)
    for _, row in grouped.iterrows():
        loc = str(row["building_name"]).strip()
        year = row["year"]
        month = row["month"]
        total_po_seats = parse_int(row.get("total_po_seats"))
        if not loc:
            continue
        if str(loc).strip().lower() == "holding":
            continue
        if total_po_seats == 0:
            continue
        loc_df = input_df[(input_df["building_name"] == loc)]

        # Get all previous months for this location (before target month)
        prev_months = loc_df[
            (loc_df["year"] < year)
            | ((loc_df["year"] == year) & (loc_df["month"] < month))
        ].sort_values(["year", "month"], ascending=False)

        # Use up to 3 most recent months, but accept whatever is available
        prev_months = prev_months.head(3)

        # Calculate average expense from available historical data
        if not prev_months.empty:
            avg_exp = (
                prev_months["exp_total_po_expense_amount"]
                .apply(lambda x: abs(parse_float(x)))
                .mean()
            )
        else:
            # Fallback to current month if no historical data
            avg_exp = abs(parse_float(row.get("exp_total_po_expense_amount")))

        occupancy_val = parse_pct(row.get("po_seats_occupied_pct"))
        raw_actual_occupancy = row.get("po_seats_actual_occupied_pct")
        parsed_actual_occupancy = parse_pct(raw_actual_occupancy)
        # Fetch published price for this location/month
        published_price = get_published_price(loc, year, month)
        location_data = LocationData(
            name=loc,
            exp_total_po_expense_amount=parse_float(
                row.get("exp_total_po_expense_amount"), absolute=True
            ),
            avg_exp_total_po_expense_amount=avg_exp,
            po_seats_actual_occupied_pct=parsed_actual_occupancy,
            po_seats_occupied_pct=occupancy_val,
            total_po_seats=total_po_seats,
            published_price=published_price,
        )
        try:
            pricing_result = calculator.calculate_pricing(location_data)
            # Prepare context for LLM reasoning
            llm_context = {
                "location": loc,
                "recommended_price": pricing_result.final_price,
                "occupancy_pct": location_data.po_seats_actual_occupied_pct,
                "breakeven_occupancy_pct": pricing_result.breakeven_occupancy_pct,
                "published_price": location_data.published_price,
            }
            llm_reasoning = generate_llm_reasoning(llm_context)
            output = PricingCLIOutput(
                building_name=loc,
                occupancy_pct=(
                    round(location_data.po_seats_actual_occupied_pct, 2)
                    if location_data.po_seats_actual_occupied_pct is not None
                    else None
                ),
                breakeven_occupancy_pct=(
                    round(pricing_result.breakeven_occupancy_pct, 2)
                    if pricing_result.breakeven_occupancy_pct is not None
                    else None
                ),
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

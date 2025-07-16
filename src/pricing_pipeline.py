from typing import List
import pandas as pd
from src.po_pricing_engine import (
    load_pricing_rules,
    get_location_rules,
    PricingRules,
    DynamicPricingTier,
    LocationData,
    calculate_breakeven_price_per_pax,
    apply_dynamic_pricing,
    apply_margin_of_safety,
    enforce_min_max_price,
    PricingCLIOutput,
)
from src.utils.parsing import parse_float, parse_int, parse_pct


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
    print(
        "DEBUG: Unique building names in DataFrame:", input_df["building_name"].unique()
    )
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
    for _, row in grouped.iterrows():
        loc = str(row["building_name"]).strip()
        print(f"DEBUG: Processing location: {repr(loc)}")
        year = row["year"]
        month = row["month"]
        total_po_seats = parse_int(row.get("total_po_seats"))
        if not loc or str(loc).strip().lower() == "holding":
            continue
        if total_po_seats == 0:
            continue
        loc_df = input_df[(input_df["building_name"] == loc)]
        
        # Get all previous months for this location (before target month)
        prev_months = loc_df[
            (loc_df["year"] < year) | ((loc_df["year"] == year) & (loc_df["month"] < month))
        ].sort_values(["year", "month"], ascending=False)
        
        # Use up to 3 most recent months, but accept whatever is available
        prev_months = prev_months.head(3)
        
        # Calculate average expense from available historical data
        if not prev_months.empty:
            avg_exp = prev_months["exp_total_po_expense_amount"].apply(
                lambda x: abs(parse_float(x))
            ).mean()
        else:
            # Fallback to current month if no historical data
            avg_exp = abs(parse_float(row.get("exp_total_po_expense_amount")))
        
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
        occupancy_val = parse_pct(row.get("po_seats_occupied_pct"))
        location_data = LocationData(
            name=loc,
            exp_total_po_expense_amount=parse_float(
                row.get("exp_total_po_expense_amount"), absolute=True
            ),
            avg_exp_total_po_expense_amount=avg_exp,
            po_seats_actual_occupied_pct=parse_float(
                row.get("po_seats_actual_occupied_pct")
            ),
            po_seats_occupied_pct=occupancy_val,
            total_po_seats=total_po_seats,
        )
        target_breakeven_occupancy = rules_dict.get("target_breakeven_occupancy", 0.7)
        try:
            breakeven_price = calculate_breakeven_price_per_pax(
                location_data, target_breakeven_occupancy
            )
            base_price = apply_dynamic_pricing(
                breakeven_price, occupancy_val, rules.dynamic_pricing_tiers
            )
            final_price = apply_margin_of_safety(base_price, rules.margin_of_safety)
            clamped_price = enforce_min_max_price(
                final_price, rules.min_price, rules.max_price
            )
            losing_money = occupancy_val < target_breakeven_occupancy
            manual_override = None
            llm_reasoning = None
            output = PricingCLIOutput(
                building_name=loc,
                occupancy_pct=occupancy_val,
                breakeven_occupancy_pct=target_breakeven_occupancy,
                recommended_price=clamped_price,
                losing_money=losing_money,
                manual_override=manual_override,
                llm_reasoning=llm_reasoning,
            )
            outputs.append(output)
        except Exception as e:
            print(f"{loc}: Error calculating price: {e}")
    return outputs

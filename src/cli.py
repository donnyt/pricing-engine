"""
HOWTO: Using the CLI for Zoho Analytics Data Storage

1. Fetch and save Zoho Analytics data to SQLite:
   python3 src/cli.py fetch-and-save --report pnl_sms_by_month --year 2025 --month 5

2. Load data from SQLite and preview it:
   python3 src/cli.py load --report pnl_sms_by_month

Reports supported: pnl_sms_by_month (add more as needed)
"""

import argparse
from src.zoho_integration import fetch_pnl_sms_by_month_dataclasses
from src.sqlite_storage import save_to_sqlite, load_from_sqlite
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
    ManualOverrideInfo,
)
import pandas as pd


def fetch_and_save(report: str, year: int = None, month: int = None):
    if report == "pnl_sms_by_month":
        if year is None or month is None:
            print("--year and --month are required for pnl_sms_by_month")
            return
        rows = fetch_pnl_sms_by_month_dataclasses(year, month)
        save_to_sqlite("pnl_sms_by_month", rows)
        print(f"Saved {len(rows)} rows to SQLite table 'pnl_sms_by_month'.")
    else:
        print(f"Report '{report}' not supported yet.")


def load_and_preview(report: str):
    if report == "pnl_sms_by_month":
        df = load_from_sqlite("pnl_sms_by_month")
        print(df)  # Show all rows
        print(f"Total rows: {len(df)}")
    else:
        print(f"Report '{report}' not supported yet.")


def format_cli_output(output: PricingCLIOutput, verbose: bool = False) -> str:
    lines = [f"{output.building_name}:"]
    lines.append(f"  Occupancy: {int(round(output.occupancy_pct * 100))}%")
    lines.append(
        f"  Breakeven Occupancy: {int(round(output.breakeven_occupancy_pct * 100))}%"
    )
    lines.append(f"  Recommended Price: {output.recommended_price:,.2f}")
    if output.losing_money:
        lines.append(f"  ⚠️ Losing money at current occupancy!")
    if output.manual_override:
        mo = output.manual_override
        lines.append(
            f"  Manual Override: {mo.overridden_price:,.2f} by {mo.overridden_by} on {mo.overridden_at} ({mo.reason})"
        )
        lines.append(f"  Original Calculated Price: {mo.original_price:,.2f}")
    if verbose and output.llm_reasoning:
        lines.append(f"  Reasoning: {output.llm_reasoning}")
    return "\n".join(lines)


def run_pipeline(verbose=False):
    config = load_pricing_rules()
    try:
        df = load_from_sqlite("pnl_sms_by_month")
        print(f"Loaded {len(df)} rows from SQLite table 'pnl_sms_by_month'.")
        if "building_name" in df.columns:
            df = df.sort_values(by="building_name")
    except Exception as e:
        print(f"Error loading data from SQLite: {e}")
        df = pd.DataFrame()
    for idx, row in df.iterrows():
        loc = row.get("building_name")
        if not loc:
            continue
        if loc.strip().lower() == "holding":
            continue
        try:
            total_po_seats = int(str(row["total_po_seats"]).replace(",", ""))
        except Exception:
            total_po_seats = 0
        if total_po_seats == 0:
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

        def parse_pct(val):
            try:
                if isinstance(val, str) and "%" in val:
                    return float(val.replace("%", "").strip()) / 100
                return float(val)
            except Exception:
                return 0.0

        occupancy_val = parse_pct(row.get("po_seats_occupied_pct"))
        location_data = LocationData(
            name=loc,
            exp_total_po_expense_amount=parse_float(
                row["exp_total_po_expense_amount"], absolute=True
            ),
            po_seats_actual_occupied_pct=parse_float(
                row["po_seats_actual_occupied_pct"]
            ),
            po_seats_occupied_pct=occupancy_val,
            total_po_seats=total_po_seats,
        )
        target_breakeven_occupancy = rules_dict.get("target_breakeven_occupancy")
        if target_breakeven_occupancy is None:
            target_breakeven_occupancy = 0.7
        try:
            breakeven_price = calculate_breakeven_price_per_pax(
                location_data, target_breakeven_occupancy
            )
            base_price = apply_dynamic_pricing(
                breakeven_price,
                occupancy_val,
                rules.dynamic_pricing_tiers,
            )
            final_price = apply_margin_of_safety(base_price, rules.margin_of_safety)
            clamped_price = enforce_min_max_price(
                final_price, rules.min_price, rules.max_price
            )
            losing_money = occupancy_val < target_breakeven_occupancy
            # Placeholder for manual override and LLM reasoning
            manual_override = None  # TODO: integrate with audit/override system
            llm_reasoning = None  # TODO: integrate with LLM reasoning module
            output = PricingCLIOutput(
                building_name=loc,
                occupancy_pct=occupancy_val,
                breakeven_occupancy_pct=target_breakeven_occupancy,
                recommended_price=clamped_price,
                losing_money=losing_money,
                manual_override=manual_override,
                llm_reasoning=llm_reasoning,
            )
            print(format_cli_output(output, verbose=verbose))
        except Exception as e:
            print(f"{loc}: Error calculating price: {e}")


def main():
    parser = argparse.ArgumentParser(description="Zoho Analytics Data CLI")
    subparsers = parser.add_subparsers(dest="command")

    fetch_parser = subparsers.add_parser(
        "fetch-and-save", help="Fetch Zoho data and save to SQLite"
    )
    fetch_parser.add_argument(
        "--report", required=True, help="Report name (e.g., pnl_sms_by_month)"
    )
    fetch_parser.add_argument(
        "--year", type=int, help="Year (required for some reports)"
    )
    fetch_parser.add_argument(
        "--month", type=int, help="Month (required for some reports)"
    )

    load_parser = subparsers.add_parser(
        "load", help="Load data from SQLite and preview"
    )
    load_parser.add_argument(
        "--report", required=True, help="Report name (e.g., pnl_sms_by_month)"
    )

    pipeline_parser = subparsers.add_parser(
        "run-pipeline",
        help="Run the full pricing pipeline and print results for all locations",
    )
    pipeline_parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output for each location"
    )

    args = parser.parse_args()
    if args.command == "fetch-and-save":
        fetch_and_save(args.report, args.year, args.month)
    elif args.command == "load":
        load_and_preview(args.report)
    elif args.command == "run-pipeline":
        run_pipeline(verbose=args.verbose)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""
Pricing Engine CLI

This module handles pricing calculations, pipeline execution, and pricing-related operations.

Usage:
1. Run pricing pipeline for all locations:
   python3 src/pricing_cli.py run-pipeline

2. Run pricing pipeline for a specific location:
   python3 src/pricing_cli.py run-pipeline --location "Pacific Place"

3. Run pricing pipeline with specific month/year:
   python3 src/pricing_cli.py run-pipeline --year 2024 --month 7

4. Run pricing pipeline with verbose output (includes LLM reasoning):
   python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --verbose

5. Check pricing for all locations with verbose output:
   python3 src/pricing_cli.py check-pricing --year 2024 --month 7
"""

import argparse
import pandas as pd
import datetime

try:
    from src.data.storage import load_from_sqlite
    from src.config.rules import load_pricing_rules
    from src.pricing.models import PricingCLIOutput
    from src.pricing.service import get_pricing_service
    from src.utils.parsing import format_price_int
except ImportError:
    # Fallback for when running the script directly
    from data.storage import load_from_sqlite
    from config.rules import load_pricing_rules
    from pricing.models import PricingCLIOutput
    from pricing.service import get_pricing_service
    from utils.parsing import format_price_int


def format_cli_output(output: PricingCLIOutput, verbose: bool = False) -> str:
    """Format pricing output for CLI display."""

    def round_to_nearest(val, nearest):
        if val is None:
            return "Not set"
        import math

        return f"{int(round(val / nearest) * nearest):,}"

    lines = [f"{output.building_name}:"]
    lines.append(f"  Latest Occupancy: {output.occupancy_pct:.1f}%")
    if output.actual_breakeven_occupancy_pct is not None:
        lines.append(
            f"  Actual Breakeven Occupancy: {output.actual_breakeven_occupancy_pct:.1f}%"
        )
    else:
        lines.append(f"  Actual Breakeven Occupancy: Not available")
    if output.sold_price_per_po_seat_actual is not None:
        lines.append(
            f"  Sold Price/Seat (Actual): {round_to_nearest(output.sold_price_per_po_seat_actual, 10000)}"
        )
    lines.append("")  # Empty line for separation
    # Add smart target indicator
    target_indicator = (
        " (Smart Target)" if output.is_smart_target else " (Static Target)"
    )
    lines.append(
        f"  Target Breakeven Occupancy: {output.target_breakeven_occupancy_pct:.1f}%{target_indicator}"
    )
    if verbose and output.dynamic_multiplier is not None:
        lines.append(f"  Dynamic Multiplier: {output.dynamic_multiplier:.2f}x")
    if output.published_price is not None:
        lines.append(
            f"  Published Price: {format_price_int(output.published_price)} (Valid from Jul 2025)"
        )
    else:
        lines.append(f"  Published Price: Not set")
    lines.append(f"  Recommended Price: {format_price_int(output.recommended_price)}")
    if output.breakeven_price is not None:
        lines.append(
            f"  Bottom Price: {round_to_nearest(output.breakeven_price, 50000)}"
        )
    if output.losing_money:
        lines.append("  ⚠️ ALERT: This location is losing money at current occupancy!")
    lines.append("")  # Empty line for separation
    if (
        verbose
        and output.llm_reasoning
        and not output.llm_reasoning.startswith("[LLM reasoning unavailable")
    ):
        lines.append(f"  Reasoning: {output.llm_reasoning}")
    return "\n".join(lines)


def run_pipeline(
    verbose=False,
    year=None,
    month=None,
    location=None,
    no_auto_fetch=False,
    target_date=None,
):
    """Run the pricing pipeline for specified parameters."""
    now = datetime.datetime.now()
    target_year = int(year) if year is not None else now.year
    target_month = int(month) if month is not None else now.month

    # Get the pricing service instance
    pricing_service = get_pricing_service()

    # Run the integrated pricing pipeline
    outputs = pricing_service.run_pricing_pipeline(
        input_df=None,  # Let pipeline load merged data
        config=None,  # Service will load config internally
        target_year=target_year,
        target_month=target_month,
        target_date=target_date,  # Pass specific target date if provided
        verbose=verbose,
        auto_fetch=not no_auto_fetch,
        target_location=location,  # Pass location for targeted data loading
    )

    if not outputs:
        location_msg = f" for location '{location}'" if location else ""
        print(
            f"\n❌ No pricing results found{location_msg} for {target_year}-{target_month:02d}."
        )
        print("This usually means:")
        print("  1. No data is available in the database")
        print("  2. No data exists for the specified location")
        print("  3. No data exists for the specified month/year")
        print("\nTo load data, try:")
        print(
            "  python3 src/cli.py zoho upsert --report pnl_sms_by_month --year 2025 --month 1"
        )
        print(
            "  python3 src/cli.py zoho upsert --report private_office_occupancies_by_building --date 2025-01-15"
        )
        return

    print(f"\n📊 Pricing Results for {target_year}-{target_month:02d}:")
    for output in outputs:
        print(format_cli_output(output, verbose=verbose))


def check_pricing(year=None, month=None):
    """Check pricing for all locations with verbose output."""
    try:
        df = load_from_sqlite("pnl_sms_by_month")
        print(f"Loaded {len(df)} rows from SQLite table 'pnl_sms_by_month'.")
    except Exception as e:
        print(f"Error loading data from SQLite: {e}")
        df = pd.DataFrame()

    now = datetime.datetime.now()
    target_year = int(year) if year is not None else now.year
    target_month = int(month) if month is not None else now.month

    # Get the pricing service instance
    pricing_service = get_pricing_service()
    outputs = pricing_service.run_pricing_pipeline(
        df,
        config=None,
        target_year=target_year,
        target_month=target_month,
        verbose=True,
    )

    if not outputs:
        print(f"\n❌ No pricing results found for {target_year}-{target_month:02d}.")
        print("This usually means:")
        print("  1. No data is available in the database")
        print("  2. No data exists for the specified month/year")
        print("\nTo load data, try:")
        print(
            "  python3 src/cli.py zoho upsert --report pnl_sms_by_month --year 2025 --month 1"
        )
        print(
            "  python3 src/cli.py zoho upsert --report private_office_occupancies_by_building --date 2025-01-15"
        )
    else:
        print(f"\n📊 Pricing Results for {target_year}-{target_month:02d}:")
        for output in outputs:
            print(format_cli_output(output, verbose=True))


def main():
    """Main CLI entry point for pricing operations."""
    parser = argparse.ArgumentParser(description="Pricing Engine CLI")
    subparsers = parser.add_subparsers(dest="command")

    pipeline_parser = subparsers.add_parser(
        "run-pipeline",
        help="Run the full pricing pipeline and print results for all locations or a single location",
    )
    pipeline_parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output for each location"
    )
    pipeline_parser.add_argument(
        "--year", type=int, help="Target year for pricing (default: current year)"
    )
    pipeline_parser.add_argument(
        "--month", type=int, help="Target month for pricing (default: current month)"
    )
    pipeline_parser.add_argument(
        "--location",
        type=str,
        help="Run for a single location (default: all locations)",
    )
    pipeline_parser.add_argument(
        "--no-auto-fetch",
        action="store_true",
        help="Disable automatic fetching of daily occupancy data from Zoho Analytics",
    )
    pipeline_parser.add_argument(
        "--target-date",
        type=str,
        help="Specific target date for daily occupancy data (YYYY-MM-DD format, overrides year/month)",
    )

    check_parser = subparsers.add_parser(
        "check-pricing",
        help="Check pricing for all locations for a given year and month (with verbose output)",
    )
    check_parser.add_argument("--year", type=int, help="Year")
    check_parser.add_argument("--month", type=int, help="Month")

    args = parser.parse_args()
    if args.command == "run-pipeline":
        run_pipeline(
            verbose=args.verbose,
            year=args.year,
            month=args.month,
            location=args.location,
            no_auto_fetch=args.no_auto_fetch,
            target_date=args.target_date,
        )
    elif args.command == "check-pricing":
        check_pricing(year=args.year, month=args.month)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

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
from src.sqlite_storage import load_from_sqlite
from src.po_pricing_engine import (
    load_pricing_rules,
    PricingCLIOutput,
)
from src.pricing_pipeline import run_pricing_pipeline
from src.utils.parsing import format_price_int


def format_cli_output(output: PricingCLIOutput, verbose: bool = False) -> str:
    """Format pricing output for CLI display."""
    lines = [f"{output.building_name}:"]
    lines.append(f"  Latest Occupancy: {output.occupancy_pct:.1f}%")
    lines.append(f"  Breakeven Occupancy: {output.breakeven_occupancy_pct:.1f}%")
    if verbose and output.dynamic_multiplier is not None:
        lines.append(f"  Dynamic Multiplier: {output.dynamic_multiplier:.2f}x")
    if hasattr(output, "published_price") and output.published_price is not None:
        lines.append(f"  Published Price: {format_price_int(output.published_price)}")
    lines.append(f"  Recommended Price: {format_price_int(output.recommended_price)}")
    if output.losing_money:
        lines.append("  ⚠️ ALERT: This location is losing money at current occupancy!")
    if (
        verbose
        and output.llm_reasoning
        and not output.llm_reasoning.startswith("[LLM reasoning unavailable")
    ):
        lines.append(f"  Reasoning: {output.llm_reasoning}")
    return "\n".join(lines)


def run_pipeline(verbose=False, year=None, month=None, location=None):
    """Run the pricing pipeline for specified parameters."""
    try:
        df = load_from_sqlite("pnl_sms_by_month")
    except Exception as e:
        print(f"Error loading data from SQLite: {e}")
        df = pd.DataFrame()

    now = datetime.datetime.now()
    target_year = int(year) if year is not None else now.year
    target_month = int(month) if month is not None else now.month

    if not df.empty:
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)

    config = load_pricing_rules()

    if location:
        # Normalize location for matching
        normalized_location = location.strip().lower()
        df = df[
            df["building_name"].astype(str).str.strip().str.lower()
            == normalized_location
        ]

    outputs = run_pricing_pipeline(
        df, config, target_year=target_year, target_month=target_month, verbose=verbose
    )

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

    config = load_pricing_rules()
    outputs = run_pricing_pipeline(
        df, config, target_year=target_year, target_month=target_month, verbose=True
    )

    if not outputs:
        print(f"No pricing results found for {target_year}-{target_month:02d}.")
    else:
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
        )
    elif args.command == "check-pricing":
        check_pricing(year=args.year, month=args.month)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

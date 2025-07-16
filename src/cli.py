"""
HOWTO: Using the CLI for Zoho Analytics Data Storage

1. Fetch and save Zoho Analytics data to SQLite:
   python3 src/cli.py fetch-and-save --report pnl_sms_by_month --year 2025 --month 5

2. Load data from SQLite and preview it:
   python3 src/cli.py load --report pnl_sms_by_month

3. Clear and reload data for a specific month:
   python3 src/cli.py clear-and-reload --report pnl_sms_by_month --year 2025 --month 5

4. Clear and reload data for a range of months:
   python3 src/cli.py clear-and-reload-range --report pnl_sms_by_month --start-year 2025 --start-month 1 --end-year 2025 --end-month 5

Reports supported: pnl_sms_by_month (add more as needed)
"""

import argparse
import pandas as pd
import datetime
from zoho_integration import (
    fetch_pnl_sms_by_month_dataclasses,
    clear_and_reload_pnl_sms_by_month,
    clear_and_reload_pnl_sms_by_month_range,
)
from sqlite_storage import save_to_sqlite, load_from_sqlite
from po_pricing_engine import (
    load_pricing_rules,
    PricingCLIOutput,
)
from pricing_pipeline import run_pricing_pipeline
from utils.parsing import format_price_int


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
        print(df)
        print(f"Total rows: {len(df)}")
    else:
        print(f"Report '{report}' not supported yet.")


def clear_and_reload(report: str, year: int = None, month: int = None):
    if report == "pnl_sms_by_month":
        if year is None or month is None:
            print("--year and --month are required for pnl_sms_by_month")
            return
        n = clear_and_reload_pnl_sms_by_month(year, month)
        print(
            f"Cleared and reloaded {n} rows for {year}-{month:02d} in 'pnl_sms_by_month'."
        )
    else:
        print(f"Report '{report}' not supported yet.")


def clear_and_reload_range(
    report: str, start_year: int, start_month: int, end_year: int, end_month: int
):
    if report == "pnl_sms_by_month":
        n = clear_and_reload_pnl_sms_by_month_range(
            start_year, start_month, end_year, end_month
        )
        print(
            f"Cleared and reloaded {n} rows for {start_year}-{start_month:02d} to {end_year}-{end_month:02d} in 'pnl_sms_by_month'."
        )
    else:
        print(f"Report '{report}' not supported yet.")


def format_cli_output(output: PricingCLIOutput, verbose: bool = False) -> str:
    lines = [f"{output.building_name}:"]
    lines.append(f"  Occupancy: {int(round(output.occupancy_pct * 100))}%")
    lines.append(
        f"  Breakeven Occupancy: {int(round(output.breakeven_occupancy_pct * 100))}%"
    )
    lines.append(f"  Recommended Price: {format_price_int(output.recommended_price)}")
    if output.losing_money:
        lines.append("  ⚠️ Losing money at current occupancy!")
    if output.manual_override:
        mo = output.manual_override
        lines.append(
            f"  Manual Override: {mo.overridden_price:,.2f} by {mo.overridden_by} on {mo.overridden_at} ({mo.reason})"
        )
        lines.append(f"  Original Calculated Price: {mo.original_price:,.2f}")
    if verbose and output.llm_reasoning:
        lines.append(f"  Reasoning: {output.llm_reasoning}")
    return "\n".join(lines)


def run_pipeline(verbose=False, year=None, month=None):
    try:
        df = load_from_sqlite("pnl_sms_by_month")
        print(f"Loaded {len(df)} rows from SQLite table 'pnl_sms_by_month'.")
    except Exception as e:
        print(f"Error loading data from SQLite: {e}")
        df = pd.DataFrame()
    # Determine target year/month
    now = datetime.datetime.now()
    target_year = int(year) if year is not None else now.year
    target_month = int(month) if month is not None else now.month
    # Ensure year and month columns are int for filtering
    if not df.empty:
        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
    print(f"Processing for target period: {target_year}-{target_month:02d}")
    config = load_pricing_rules()
    outputs = run_pricing_pipeline(
        df, config, target_year=target_year, target_month=target_month, verbose=verbose
    )
    for output in outputs:
        print(format_cli_output(output, verbose=verbose))


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
    pipeline_parser.add_argument(
        "--year", type=int, help="Target year for pricing (default: current year)"
    )
    pipeline_parser.add_argument(
        "--month", type=int, help="Target month for pricing (default: current month)"
    )

    clear_parser = subparsers.add_parser(
        "clear-and-reload", help="Clear and reload data for a specific month"
    )
    clear_parser.add_argument(
        "--report", required=True, help="Report name (e.g., pnl_sms_by_month)"
    )
    clear_parser.add_argument(
        "--year", type=int, help="Year (required for some reports)"
    )
    clear_parser.add_argument(
        "--month", type=int, help="Month (required for some reports)"
    )

    clear_range_parser = subparsers.add_parser(
        "clear-and-reload-range", help="Clear and reload data for a range of months"
    )
    clear_range_parser.add_argument(
        "--report", required=True, help="Report name (e.g., pnl_sms_by_month)"
    )
    clear_range_parser.add_argument(
        "--start-year", type=int, required=True, help="Start year"
    )
    clear_range_parser.add_argument(
        "--start-month", type=int, required=True, help="Start month"
    )
    clear_range_parser.add_argument(
        "--end-year", type=int, required=True, help="End year"
    )
    clear_range_parser.add_argument(
        "--end-month", type=int, required=True, help="End month"
    )

    args = parser.parse_args()
    if args.command == "fetch-and-save":
        fetch_and_save(args.report, args.year, args.month)
    elif args.command == "load":
        load_and_preview(args.report)
    elif args.command == "run-pipeline":
        run_pipeline(verbose=args.verbose, year=args.year, month=args.month)
    elif args.command == "clear-and-reload":
        clear_and_reload(args.report, args.year, args.month)
    elif args.command == "clear-and-reload-range":
        clear_and_reload_range(
            args.report,
            args.start_year,
            args.start_month,
            args.end_year,
            args.end_month,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

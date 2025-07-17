"""
Zoho Analytics Data Management CLI

This module handles Zoho Analytics data fetching, storage, and management operations.

Usage:
1. Upsert Zoho Analytics data to SQLite (insert if not exists, delete and reinsert if exists):
   python3 src/zoho_cli.py upsert --report pnl_sms_by_month --year 2025 --month 5

2. Upsert data for a range of months:
   python3 src/zoho_cli.py upsert-range --report pnl_sms_by_month --start-year 2025 --start-month 1 --end-year 2025 --end-month 5

3. Load data from SQLite and preview it:
   python3 src/zoho_cli.py load --report pnl_sms_by_month

4. Legacy commands (still supported):
   python3 src/zoho_cli.py fetch-and-save --report pnl_sms_by_month --year 2025 --month 5
   python3 src/zoho_cli.py clear-and-reload --report pnl_sms_by_month --year 2025 --month 5
   python3 src/zoho_cli.py clear-and-reload-range --report pnl_sms_by_month --start-year 2025 --start-month 1 --end-year 2025 --end-month 5

Reports supported: pnl_sms_by_month (add more as needed)
"""

import argparse
from src.zoho_integration import (
    fetch_pnl_sms_by_month_dataclasses,
    clear_and_reload_pnl_sms_by_month,
    clear_and_reload_pnl_sms_by_month_range,
    upsert_pnl_sms_by_month,
    upsert_pnl_sms_by_month_range,
)
from src.sqlite_storage import save_to_sqlite, load_from_sqlite


def upsert_data(report: str, year: int = None, month: int = None):
    """Upsert data from Zoho Analytics to SQLite (insert if not exists, delete and reinsert if exists)."""
    if report == "pnl_sms_by_month":
        if year is None or month is None:
            print("--year and --month are required for pnl_sms_by_month")
            return
        n = upsert_pnl_sms_by_month(year, month)
        print(f"Upserted {n} rows for {year}-{month:02d} in 'pnl_sms_by_month'.")
    else:
        print(f"Report '{report}' not supported yet.")


def upsert_data_range(
    report: str, start_year: int, start_month: int, end_year: int, end_month: int
):
    """Upsert data for a range of months from Zoho Analytics to SQLite."""
    if report == "pnl_sms_by_month":
        n = upsert_pnl_sms_by_month_range(start_year, start_month, end_year, end_month)
        print(
            f"Upserted {n} rows for {start_year}-{start_month:02d} to {end_year}-{end_month:02d} in 'pnl_sms_by_month'."
        )
    else:
        print(f"Report '{report}' not supported yet.")


def fetch_and_save(report: str, year: int = None, month: int = None):
    """Fetch data from Zoho Analytics and save to SQLite."""
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
    """Load data from SQLite and display preview."""
    if report == "pnl_sms_by_month":
        df = load_from_sqlite("pnl_sms_by_month")
        print(df)
        print(f"Total rows: {len(df)}")
    else:
        print(f"Report '{report}' not supported yet.")


def clear_and_reload(report: str, year: int = None, month: int = None):
    """Clear existing data for a specific month and reload from Zoho."""
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
    """Clear existing data for a range of months and reload from Zoho."""
    if report == "pnl_sms_by_month":
        n = clear_and_reload_pnl_sms_by_month_range(
            start_year, start_month, end_year, end_month
        )
        print(
            f"Cleared and reloaded {n} rows for {start_year}-{start_month:02d} to {end_year}-{end_month:02d} in 'pnl_sms_by_month'."
        )
    else:
        print(f"Report '{report}' not supported yet.")


def main():
    """Main CLI entry point for Zoho Analytics operations."""
    parser = argparse.ArgumentParser(description="Zoho Analytics Data Management CLI")
    subparsers = parser.add_subparsers(dest="command")

    # New upsert commands (recommended)
    upsert_parser = subparsers.add_parser(
        "upsert",
        help="Upsert Zoho data to SQLite (insert if not exists, delete and reinsert if exists)",
    )
    upsert_parser.add_argument(
        "--report", required=True, help="Report name (e.g., pnl_sms_by_month)"
    )
    upsert_parser.add_argument(
        "--year", type=int, help="Year (required for some reports)"
    )
    upsert_parser.add_argument(
        "--month", type=int, help="Month (required for some reports)"
    )

    upsert_range_parser = subparsers.add_parser(
        "upsert-range", help="Upsert Zoho data for a range of months"
    )
    upsert_range_parser.add_argument(
        "--report", required=True, help="Report name (e.g., pnl_sms_by_month)"
    )
    upsert_range_parser.add_argument(
        "--start-year", type=int, required=True, help="Start year"
    )
    upsert_range_parser.add_argument(
        "--start-month", type=int, required=True, help="Start month"
    )
    upsert_range_parser.add_argument(
        "--end-year", type=int, required=True, help="End year"
    )
    upsert_range_parser.add_argument(
        "--end-month", type=int, required=True, help="End month"
    )

    # Legacy commands (still supported)
    fetch_parser = subparsers.add_parser(
        "fetch-and-save", help="Fetch Zoho data and save to SQLite (legacy)"
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

    clear_parser = subparsers.add_parser(
        "clear-and-reload", help="Clear and reload data for a specific month (legacy)"
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
        "clear-and-reload-range",
        help="Clear and reload data for a range of months (legacy)",
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
    if args.command == "upsert":
        upsert_data(args.report, args.year, args.month)
    elif args.command == "upsert-range":
        upsert_data_range(
            args.report,
            args.start_year,
            args.start_month,
            args.end_year,
            args.end_month,
        )
    elif args.command == "fetch-and-save":
        fetch_and_save(args.report, args.year, args.month)
    elif args.command == "load":
        load_and_preview(args.report)
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

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

try:
    from src.zoho_integration import (
        fetch_pnl_sms_by_month_dataclasses,
        clear_and_reload_pnl_sms_by_month,
        clear_and_reload_pnl_sms_by_month_range,
        upsert_pnl_sms_by_month,
        upsert_pnl_sms_by_month_range,
        fetch_private_office_occupancies_by_building_dataclasses,
        upsert_private_office_occupancies_by_building,
        upsert_private_office_occupancies_by_building_range,
    )
    from src.sqlite_storage import save_to_sqlite, load_from_sqlite
except ImportError:
    # Fallback for when running the script directly
    from zoho_integration import (
        fetch_pnl_sms_by_month_dataclasses,
        clear_and_reload_pnl_sms_by_month,
        clear_and_reload_pnl_sms_by_month_range,
        upsert_pnl_sms_by_month,
        upsert_pnl_sms_by_month_range,
        fetch_private_office_occupancies_by_building_dataclasses,
        upsert_private_office_occupancies_by_building,
        upsert_private_office_occupancies_by_building_range,
    )
    from sqlite_storage import save_to_sqlite, load_from_sqlite


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
    elif report == "private_office_occupancies_by_building":
        # For daily occupancy data, we need a date parameter instead of year/month
        # This will be handled by a separate CLI command with --date parameter
        print(
            "Use 'fetch-daily-occupancy' command for private_office_occupancies_by_building"
        )
        return
    else:
        print(f"Report '{report}' not supported yet.")


def load_and_preview(report: str):
    """Load data from SQLite and display preview."""
    if report == "pnl_sms_by_month":
        df = load_from_sqlite("pnl_sms_by_month")
        print(df)
        print(f"Total rows: {len(df)}")
    elif report == "private_office_occupancies_by_building":
        df = load_from_sqlite("private_office_occupancies_by_building")
        print(df)
        print(f"Total rows: {len(df)}")
    else:
        print(f"Report '{report}' not supported yet.")


def fetch_daily_occupancy(date: str):
    """Fetch daily occupancy data from Zoho Analytics and save to SQLite."""
    print(f"Fetching daily occupancy data for date: {date}")
    try:
        rows = fetch_private_office_occupancies_by_building_dataclasses(date)
        save_to_sqlite("private_office_occupancies_by_building", rows)
        print(
            f"Saved {len(rows)} rows to SQLite table 'private_office_occupancies_by_building' for date {date}."
        )
        if rows:
            print("First row structure:")
            print(rows[0])
            print("\nAll field names:")
            from dataclasses import fields

            print([field.name for field in fields(rows[0])])
    except Exception as e:
        print(f"Error fetching data: {e}")
        print("This is expected if Zoho credentials are not configured.")


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


def upsert_daily_occupancy(date: str):
    """Upsert daily occupancy data from Zoho Analytics to SQLite."""
    print(f"Upserting daily occupancy data for date: {date}")
    try:
        n = upsert_private_office_occupancies_by_building(date)
        print(
            f"Upserted {n} rows for date {date} in 'private_office_occupancies_by_building'."
        )
    except Exception as e:
        print(f"Error upserting data: {e}")
        print("This is expected if Zoho credentials are not configured.")


def upsert_daily_occupancy_range(start_date: str, end_date: str):
    """Upsert daily occupancy data for a range of dates from Zoho Analytics to SQLite."""
    print(f"Upserting daily occupancy data for range: {start_date} to {end_date}")
    try:
        n = upsert_private_office_occupancies_by_building_range(start_date, end_date)
        print(
            f"Upserted {n} rows for range {start_date} to {end_date} in 'private_office_occupancies_by_building'."
        )
    except Exception as e:
        print(f"Error upserting data: {e}")
        print("This is expected if Zoho credentials are not configured.")


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

    # New command for daily occupancy data
    fetch_daily_occupancy_parser = subparsers.add_parser(
        "fetch-daily-occupancy", help="Fetch daily occupancy data from Zoho Analytics"
    )
    fetch_daily_occupancy_parser.add_argument(
        "--date",
        help="Date in YYYY-MM-DD format (e.g., 2025-01-15). Defaults to today's date.",
    )

    # New commands for upserting daily occupancy data
    upsert_daily_occupancy_parser = subparsers.add_parser(
        "upsert-daily-occupancy", help="Upsert daily occupancy data from Zoho Analytics"
    )
    upsert_daily_occupancy_parser.add_argument(
        "--date",
        help="Date in YYYY-MM-DD format (e.g., 2025-01-15). Defaults to today's date.",
    )

    upsert_daily_occupancy_range_parser = subparsers.add_parser(
        "upsert-daily-occupancy-range",
        help="Upsert daily occupancy data for a range of dates",
    )
    upsert_daily_occupancy_range_parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format (e.g., 2025-01-01)",
    )
    upsert_daily_occupancy_range_parser.add_argument(
        "--end-date",
        required=True,
        help="End date in YYYY-MM-DD format (e.g., 2025-01-31)",
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
    elif args.command == "fetch-daily-occupancy":
        from datetime import date

        target_date = args.date or date.today().strftime("%Y-%m-%d")
        fetch_daily_occupancy(target_date)
    elif args.command == "upsert-daily-occupancy":
        from datetime import date

        target_date = args.date or date.today().strftime("%Y-%m-%d")
        upsert_daily_occupancy(target_date)
    elif args.command == "upsert-daily-occupancy-range":
        from datetime import date

        start_date = args.start_date or date.today().strftime("%Y-%m-%d")
        end_date = args.end_date or date.today().strftime("%Y-%m-%d")
        upsert_daily_occupancy_range(start_date, end_date)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

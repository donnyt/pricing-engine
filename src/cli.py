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

    args = parser.parse_args()
    if args.command == "fetch-and-save":
        fetch_and_save(args.report, args.year, args.month)
    elif args.command == "load":
        load_and_preview(args.report)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

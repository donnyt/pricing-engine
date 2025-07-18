#!/usr/bin/env python3
"""
Database Initialization Script

This script creates the SQLite database with proper schema and data types
from the start, ensuring all tables have the correct column types.
"""

import sqlite3
import os
from typing import Dict, List, Tuple


def get_table_schemas() -> Dict[str, List[Tuple[str, str]]]:
    """
    Define the proper schema for each table with correct data types.

    Returns:
        Dictionary mapping table names to list of (column_name, data_type) tuples
    """
    return {
        "pnl_sms_by_month": [
            ("entry_date", "TEXT"),
            ("year", "INTEGER"),
            ("month", "INTEGER"),
            ("building_name", "TEXT"),
            ("rev_total_revenue_amount", "REAL"),
            ("exp_total_rent_service_utilities_internet_expense_amount", "REAL"),
            ("exp_total_cogs_and_opex_amount", "REAL"),
            ("exp_total_expense_amount", "REAL"),
            ("ebitda", "REAL"),
            ("ebitda_pct", "REAL"),
            ("net_profit", "REAL"),
            ("revenue_psm", "REAL"),
            ("expense_psm", "REAL"),
            ("rev_total_po_revenue_amount", "REAL"),
            ("exp_total_po_expense_amount", "REAL"),
            ("po_margin", "REAL"),
            ("po_margin_pct", "REAL"),
            ("forecast_total_po_revenue_amount", "REAL"),
            ("forecast_total_po_revenue_deviation_amount", "REAL"),
            ("forecast_po_deviation_pct", "REAL"),
            ("sold_price_per_po_seat_actual", "REAL"),
            ("rev_total_meeting_room_revenue_amount", "REAL"),
            ("rev_total_events_revenue_amount", "REAL"),
            ("rev_total_vo_revenue_amount", "REAL"),
            ("rev_total_coworking_revenue_amount", "REAL"),
            ("rev_total_printing_snacks_top_up_amount", "REAL"),
            ("rev_total_other_services_revenue_amount", "REAL"),
            ("rev_total_partnerships_revenue_amount", "REAL"),
            ("rev_total_other_income_amount", "REAL"),
            ("exp_rent_expenses_amount", "REAL"),
            ("exp_service_charges_amount", "REAL"),
            ("exp_utilities_expenses_amount", "REAL"),
            ("exp_internet_expenses_amount", "REAL"),
            ("exp_total_cost_of_services_expense_amount", "REAL"),
            ("exp_outsourcing_expenses_amount", "REAL"),
            ("exp_total_hr_related_expense_amount", "REAL"),
            ("exp_total_office_related_expense_amount", "REAL"),
            ("exp_total_po_taxes_expense_amount", "REAL"),
            ("exp_total_taxes_expense_amount", "REAL"),
            ("exp_total_depreciation_interest_loan_expense_amount", "REAL"),
            ("exp_total_other_expense_amount", "REAL"),
            ("total_semi_gross_area", "REAL"),
            ("total_nett_area", "REAL"),
            ("total_po_seats_occupied", "INTEGER"),
            ("po_seats_occupied_pct", "REAL"),
            ("total_po_seats_occupied_actual", "INTEGER"),
            ("po_seats_actual_occupied_pct", "REAL"),
            ("po_seats_efficiency_loss_pct", "REAL"),
            ("breakeven_occupancy_pct", "REAL"),
            ("total_po_seats", "INTEGER"),
            ("po_qty", "INTEGER"),
            ("mr_qty", "INTEGER"),
            ("mr_capacity", "INTEGER"),
            ("co_qty", "INTEGER"),
            ("co_capacity", "INTEGER"),
            ("evt_qty", "INTEGER"),
            ("evt_capacity", "INTEGER"),
            ("cmn_capacity", "INTEGER"),
            ("dd_capacity", "INTEGER"),
            ("sto_qty", "INTEGER"),
            ("sto_area", "REAL"),
            ("svr_qty", "INTEGER"),
            ("svr_area", "REAL"),
        ],
        "private_office_occupancies_by_building": [
            ("date", "TEXT"),
            ("building_id", "TEXT"),
            ("building_name", "TEXT"),
            ("total_po", "INTEGER"),
            ("po_occupied", "INTEGER"),
            ("po_vacant", "INTEGER"),
            ("total_po_pax", "INTEGER"),
            ("po_seats_occupied", "INTEGER"),
            ("po_seats_occupied_actual", "INTEGER"),
            ("po_seats_vacant", "INTEGER"),
            ("po_occupied_pct", "REAL"),
            ("po_seats_occupied_pct", "REAL"),
            ("po_seats_occupied_actual_pct", "REAL"),
        ],
        "published_prices": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("building_name", "TEXT NOT NULL"),
            ("year_from", "INTEGER NOT NULL"),
            ("month_from", "INTEGER NOT NULL"),
            ("year_to", "INTEGER NOT NULL"),
            ("month_to", "INTEGER NOT NULL"),
            ("price", "INTEGER NOT NULL"),
        ],
    }


def create_table(
    conn: sqlite3.Connection, table_name: str, schema: List[Tuple[str, str]]
) -> None:
    """
    Create a table with the specified schema.

    Args:
        conn: SQLite connection
        table_name: Name of the table to create
        schema: List of (column_name, data_type) tuples
    """
    cursor = conn.cursor()

    # Check if table already exists
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    if cursor.fetchone():
        print(f"Table {table_name} already exists, skipping...")
        return

    # Create table with proper schema
    column_definitions = ", ".join([f"{col} {dtype}" for col, dtype in schema])
    create_sql = f"CREATE TABLE {table_name} ({column_definitions})"

    print(f"Creating table: {table_name}")
    cursor.execute(create_sql)

    print(f"  Created with {len(schema)} columns")
    for col_name, data_type in schema:
        print(f"    {col_name}: {data_type}")


def create_indexes(conn: sqlite3.Connection) -> None:
    """
    Create useful indexes for better query performance.

    Args:
        conn: SQLite connection
    """
    cursor = conn.cursor()

    # Indexes for pnl_sms_by_month
    indexes = [
        (
            "idx_pnl_building_year_month",
            "pnl_sms_by_month",
            "(building_name, year, month)",
        ),
        ("idx_pnl_year_month", "pnl_sms_by_month", "(year, month)"),
        ("idx_pnl_building", "pnl_sms_by_month", "(building_name)"),
        # Indexes for private_office_occupancies_by_building
        ("idx_occupancy_date", "private_office_occupancies_by_building", "(date)"),
        (
            "idx_occupancy_building",
            "private_office_occupancies_by_building",
            "(building_name)",
        ),
        (
            "idx_occupancy_building_date",
            "private_office_occupancies_by_building",
            "(building_name, date)",
        ),
        # Indexes for published_prices
        (
            "idx_prices_building_year_from",
            "published_prices",
            "(building_name, year_from, month_from)",
        ),
        ("idx_prices_year_from", "published_prices", "(year_from, month_from)"),
    ]

    for index_name, table_name, columns in indexes:
        try:
            cursor.execute(f"CREATE INDEX {index_name} ON {table_name} {columns}")
            print(f"Created index: {index_name}")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print(f"Index {index_name} already exists, skipping...")
            else:
                print(f"Error creating index {index_name}: {e}")


def init_database(db_path: str = "data/zoho_data.db") -> None:
    """
    Initialize the database with proper schema.

    Args:
        db_path: Path to the SQLite database file
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    print(f"Initializing database: {db_path}")

    # Connect to database (this will create the file if it doesn't exist)
    conn = sqlite3.connect(db_path)

    try:
        # Get table schemas
        schemas = get_table_schemas()

        # Create each table
        for table_name, table_schema in schemas.items():
            create_table(conn, table_name, table_schema)

        # Create indexes
        print("\nCreating indexes...")
        create_indexes(conn)

        # Commit changes
        conn.commit()

        print(f"\nDatabase initialization completed successfully!")
        print(f"Database file: {db_path}")

        # Show table summary
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nCreated tables: {[table[0] for table in tables]}")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def verify_schema(db_path: str = "data/zoho_data.db") -> None:
    """
    Verify that the database has the correct schema.

    Args:
        db_path: Path to the SQLite database file
    """
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    print(f"\nVerifying database schema: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        schemas = get_table_schemas()

        for table_name, expected_schema in schemas.items():
            print(f"\nTable: {table_name}")

            # Check if table exists
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if not cursor.fetchone():
                print(f"  ❌ Table does not exist")
                continue

            # Get actual schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            actual_schema = cursor.fetchall()

            # Compare schemas (ignore constraints like NOT NULL, PRIMARY KEY for now)
            expected_columns = {
                col: dtype.split()[0] for col, dtype in expected_schema
            }  # Get base type
            actual_columns = {row[1]: row[2] for row in actual_schema}

            all_match = True
            for col, expected_dtype in expected_columns.items():
                if col not in actual_columns:
                    print(f"  ❌ Missing column: {col}")
                    all_match = False
                elif actual_columns[col] != expected_dtype:
                    print(
                        f"  ❌ Wrong type for {col}: expected {expected_dtype}, got {actual_columns[col]}"
                    )
                    all_match = False

            if all_match:
                print(f"  ✅ Schema is correct ({len(expected_schema)} columns)")

    finally:
        conn.close()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize database with proper schema"
    )
    parser.add_argument(
        "--db-path", default="data/zoho_data.db", help="Database file path"
    )
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify existing schema"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force recreation of existing tables"
    )

    args = parser.parse_args()

    if args.verify_only:
        verify_schema(args.db_path)
    else:
        if args.force and os.path.exists(args.db_path):
            print(f"Removing existing database: {args.db_path}")
            os.remove(args.db_path)

        init_database(args.db_path)
        verify_schema(args.db_path)


if __name__ == "__main__":
    main()

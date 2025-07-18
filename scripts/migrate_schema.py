#!/usr/bin/env python3
"""
Schema Migration Script

This script migrates the SQLite database schema to use proper data types
instead of storing everything as TEXT. This will improve performance,
data integrity, and fix parsing issues.
"""

import sqlite3
import os
from typing import Dict, List, Tuple
from src.utils.parsing import parse_float, parse_int, parse_pct


def get_proper_schema() -> Dict[str, List[Tuple[str, str]]]:
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
    }


def convert_value(value: str, target_type: str) -> any:
    """
    Convert a string value to the target data type.

    Args:
        value: String value to convert
        target_type: Target SQLite data type

    Returns:
        Converted value
    """
    if value is None or value == "":
        return None

    try:
        if target_type == "INTEGER":
            return parse_int(value)
        elif target_type == "REAL":
            # Handle percentage values
            if "%" in str(value):
                return parse_pct(value)
            else:
                return parse_float(value)
        else:  # TEXT
            return str(value)
    except Exception as e:
        print(f"Warning: Could not convert '{value}' to {target_type}: {e}")
        return None


def migrate_table(
    conn: sqlite3.Connection, table_name: str, schema: List[Tuple[str, str]]
) -> None:
    """
    Migrate a single table to use proper data types.

    Args:
        conn: SQLite connection
        table_name: Name of the table to migrate
        schema: List of (column_name, data_type) tuples
    """
    print(f"Migrating table: {table_name}")

    # Get current data
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    if not rows:
        print(f"  No data found in {table_name}")
        return

    # Get column names from first row
    cursor.execute(f"PRAGMA table_info({table_name})")
    old_columns = [row[1] for row in cursor.fetchall()]

    # Create new table with proper schema
    new_table_name = f"{table_name}_new"
    column_definitions = ", ".join([f"{col} {dtype}" for col, dtype in schema])
    create_sql = f"CREATE TABLE {new_table_name} ({column_definitions})"

    print(f"  Creating new table: {new_table_name}")
    cursor.execute(create_sql)

    # Convert and insert data
    print(f"  Converting {len(rows)} rows...")
    converted_count = 0
    error_count = 0

    for row in rows:
        try:
            # Convert each value to proper type
            converted_row = []
            for i, (col_name, target_type) in enumerate(schema):
                if i < len(row):
                    converted_value = convert_value(row[i], target_type)
                    converted_row.append(converted_value)
                else:
                    converted_row.append(None)

            # Insert converted row
            placeholders = ", ".join(["?" for _ in converted_row])
            insert_sql = f"INSERT INTO {new_table_name} VALUES ({placeholders})"
            cursor.execute(insert_sql, converted_row)
            converted_count += 1

        except Exception as e:
            print(f"    Error converting row: {e}")
            error_count += 1

    print(f"  Converted {converted_count} rows successfully, {error_count} errors")

    # Drop old table and rename new table
    cursor.execute(f"DROP TABLE {table_name}")
    cursor.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")

    print(f"  Migration completed for {table_name}")


def main():
    """Main migration function."""
    db_path = "data/zoho_data.db"

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    print("Starting schema migration...")
    print(f"Database: {db_path}")

    # Create backup
    backup_path = f"{db_path}.backup"
    import shutil

    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Get proper schema
    schema = get_proper_schema()

    # Connect to database
    conn = sqlite3.connect(db_path)

    try:
        # Migrate each table
        for table_name, table_schema in schema.items():
            # Check if table exists
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            if cursor.fetchone():
                migrate_table(conn, table_name, table_schema)
            else:
                print(f"Table {table_name} not found, skipping...")

        conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        print("Restoring from backup...")
        conn.close()
        shutil.copy2(backup_path, db_path)
        print("Backup restored.")
        return

    finally:
        conn.close()


if __name__ == "__main__":
    main()

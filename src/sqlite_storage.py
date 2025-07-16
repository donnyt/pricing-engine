import sqlite3
import pandas as pd
from typing import List, Any


def save_to_sqlite(
    table_name: str,
    rows: List[Any],
    db_path: str = "zoho_data.db",
    if_exists: str = "replace",
):
    """
    Save a list of dataclass instances (or dicts) to a SQLite table.
    - table_name: Name of the SQLite table.
    - rows: List of dataclass instances or dicts.
    - db_path: Path to the SQLite database file.
    - if_exists: 'replace' (default) or 'append'.
    """
    if not rows:
        return
    # Convert dataclass instances to dicts if needed
    if not isinstance(rows[0], dict):
        rows = [row.__dict__ for row in rows]
    df = pd.DataFrame(rows)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)


def load_from_sqlite(table_name: str, db_path: str = "zoho_data.db") -> pd.DataFrame:
    """
    Load data from a SQLite table into a pandas DataFrame.
    """
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)


def delete_from_sqlite_by_year_month(
    table_name: str, year: int, month: int, db_path: str = "zoho_data.db"
):
    """
    Delete rows from a SQLite table for a specific year and month.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"DELETE FROM {table_name} WHERE year = ? AND month = ?", (year, month)
        )
        conn.commit()


def delete_from_sqlite_by_range(
    table_name: str,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    db_path: str = "zoho_data.db",
):
    """
    Delete rows from a SQLite table for a range of months/years (inclusive).
    """
    # Build a list of (year, month) tuples in the range
    ym = []
    y, m = start_year, start_month
    while (y < end_year) or (y == end_year and m <= end_month):
        ym.append((y, m))
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1
    with sqlite3.connect(db_path) as conn:
        for year, month in ym:
            conn.execute(
                f"DELETE FROM {table_name} WHERE year = ? AND month = ?", (year, month)
            )
        conn.commit()

import sqlite3
import pandas as pd
from typing import List, Any, Optional
from dataclasses import dataclass


def save_to_sqlite(
    table_name: str,
    rows: List[Any],
    db_path: str = "data/zoho_data.db",
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


def load_from_sqlite(
    table_name: str, db_path: str = "data/zoho_data.db"
) -> pd.DataFrame:
    """
    Load data from a SQLite table into a pandas DataFrame.
    """
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)


def delete_from_sqlite_by_year_month(
    table_name: str, year: int, month: int, db_path: str = "data/zoho_data.db"
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
    db_path: str = "data/zoho_data.db",
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


def delete_from_sqlite_by_date(
    table_name: str, date: str, db_path: str = "data/zoho_data.db"
):
    """
    Delete rows from a SQLite table for a specific date.
    Args:
        table_name: Name of the SQLite table
        date: Date in 'YYYY-MM-DD' format
        db_path: Path to the SQLite database file
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"DELETE FROM {table_name} WHERE date = ?", (date,))
        conn.commit()


def delete_from_sqlite_by_date_range(
    table_name: str,
    start_date: str,
    end_date: str,
    db_path: str = "data/zoho_data.db",
):
    """
    Delete rows from a SQLite table for a range of dates (inclusive).
    Args:
        table_name: Name of the SQLite table
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        db_path: Path to the SQLite database file
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"DELETE FROM {table_name} WHERE date >= ? AND date <= ?",
            (start_date, end_date),
        )
        conn.commit()


@dataclass
class PublishedPrice:
    building_name: str
    year_from: int
    month_from: int
    year_to: int
    month_to: int
    price: float
    reason: Optional[str] = None


def save_published_price(
    published_price: PublishedPrice,
    db_path: str = "data/zoho_data.db",
):
    """
    Save a published price record to the published_prices table.
    If a published price already exists for the same building and period (range), replace it.
    """
    with sqlite3.connect(db_path) as conn:
        # Delete any existing published price(s) for this building and period (range)
        conn.execute(
            """
            DELETE FROM published_prices
            WHERE building_name = ?
              AND year_from = ? AND month_from = ?
              AND year_to = ? AND month_to = ?
            """,
            (
                published_price.building_name,
                published_price.year_from,
                published_price.month_from,
                published_price.year_to,
                published_price.month_to,
            ),
        )
        # Insert the new published price
        conn.execute(
            """
            INSERT INTO published_prices (
                building_name, year_from, month_from, year_to, month_to, price, published_by, published_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                published_price.building_name,
                published_price.year_from,
                published_price.month_from,
                published_price.year_to,
                published_price.month_to,
                published_price.price,
                getattr(published_price, "published_by", None),
                getattr(published_price, "published_at", None),
                published_price.reason,
            ),
        )
        conn.commit()


def get_published_price(
    building_name: str,
    year: int,
    month: int,
    db_path: str = "data/zoho_data.db",
) -> Optional[float]:
    """
    Get the published price for a building and year/month from the published_prices table.
    Returns the price if found, else None.
    """
    query = """
        SELECT price FROM published_prices
        WHERE building_name = ?
          AND (year_from < ? OR (year_from = ? AND month_from <= ?))
          AND (year_to > ? OR (year_to = ? AND month_to >= ?))
        ORDER BY year_from DESC, month_from DESC
        LIMIT 1
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            query,
            (
                building_name,
                year,
                year,
                month,
                year,
                year,
                month,
            ),
        )
        row = cur.fetchone()
        if row:
            return float(row[0])
        return None

import sqlite3
import pandas as pd
from typing import List, Any


def save_to_sqlite(table_name: str, rows: List[Any], db_path: str = "zoho_data.db"):
    """
    Save a list of dataclass instances (or dicts) to a SQLite table.
    - table_name: Name of the SQLite table.
    - rows: List of dataclass instances or dicts.
    - db_path: Path to the SQLite database file.
    """
    if not rows:
        return
    # Convert dataclass instances to dicts if needed
    if not isinstance(rows[0], dict):
        rows = [row.__dict__ for row in rows]
    df = pd.DataFrame(rows)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)


def load_from_sqlite(table_name: str, db_path: str = "zoho_data.db") -> pd.DataFrame:
    """
    Load data from a SQLite table into a pandas DataFrame.
    """
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)

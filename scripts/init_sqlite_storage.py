import sqlite3
import os

DB_PATH = os.environ.get("SQLITE_DB_PATH", "data/zoho_data.db")

PUBLISHED_PRICES_SCHEMA = """
CREATE TABLE IF NOT EXISTS published_prices (
    building_name TEXT NOT NULL,
    year_from INTEGER NOT NULL,
    month_from INTEGER NOT NULL,
    year_to INTEGER NOT NULL,
    month_to INTEGER NOT NULL,
    price REAL NOT NULL,
    published_by TEXT,
    published_at TEXT,
    reason TEXT,
    PRIMARY KEY (building_name, year_from, month_from, year_to, month_to)
);
"""


def main():
    print(f"Initializing SQLite DB at: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(PUBLISHED_PRICES_SCHEMA)
        conn.commit()
    print("published_prices table created (if not exists). Done.")


if __name__ == "__main__":
    main()

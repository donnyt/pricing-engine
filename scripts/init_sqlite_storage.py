#!/usr/bin/env python3
"""
SQLite Storage Initialization Script

This script initializes the SQLite database with proper schema for all tables.
It's a wrapper around the comprehensive init_database.py script.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.init_database import init_database, verify_schema

DB_PATH = os.environ.get("SQLITE_DB_PATH", "data/zoho_data.db")


def main():
    """Initialize the SQLite database with proper schema."""
    print(f"Initializing SQLite DB at: {DB_PATH}")

    try:
        # Initialize database with proper schema
        init_database(DB_PATH)

        # Verify the schema
        verify_schema(DB_PATH)

        print("\n✅ SQLite storage initialization completed successfully!")

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

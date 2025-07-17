"""
Simple tests for Zoho Analytics upsert functionality.

These tests verify the core upsert logic without complex mocking.
"""

import pytest
import tempfile
import os
import sqlite3
import pandas as pd
from dataclasses import dataclass
from typing import Optional

from src.zoho_integration import (
    upsert_pnl_sms_by_month,
    upsert_pnl_sms_by_month_range,
)
from src.sqlite_storage import (
    save_to_sqlite,
    load_from_sqlite,
    delete_from_sqlite_by_year_month,
    delete_from_sqlite_by_range,
)


@dataclass
class MockPnlSmsRow:
    """Mock dataclass for testing PnL SMS data."""

    year: Optional[str] = None
    month: Optional[str] = None
    building_name: Optional[str] = None
    exp_total_po_expense_amount: Optional[str] = None
    po_seats_actual_occupied_pct: Optional[str] = None
    total_po_seats: Optional[str] = None
    po_seats_occupied_pct: Optional[str] = None


class TestZohoUpsertSimple:
    """Simple test class for Zoho upsert functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def sample_data_2025_05(self):
        """Sample data for May 2025."""
        return [
            MockPnlSmsRow(
                year="2025",
                month="5",
                building_name="Test Tower",
                exp_total_po_expense_amount="100000000",
                po_seats_actual_occupied_pct="0.8",
                total_po_seats="200",
                po_seats_occupied_pct="0.8",
            ),
            MockPnlSmsRow(
                year="2025",
                month="5",
                building_name="Test Building",
                exp_total_po_expense_amount="50000000",
                po_seats_actual_occupied_pct="0.6",
                total_po_seats="100",
                po_seats_occupied_pct="0.6",
            ),
        ]

    @pytest.fixture
    def sample_data_2025_06(self):
        """Sample data for June 2025."""
        return [
            MockPnlSmsRow(
                year="2025",
                month="6",
                building_name="Test Tower",
                exp_total_po_expense_amount="110000000",
                po_seats_actual_occupied_pct="0.85",
                total_po_seats="200",
                po_seats_occupied_pct="0.85",
            ),
        ]

    def test_upsert_logic_single_month(self, temp_db_path, sample_data_2025_05):
        """Test the core upsert logic for a single month."""
        # Test 1: Insert when no data exists
        # First, verify no data exists
        with sqlite3.connect(temp_db_path) as conn:
            # Create table if it doesn't exist
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pnl_sms_by_month (
                    year TEXT,
                    month TEXT,
                    building_name TEXT,
                    exp_total_po_expense_amount TEXT,
                    po_seats_actual_occupied_pct TEXT,
                    total_po_seats TEXT,
                    po_seats_occupied_pct TEXT
                )
            """
            )
            conn.commit()

        # Check initial state
        df_initial = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_initial) == 0

        # Simulate upsert: delete existing, then insert new
        delete_from_sqlite_by_year_month(
            "pnl_sms_by_month", 2025, 5, db_path=temp_db_path
        )
        save_to_sqlite(
            "pnl_sms_by_month",
            sample_data_2025_05,
            db_path=temp_db_path,
            if_exists="append",
        )

        # Verify data was inserted
        df_after = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_after) == 2
        assert df_after.iloc[0]["year"] == "2025"
        assert df_after.iloc[0]["month"] == "5"

        # Test 2: Update when data exists
        # Add some different data for the same month
        different_data = [
            MockPnlSmsRow(
                year="2025",
                month="5",
                building_name="Updated Tower",
                exp_total_po_expense_amount="200000000",
                po_seats_actual_occupied_pct="0.9",
                total_po_seats="300",
                po_seats_occupied_pct="0.9",
            ),
        ]

        # Simulate upsert: delete existing, then insert new
        delete_from_sqlite_by_year_month(
            "pnl_sms_by_month", 2025, 5, db_path=temp_db_path
        )
        save_to_sqlite(
            "pnl_sms_by_month", different_data, db_path=temp_db_path, if_exists="append"
        )

        # Verify data was updated
        df_updated = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_updated) == 1  # Only the new data
        assert df_updated.iloc[0]["building_name"] == "Updated Tower"
        assert df_updated.iloc[0]["exp_total_po_expense_amount"] == "200000000"

    def test_upsert_logic_range(
        self, temp_db_path, sample_data_2025_05, sample_data_2025_06
    ):
        """Test the core upsert logic for a range of months."""
        # Set up database
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pnl_sms_by_month (
                    year TEXT,
                    month TEXT,
                    building_name TEXT,
                    exp_total_po_expense_amount TEXT,
                    po_seats_actual_occupied_pct TEXT,
                    total_po_seats TEXT,
                    po_seats_occupied_pct TEXT
                )
            """
            )
            conn.commit()

        # Test 1: Insert range when no data exists
        # Simulate upsert range: delete existing range, then insert new data for each month
        delete_from_sqlite_by_range(
            "pnl_sms_by_month", 2025, 5, 2025, 6, db_path=temp_db_path
        )

        # Insert data for first month
        save_to_sqlite(
            "pnl_sms_by_month",
            sample_data_2025_05,
            db_path=temp_db_path,
            if_exists="append",
        )
        # Insert data for second month
        save_to_sqlite(
            "pnl_sms_by_month",
            sample_data_2025_06,
            db_path=temp_db_path,
            if_exists="append",
        )

        # Verify data was inserted for both months
        df_after = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_after) == 3  # 2 from May + 1 from June

        # Check May data
        df_may = df_after[df_after["month"] == "5"]
        assert len(df_may) == 2

        # Check June data
        df_june = df_after[df_after["month"] == "6"]
        assert len(df_june) == 1

        # Test 2: Update range when data exists
        # Add different data for the range
        different_data_may = [
            MockPnlSmsRow(
                year="2025",
                month="5",
                building_name="Updated May Tower",
                exp_total_po_expense_amount="300000000",
                po_seats_actual_occupied_pct="0.95",
                total_po_seats="400",
                po_seats_occupied_pct="0.95",
            ),
        ]

        different_data_june = [
            MockPnlSmsRow(
                year="2025",
                month="6",
                building_name="Updated June Tower",
                exp_total_po_expense_amount="400000000",
                po_seats_actual_occupied_pct="0.98",
                total_po_seats="500",
                po_seats_occupied_pct="0.98",
            ),
        ]

        # Simulate upsert range: delete existing range, then insert new data
        delete_from_sqlite_by_range(
            "pnl_sms_by_month", 2025, 5, 2025, 6, db_path=temp_db_path
        )
        save_to_sqlite(
            "pnl_sms_by_month",
            different_data_may,
            db_path=temp_db_path,
            if_exists="append",
        )
        save_to_sqlite(
            "pnl_sms_by_month",
            different_data_june,
            db_path=temp_db_path,
            if_exists="append",
        )

        # Verify data was updated
        df_updated = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_updated) == 2  # 1 from May + 1 from June

        # Check updated May data
        df_may_updated = df_updated[df_updated["month"] == "5"]
        assert len(df_may_updated) == 1
        assert df_may_updated.iloc[0]["building_name"] == "Updated May Tower"

        # Check updated June data
        df_june_updated = df_updated[df_updated["month"] == "6"]
        assert len(df_june_updated) == 1
        assert df_june_updated.iloc[0]["building_name"] == "Updated June Tower"

    def test_upsert_empty_data(self, temp_db_path):
        """Test upsert with empty data."""
        # Set up database
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pnl_sms_by_month (
                    year TEXT,
                    month TEXT,
                    building_name TEXT,
                    exp_total_po_expense_amount TEXT,
                    po_seats_actual_occupied_pct TEXT,
                    total_po_seats TEXT,
                    po_seats_occupied_pct TEXT
                )
            """
            )
            conn.commit()

        # Test upsert with empty data
        delete_from_sqlite_by_year_month(
            "pnl_sms_by_month", 2025, 5, db_path=temp_db_path
        )
        save_to_sqlite("pnl_sms_by_month", [], db_path=temp_db_path, if_exists="append")

        # Verify no data was inserted
        df_after = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_after) == 0

    def test_upsert_cross_year_range(self, temp_db_path):
        """Test upsert range that crosses year boundary."""
        # Set up database
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pnl_sms_by_month (
                    year TEXT,
                    month TEXT,
                    building_name TEXT,
                    exp_total_po_expense_amount TEXT,
                    po_seats_actual_occupied_pct TEXT,
                    total_po_seats TEXT,
                    po_seats_occupied_pct TEXT
                )
            """
            )
            conn.commit()

        # Create data for Dec 2024 and Jan 2025
        dec_2024_data = [
            MockPnlSmsRow(
                year="2024",
                month="12",
                building_name="Dec 2024 Tower",
                exp_total_po_expense_amount="100000000",
                po_seats_actual_occupied_pct="0.8",
                total_po_seats="200",
                po_seats_occupied_pct="0.8",
            ),
        ]

        jan_2025_data = [
            MockPnlSmsRow(
                year="2025",
                month="1",
                building_name="Jan 2025 Tower",
                exp_total_po_expense_amount="150000000",
                po_seats_actual_occupied_pct="0.85",
                total_po_seats="250",
                po_seats_occupied_pct="0.85",
            ),
        ]

        # Simulate upsert range across year boundary
        delete_from_sqlite_by_range(
            "pnl_sms_by_month", 2024, 12, 2025, 1, db_path=temp_db_path
        )
        save_to_sqlite(
            "pnl_sms_by_month", dec_2024_data, db_path=temp_db_path, if_exists="append"
        )
        save_to_sqlite(
            "pnl_sms_by_month", jan_2025_data, db_path=temp_db_path, if_exists="append"
        )

        # Verify data was inserted for both months
        df_after = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_after) == 2

        # Check Dec 2024 data
        df_dec = df_after[(df_after["year"] == "2024") & (df_after["month"] == "12")]
        assert len(df_dec) == 1
        assert df_dec.iloc[0]["building_name"] == "Dec 2024 Tower"

        # Check Jan 2025 data
        df_jan = df_after[(df_after["year"] == "2025") & (df_after["month"] == "1")]
        assert len(df_jan) == 1
        assert df_jan.iloc[0]["building_name"] == "Jan 2025 Tower"

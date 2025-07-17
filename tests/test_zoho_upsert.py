"""
Tests for Zoho Analytics upsert functionality.

These tests verify that the upsert operations correctly handle:
- Inserting new data when none exists
- Deleting and reinserting existing data
- Range operations for multiple months
"""

import pytest
import pandas as pd
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from typing import List, Optional

from src.zoho_integration import (
    upsert_pnl_sms_by_month,
    upsert_pnl_sms_by_month_range,
    fetch_pnl_sms_by_month_dataclasses,
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


class TestZohoUpsert:
    """Test class for Zoho upsert functionality."""

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

    def test_upsert_pnl_sms_by_month_new_data(self, temp_db_path, sample_data_2025_05):
        """Test upsert when no existing data exists."""
        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses",
            return_value=sample_data_2025_05,
        ):
            with patch("src.sqlite_storage.save_to_sqlite") as mock_save:
                with patch(
                    "src.sqlite_storage.delete_from_sqlite_by_year_month"
                ) as mock_delete:
                    # Call upsert
                    result = upsert_pnl_sms_by_month(2025, 5)

                    # Verify delete was called
                    mock_delete.assert_called_once_with("pnl_sms_by_month", 2025, 5)

                    # Verify save was called with append
                    mock_save.assert_called_once_with(
                        "pnl_sms_by_month", sample_data_2025_05, if_exists="append"
                    )

                    # Verify return value
                    assert result == 2

    def test_upsert_pnl_sms_by_month_existing_data(
        self, temp_db_path, sample_data_2025_05, sample_data_2025_06
    ):
        """Test upsert when existing data exists - should delete and reinsert."""
        # First, save some existing data
        save_to_sqlite("pnl_sms_by_month", sample_data_2025_05, db_path=temp_db_path)

        # Verify data exists
        df_before = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_before) == 2

        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses",
            return_value=sample_data_2025_06,
        ):
            with patch("src.sqlite_storage.save_to_sqlite") as mock_save:
                with patch(
                    "src.sqlite_storage.delete_from_sqlite_by_year_month"
                ) as mock_delete:
                    # Call upsert for the same month
                    result = upsert_pnl_sms_by_month(2025, 5)

                    # Verify delete was called
                    mock_delete.assert_called_once_with("pnl_sms_by_month", 2025, 5)

                    # Verify save was called with append
                    mock_save.assert_called_once_with(
                        "pnl_sms_by_month", sample_data_2025_06, if_exists="append"
                    )

                    # Verify return value
                    assert result == 1

    def test_upsert_pnl_sms_by_month_range_new_data(
        self, temp_db_path, sample_data_2025_05, sample_data_2025_06
    ):
        """Test upsert range when no existing data exists."""
        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses"
        ) as mock_fetch:
            mock_fetch.side_effect = [sample_data_2025_05, sample_data_2025_06]

            with patch("src.sqlite_storage.save_to_sqlite") as mock_save:
                with patch(
                    "src.sqlite_storage.delete_from_sqlite_by_range"
                ) as mock_delete:
                    # Call upsert range
                    result = upsert_pnl_sms_by_month_range(2025, 5, 2025, 6)

                    # Verify delete was called for the range
                    mock_delete.assert_called_once_with(
                        "pnl_sms_by_month", 2025, 5, 2025, 6
                    )

                    # Verify save was called twice (once for each month)
                    assert mock_save.call_count == 2

                    # Verify fetch was called twice
                    assert mock_fetch.call_count == 2
                    mock_fetch.assert_any_call(2025, 5)
                    mock_fetch.assert_any_call(2025, 6)

                    # Verify return value (total rows from both months)
                    assert result == 3

    def test_upsert_pnl_sms_by_month_range_existing_data(
        self, temp_db_path, sample_data_2025_05, sample_data_2025_06
    ):
        """Test upsert range when existing data exists."""
        # First, save some existing data
        save_to_sqlite("pnl_sms_by_month", sample_data_2025_05, db_path=temp_db_path)

        # Verify data exists
        df_before = load_from_sqlite("pnl_sms_by_month", db_path=temp_db_path)
        assert len(df_before) == 2

        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses"
        ) as mock_fetch:
            mock_fetch.side_effect = [sample_data_2025_05, sample_data_2025_06]

            with patch("src.sqlite_storage.save_to_sqlite") as mock_save:
                with patch(
                    "src.sqlite_storage.delete_from_sqlite_by_range"
                ) as mock_delete:
                    # Call upsert range
                    result = upsert_pnl_sms_by_month_range(2025, 5, 2025, 6)

                    # Verify delete was called for the range
                    mock_delete.assert_called_once_with(
                        "pnl_sms_by_month", 2025, 5, 2025, 6
                    )

                    # Verify save was called twice
                    assert mock_save.call_count == 2

                    # Verify return value
                    assert result == 3

    def test_upsert_pnl_sms_by_month_empty_result(self, temp_db_path):
        """Test upsert when Zoho returns empty data."""
        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses", return_value=[]
        ):
            with patch("src.sqlite_storage.save_to_sqlite") as mock_save:
                with patch(
                    "src.sqlite_storage.delete_from_sqlite_by_year_month"
                ) as mock_delete:
                    # Call upsert
                    result = upsert_pnl_sms_by_month(2025, 5)

                    # Verify delete was called
                    mock_delete.assert_called_once_with("pnl_sms_by_month", 2025, 5)

                    # Verify save was called with empty list
                    mock_save.assert_called_once_with(
                        "pnl_sms_by_month", [], if_exists="append"
                    )

                    # Verify return value
                    assert result == 0

    def test_upsert_pnl_sms_by_month_range_cross_year(
        self, temp_db_path, sample_data_2025_05, sample_data_2025_06
    ):
        """Test upsert range that crosses year boundary."""
        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses"
        ) as mock_fetch:
            mock_fetch.side_effect = [sample_data_2025_05, sample_data_2025_06]

            with patch("src.sqlite_storage.save_to_sqlite") as mock_save:
                with patch(
                    "src.sqlite_storage.delete_from_sqlite_by_range"
                ) as mock_delete:
                    # Call upsert range that crosses year (Dec 2024 to Jan 2025)
                    result = upsert_pnl_sms_by_month_range(2024, 12, 2025, 1)

                    # Verify delete was called for the range
                    mock_delete.assert_called_once_with(
                        "pnl_sms_by_month", 2024, 12, 2025, 1
                    )

                    # Verify fetch was called for both months
                    assert mock_fetch.call_count == 2
                    mock_fetch.assert_any_call(2024, 12)
                    mock_fetch.assert_any_call(2025, 1)

                    # Verify save was called twice
                    assert mock_save.call_count == 2

                    # Verify return value
                    assert result == 3

    def test_upsert_pnl_sms_by_month_range_single_month(
        self, temp_db_path, sample_data_2025_05
    ):
        """Test upsert range for a single month (start and end same)."""
        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses",
            return_value=sample_data_2025_05,
        ):
            with patch("src.sqlite_storage.save_to_sqlite") as mock_save:
                with patch(
                    "src.sqlite_storage.delete_from_sqlite_by_range"
                ) as mock_delete:
                    # Call upsert range for same start and end
                    result = upsert_pnl_sms_by_month_range(2025, 5, 2025, 5)

                    # Verify delete was called for the range
                    mock_delete.assert_called_once_with(
                        "pnl_sms_by_month", 2025, 5, 2025, 5
                    )

                    # Verify fetch was called once
                    assert mock_fetch.call_count == 1
                    mock_fetch.assert_any_call(2025, 5)

                    # Verify save was called once
                    assert mock_save.call_count == 1

                    # Verify return value
                    assert result == 2

    def test_upsert_pnl_sms_by_month_range_rate_limiting(
        self, temp_db_path, sample_data_2025_05, sample_data_2025_06
    ):
        """Test that rate limiting delay is applied between API calls."""
        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses"
        ) as mock_fetch:
            mock_fetch.side_effect = [sample_data_2025_05, sample_data_2025_06]

            with patch("src.sqlite_storage.save_to_sqlite") as mock_save:
                with patch(
                    "src.sqlite_storage.delete_from_sqlite_by_range"
                ) as mock_delete:
                    with patch("time.sleep") as mock_sleep:
                        # Call upsert range
                        result = upsert_pnl_sms_by_month_range(2025, 5, 2025, 6)

                        # Verify sleep was called once (between the two months)
                        mock_sleep.assert_called_once_with(2)

                        # Verify return value
                        assert result == 3


class TestZohoUpsertIntegration:
    """Integration tests for Zoho upsert functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_upsert_integration_with_real_sqlite(self, temp_db_path):
        """Test upsert with real SQLite operations."""
        # Create sample data
        sample_data = [
            MockPnlSmsRow(
                year="2025",
                month="5",
                building_name="Test Tower",
                exp_total_po_expense_amount="100000000",
                po_seats_actual_occupied_pct="0.8",
                total_po_seats="200",
                po_seats_occupied_pct="0.8",
            ),
        ]

        # Mock the fetch function to return our sample data
        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses",
            return_value=sample_data,
        ):
            # Call upsert
            result = upsert_pnl_sms_by_month(2025, 5)

            # Verify return value
            assert result == 1

            # Verify data was actually saved to SQLite
            df = load_from_sqlite("pnl_sms_by_month")
            assert len(df) == 1
            assert df.iloc[0]["year"] == "2025"
            assert df.iloc[0]["month"] == "5"
            assert df.iloc[0]["building_name"] == "Test Tower"

    def test_upsert_range_integration_with_real_sqlite(self, temp_db_path):
        """Test upsert range with real SQLite operations."""
        # Create sample data for two months
        sample_data_1 = [
            MockPnlSmsRow(
                year="2025",
                month="5",
                building_name="Test Tower",
                exp_total_po_expense_amount="100000000",
                po_seats_actual_occupied_pct="0.8",
                total_po_seats="200",
                po_seats_occupied_pct="0.8",
            ),
        ]

        sample_data_2 = [
            MockPnlSmsRow(
                year="2025",
                month="6",
                building_name="Test Building",
                exp_total_po_expense_amount="50000000",
                po_seats_actual_occupied_pct="0.6",
                total_po_seats="100",
                po_seats_occupied_pct="0.6",
            ),
        ]

        # Mock the fetch function to return our sample data
        with patch(
            "src.zoho_integration.fetch_pnl_sms_by_month_dataclasses"
        ) as mock_fetch:
            mock_fetch.side_effect = [sample_data_1, sample_data_2]

            # Call upsert range
            result = upsert_pnl_sms_by_month_range(2025, 5, 2025, 6)

            # Verify return value
            assert result == 2

            # Verify data was actually saved to SQLite
            df = load_from_sqlite("pnl_sms_by_month")
            assert len(df) == 2

            # Verify first month data
            df_2025_05 = df[df["month"] == "5"]
            assert len(df_2025_05) == 1
            assert df_2025_05.iloc[0]["building_name"] == "Test Tower"

            # Verify second month data
            df_2025_06 = df[df["month"] == "6"]
            assert len(df_2025_06) == 1
            assert df_2025_06.iloc[0]["building_name"] == "Test Building"

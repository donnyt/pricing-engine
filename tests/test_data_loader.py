"""
Tests for DataLoaderService

This module tests the centralized data loading service to ensure it works correctly
and follows the Single Responsibility Principle.
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, date
from src.data.loader import DataLoaderService


class TestDataLoaderService(unittest.TestCase):
    """Test cases for DataLoaderService."""

    def setUp(self):
        """Set up test fixtures."""
        self.data_loader = DataLoaderService()

    def test_data_loader_initialization(self):
        """Test that DataLoaderService can be initialized."""
        self.assertIsNotNone(self.data_loader)
        self.assertIsInstance(self.data_loader, DataLoaderService)

    def test_load_merged_pricing_data_default_date(self):
        """Test that load_merged_pricing_data uses today's date when none provided."""
        with patch.object(
            self.data_loader, "load_monthly_expense_data"
        ) as mock_monthly:
            with patch.object(
                self.data_loader, "load_daily_occupancy_data"
            ) as mock_daily:
                mock_monthly.return_value = pd.DataFrame()
                mock_daily.return_value = pd.DataFrame()

                # Call without target_date
                self.data_loader.load_merged_pricing_data(auto_fetch=False)

                # Verify that load_daily_occupancy_data was called with today's date
                mock_daily.assert_called_once()
                call_args = mock_daily.call_args[0]
                self.assertEqual(call_args[0], date.today().strftime("%Y-%m-%d"))

    def test_load_merged_pricing_data_with_empty_data(self):
        """Test that load_merged_pricing_data handles empty data gracefully."""
        with patch.object(
            self.data_loader, "load_monthly_expense_data"
        ) as mock_monthly:
            with patch.object(
                self.data_loader, "load_daily_occupancy_data"
            ) as mock_daily:
                mock_monthly.return_value = pd.DataFrame()
                mock_daily.return_value = pd.DataFrame()

                # Call with empty data
                result = self.data_loader.load_merged_pricing_data(auto_fetch=False)

                # Should return empty DataFrame
                self.assertTrue(result.empty)

    def test_load_merged_pricing_data_with_monthly_only(self):
        """Test that load_merged_pricing_data works with only monthly data."""
        with patch.object(
            self.data_loader, "load_monthly_expense_data"
        ) as mock_monthly:
            with patch.object(
                self.data_loader, "load_daily_occupancy_data"
            ) as mock_daily:
                # Mock monthly data
                monthly_data = pd.DataFrame(
                    {
                        "building_name": ["Pacific Place"],
                        "year": [2024],
                        "month": [1],
                        "exp_total_po_expense_amount": [1000],
                    }
                )
                mock_monthly.return_value = monthly_data
                mock_daily.return_value = pd.DataFrame()

                # Call with monthly data only
                result = self.data_loader.load_merged_pricing_data(auto_fetch=False)

                # Should return monthly data
                self.assertFalse(result.empty)
                self.assertEqual(len(result), 1)
                self.assertIn("exp_total_po_expense_amount", result.columns)

    def test_load_merged_pricing_data_with_both_data_types(self):
        """Test that load_merged_pricing_data merges both data types correctly."""
        with patch.object(
            self.data_loader, "load_monthly_expense_data"
        ) as mock_monthly:
            with patch.object(
                self.data_loader, "load_daily_occupancy_data"
            ) as mock_daily:
                # Mock monthly data
                monthly_data = pd.DataFrame(
                    {
                        "building_name": ["Pacific Place"],
                        "year": [2024],
                        "month": [1],
                        "exp_total_po_expense_amount": [1000],
                    }
                )

                # Mock daily data
                daily_data = pd.DataFrame(
                    {
                        "building_name": ["Pacific Place"],
                        "date": ["2024-01-15"],
                        "po_seats_occupied_actual_pct": [75.5],
                    }
                )

                mock_monthly.return_value = monthly_data
                mock_daily.return_value = daily_data

                # Call with both data types
                result = self.data_loader.load_merged_pricing_data(
                    "2024-01-15", auto_fetch=False
                )

                # Should return merged data
                self.assertFalse(result.empty)
                self.assertEqual(len(result), 1)
                # Should have both monthly and daily data columns
                self.assertIn("exp_total_po_expense_amount", result.columns)
                self.assertIn("po_seats_occupied_actual_pct", result.columns)

    def test_auto_fetch_parameter_handling(self):
        """Test that auto_fetch parameter is handled correctly."""
        with patch.object(
            self.data_loader, "load_monthly_expense_data"
        ) as mock_monthly:
            with patch.object(
                self.data_loader, "load_daily_occupancy_data"
            ) as mock_daily:
                mock_monthly.return_value = pd.DataFrame()
                mock_daily.return_value = pd.DataFrame()

                # Test with auto_fetch=False
                self.data_loader.load_merged_pricing_data(auto_fetch=False)

                # Verify that load_daily_occupancy_data was called with auto_fetch=False
                mock_daily.assert_called_once()
                call_args = mock_daily.call_args[0]
                call_kwargs = mock_daily.call_args[1]
                # auto_fetch should be the third positional argument
                self.assertFalse(call_args[2])

    def test_auto_fetch_default_value(self):
        """Test that auto_fetch defaults to True."""
        with patch.object(
            self.data_loader, "load_monthly_expense_data"
        ) as mock_monthly:
            with patch.object(
                self.data_loader, "load_daily_occupancy_data"
            ) as mock_daily:
                mock_monthly.return_value = pd.DataFrame()
                mock_daily.return_value = pd.DataFrame()

                # Test without specifying auto_fetch (should default to True)
                self.data_loader.load_merged_pricing_data()

                # Verify that load_daily_occupancy_data was called with auto_fetch=True
                mock_daily.assert_called_once()
                call_args = mock_daily.call_args[0]
                # auto_fetch should be the third positional argument
                self.assertTrue(call_args[2])


if __name__ == "__main__":
    unittest.main()

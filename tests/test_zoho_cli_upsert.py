"""
Tests for Zoho CLI upsert functionality.

These tests verify that the CLI upsert commands correctly:
- Parse arguments and call the appropriate functions
- Handle different report types
- Provide proper error messages
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from io import StringIO
from dataclasses import dataclass
from typing import Optional

from src.zoho_cli import (
    upsert_data,
    upsert_data_range,
    fetch_replace,
    main,
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


class TestZohoCliUpsert:
    """Test class for Zoho CLI upsert functionality."""

    def test_upsert_data_success(self):
        """Test successful upsert data operation."""
        with patch(
            "src.zoho_cli.upsert_pnl_sms_by_month", return_value=5
        ) as mock_upsert:
            # Capture stdout to check output
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                upsert_data("pnl_sms_by_month", 2025, 5)

                # Verify the function was called
                mock_upsert.assert_called_once_with(2025, 5)

                # Verify output message
                output = mock_stdout.getvalue()
                assert "Upserted 5 rows for 2025-05 in 'pnl_sms_by_month'." in output

    def test_upsert_data_missing_parameters(self):
        """Test upsert data with missing year/month parameters."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            upsert_data("pnl_sms_by_month", None, None)

            # Verify error message
            output = mock_stdout.getvalue()
            assert "--year and --month are required for pnl_sms_by_month" in output

    def test_upsert_data_unsupported_report(self):
        """Test upsert data with unsupported report type."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            upsert_data("unsupported_report", 2025, 5)

            # Verify error message
            output = mock_stdout.getvalue()
            assert "Report 'unsupported_report' not supported yet." in output

    def test_upsert_data_range_success(self):
        """Test successful upsert data range operation."""
        with patch(
            "src.zoho_cli.upsert_pnl_sms_by_month_range", return_value=10
        ) as mock_upsert:
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                upsert_data_range("pnl_sms_by_month", 2025, 1, 2025, 5)

                # Verify the function was called
                mock_upsert.assert_called_once_with(2025, 1, 2025, 5)

                # Verify output message
                output = mock_stdout.getvalue()
                assert (
                    "Upserted 10 rows for 2025-01 to 2025-05 in 'pnl_sms_by_month'."
                    in output
                )

    def test_upsert_data_range_unsupported_report(self):
        """Test upsert data range with unsupported report type."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            upsert_data_range("unsupported_report", 2025, 1, 2025, 5)

            # Verify error message
            output = mock_stdout.getvalue()
            assert "Report 'unsupported_report' not supported yet." in output


class TestZohoCliMain:
    """Test class for Zoho CLI main function."""

    def test_main_upsert_command(self):
        """Test main function with upsert command."""
        with patch(
            "sys.argv",
            [
                "zoho_cli.py",
                "upsert",
                "--report",
                "pnl_sms_by_month",
                "--year",
                "2025",
                "--month",
                "5",
            ],
        ):
            with patch("src.zoho_cli.upsert_data") as mock_upsert:
                main()

                # Verify upsert_data was called
                mock_upsert.assert_called_once_with("pnl_sms_by_month", 2025, 5)

    def test_main_upsert_range_command(self):
        """Test main function with upsert-range command."""
        with patch(
            "sys.argv",
            [
                "zoho_cli.py",
                "upsert-range",
                "--report",
                "pnl_sms_by_month",
                "--start-year",
                "2025",
                "--start-month",
                "1",
                "--end-year",
                "2025",
                "--end-month",
                "5",
            ],
        ):
            with patch("src.zoho_cli.upsert_data_range") as mock_upsert_range:
                main()

                # Verify upsert_data_range was called
                mock_upsert_range.assert_called_once_with(
                    "pnl_sms_by_month", 2025, 1, 2025, 5
                )

    def test_main_legacy_fetch_replace_command(self):
        """Test main function with legacy fetch-replace command."""
        with patch(
            "sys.argv",
            [
                "zoho_cli.py",
                "fetch-replace",
                "--report",
                "pnl_sms_by_month",
                "--year",
                "2025",
                "--month",
                "5",
            ],
        ):
            with patch("src.zoho_cli.fetch_replace") as mock_fetch:
                main()

                # Verify fetch_replace was called
                mock_fetch.assert_called_once_with("pnl_sms_by_month", 2025, 5)

    def test_main_load_command(self):
        """Test main function with load command."""
        with patch("sys.argv", ["zoho_cli.py", "load", "--report", "pnl_sms_by_month"]):
            with patch("src.zoho_cli.load_and_preview") as mock_load:
                main()

                # Verify load_and_preview was called
                mock_load.assert_called_once_with("pnl_sms_by_month")

    def test_main_no_command(self):
        """Test main function with no command (should show help)."""
        with patch("sys.argv", ["zoho_cli.py"]):
            with patch("argparse.ArgumentParser.print_help") as mock_help:
                main()

                # Verify help was called
                mock_help.assert_called_once()

    def test_main_unknown_command(self):
        """Test main function with unknown command (should exit with error)."""
        with patch("sys.argv", ["zoho_cli.py", "unknown-command"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

                # Verify it exits with error code 2
                assert exc_info.value.code == 2


class TestZohoCliIntegration:
    """Integration tests for Zoho CLI functionality."""

    def test_cli_help_output(self):
        """Test that CLI help output includes new upsert commands."""
        with patch("sys.argv", ["zoho_cli.py", "--help"]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                try:
                    main()
                except SystemExit:
                    pass  # argparse calls sys.exit() when showing help

                # Verify help output includes upsert commands
                output = mock_stdout.getvalue()
                assert "upsert" in output
                assert "upsert-range" in output
                assert "Upsert Zoho data to SQLite" in output

    def test_upsert_command_help(self):
        """Test that upsert command help is properly formatted."""
        with patch("sys.argv", ["zoho_cli.py", "upsert", "--help"]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                try:
                    main()
                except SystemExit:
                    pass

                # Verify help output
                output = mock_stdout.getvalue()
                assert "--report" in output
                assert "--year" in output
                assert "--month" in output

    def test_upsert_range_command_help(self):
        """Test that upsert-range command help is properly formatted."""
        with patch("sys.argv", ["zoho_cli.py", "upsert-range", "--help"]):
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                try:
                    main()
                except SystemExit:
                    pass

                # Verify help output
                output = mock_stdout.getvalue()
                assert "--report" in output
                assert "--start-year" in output
                assert "--start-month" in output
                assert "--end-year" in output
                assert "--end-month" in output


class TestZohoCliErrorHandling:
    """Test error handling in Zoho CLI."""

    def test_upsert_data_with_none_values(self):
        """Test upsert data with None values for year/month."""
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            upsert_data("pnl_sms_by_month", None, 5)

            # Verify error message
            output = mock_stdout.getvalue()
            assert "--year and --month are required for pnl_sms_by_month" in output

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            upsert_data("pnl_sms_by_month", 2025, None)

            # Verify error message
            output = mock_stdout.getvalue()
            assert "--year and --month are required for pnl_sms_by_month" in output

    def test_upsert_data_range_with_invalid_range(self):
        """Test upsert data range with invalid date range."""
        # This test would be useful if we add validation for date ranges
        # For now, we'll test that the function handles the call correctly
        with patch(
            "src.zoho_cli.upsert_pnl_sms_by_month_range", return_value=0
        ) as mock_upsert:
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                # Test with end date before start date (should still work but return 0)
                upsert_data_range("pnl_sms_by_month", 2025, 5, 2025, 1)

                # Verify the function was called
                mock_upsert.assert_called_once_with(2025, 5, 2025, 1)

                # Verify output message
                output = mock_stdout.getvalue()
                assert (
                    "Upserted 0 rows for 2025-05 to 2025-01 in 'pnl_sms_by_month'."
                    in output
                )

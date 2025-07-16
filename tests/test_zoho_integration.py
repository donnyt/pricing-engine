import os
import pytest
from zoho_integration import fetch_pnl_sms_by_month_dataclasses


@pytest.mark.skipif(
    not all(
        [
            os.environ.get("ZOHO_CLIENT_ID"),
            os.environ.get("ZOHO_CLIENT_SECRET"),
            os.environ.get("ZOHO_REFRESH_TOKEN"),
        ]
    ),
    reason="Zoho credentials not set in environment variables",
)
def test_zoho_connection():
    # Use a known year/month that should return data, or just check for no error
    year = 2025
    month = 5
    rows = fetch_pnl_sms_by_month_dataclasses(year, month)
    assert isinstance(rows, list)
    # Optionally: assert len(rows) > 0 if you expect data

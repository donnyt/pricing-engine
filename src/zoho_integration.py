import os
import requests
import csv
import io
from typing import List, Optional, Type, Any
from dataclasses import dataclass, make_dataclass, fields
import re
from sqlite_storage import (
    delete_from_sqlite_by_year_month,
    delete_from_sqlite_by_range,
    save_to_sqlite,
)
import time


def get_zoho_access_token(
    client_id: str, client_secret: str, refresh_token: str
) -> str:
    """Obtain a Zoho OAuth2 access token using a refresh token."""
    token_url = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
    }
    response = requests.post(token_url, data=params)
    if response.status_code == 200:
        return response.json()["access_token"]
    raise Exception(f"Failed to get access token: {response.text}")


def fetch_zoho_analytics_data(
    access_token: str, endpoint_path: str, criteria: Optional[str] = None
) -> Optional[List[List[str]]]:
    """Fetch CSV data from Zoho Analytics API and return as list of rows."""
    api_base_url = os.environ.get(
        "ZOHO_API_BASE_URL", "https://analyticsapi.zoho.com/api/donny@go-work.com"
    )
    query_params = "?ZOHO_ACTION=EXPORT&ZOHO_OUTPUT_FORMAT=CSV&ZOHO_ERROR_FORMAT=XML&ZOHO_API_VERSION=1.0"
    url = f"{api_base_url}{endpoint_path}{query_params}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {}
    if criteria:
        data["ZOHO_CRITERIA"] = criteria
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        csv_content = response.text
        reader = csv.reader(io.StringIO(csv_content))
        return list(reader)
    print(f"Error: {response.status_code} - {response.text}")
    return None


def sanitize_field_name(name: str) -> str:
    """Sanitize CSV header to be a valid Python identifier."""
    # Remove BOM if present
    name = name.lstrip("\ufeff")
    # Replace spaces and invalid chars with underscore, remove leading digits
    name = re.sub(r"\W|^(?=\d)", "_", name)
    return name


def make_dynamic_dataclass(class_name: str, field_names: List[str]) -> Type[Any]:
    """Dynamically create a dataclass with the given field names (all as Optional[str])."""
    sanitized = [sanitize_field_name(f) for f in field_names]
    return make_dataclass(class_name, [(f, Optional[str], None) for f in sanitized])


def fetch_zoho_table_as_dataclasses(
    table_name: str,
    endpoint_path: str,
    criteria: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> List[Any]:
    """
    General-purpose function to fetch any Zoho Analytics table as a list of dataclass instances.
    Args:
        table_name: Name for the dataclass (e.g., 'PnlSmsByMonthRow').
        endpoint_path: API endpoint path for the table.
        criteria: Optional filter criteria.
        client_id, client_secret, refresh_token: Optional Zoho credentials (fallback to env).
    Returns:
        List of dataclass instances (one per row).
    """
    # Get credentials from args or environment
    client_id = client_id or os.environ.get("ZOHO_CLIENT_ID")
    client_secret = client_secret or os.environ.get("ZOHO_CLIENT_SECRET")
    refresh_token = refresh_token or os.environ.get("ZOHO_REFRESH_TOKEN")
    if not all([client_id, client_secret, refresh_token]):
        raise EnvironmentError(
            "Missing Zoho credentials in environment variables or arguments."
        )
    access_token = get_zoho_access_token(client_id, client_secret, refresh_token)
    rows = fetch_zoho_analytics_data(access_token, endpoint_path, criteria)
    if not rows or len(rows) < 2:
        return []
    header, *data_rows = rows
    sanitized_header = [sanitize_field_name(h) for h in header]
    DataRow = make_dynamic_dataclass(table_name, header)
    return [DataRow(**dict(zip(sanitized_header, row))) for row in data_rows]


def fetch_pnl_sms_by_month_dataclasses(year: int, month: int) -> List[Any]:
    """
    Fetch pnl_sms_by_month as dataclass instances for a specific year and month.
    """
    endpoint_path = "/OKR/pnl_sms_by_month"
    criteria = f'("year"={year} and "month"={month})'
    return fetch_zoho_table_as_dataclasses(
        table_name="PnlSmsByMonthRow",
        endpoint_path=endpoint_path,
        criteria=criteria,
    )


def clear_and_reload_pnl_sms_by_month(year: int, month: int):
    """
    Clear previous pnl_sms_by_month data for the given year and month, then fetch and reload new data.
    """
    delete_from_sqlite_by_year_month("pnl_sms_by_month", year, month)
    rows = fetch_pnl_sms_by_month_dataclasses(year, month)
    save_to_sqlite("pnl_sms_by_month", rows)  # default is replace
    return len(rows)


def clear_and_reload_pnl_sms_by_month_range(
    start_year: int, start_month: int, end_year: int, end_month: int
):
    """
    Clear previous pnl_sms_by_month data for the given range, then fetch and reload new data for each month in the range.
    """
    delete_from_sqlite_by_range(
        "pnl_sms_by_month", start_year, start_month, end_year, end_month
    )
    ym = []
    y, m = start_year, start_month
    while (y < end_year) or (y == end_year and m <= end_month):
        ym.append((y, m))
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1
    total_rows = 0
    for i, (year, month) in enumerate(ym):
        if i > 0:
            time.sleep(2)  # Add delay to avoid API rate limiting
        rows = fetch_pnl_sms_by_month_dataclasses(year, month)
        save_to_sqlite("pnl_sms_by_month", rows, if_exists="append")
        total_rows += len(rows)
    return total_rows


if __name__ == "__main__":
    # Quick test: fetch May 2025 pnl_sms_by_month report and print first 2 rows as dataclasses
    try:
        rows = fetch_pnl_sms_by_month_dataclasses(2025, 5)
        for row in rows[:2]:
            print(row)
        if not rows:
            print("No data returned.")
    except Exception as e:
        print(f"Test failed: {e}")

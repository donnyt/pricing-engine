import os
import requests
import csv
import io
from typing import List, Optional


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


def fetch_pnl_sms_by_month(year: int, month: int) -> Optional[List[List[str]]]:
    """
    Fetch the pnl_sms_by_month report for a specific year and month from Zoho Analytics.
    Args:
        year: The year to filter on.
        month: The month to filter on.
    Returns:
        List of rows (including header) or None if error.
    """
    client_id = os.environ.get("ZOHO_CLIENT_ID")
    client_secret = os.environ.get("ZOHO_CLIENT_SECRET")
    refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN")
    if not all([client_id, client_secret, refresh_token]):
        raise EnvironmentError("Missing Zoho credentials in environment variables.")
    access_token = get_zoho_access_token(client_id, client_secret, refresh_token)
    endpoint_path = "/OKR/pnl_sms_by_month"
    criteria = f'("year"={year} and "month"={month})'
    return fetch_zoho_analytics_data(access_token, endpoint_path, criteria)


if __name__ == "__main__":
    # Quick test: fetch May 2025 pnl_sms_by_month report and print first 5 rows
    try:
        rows = fetch_pnl_sms_by_month(2025, 5)
        if rows:
            for row in rows[:5]:
                print(row)
        else:
            print("No data returned.")
    except Exception as e:
        print(f"Test failed: {e}")

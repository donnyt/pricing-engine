import sys
from po_pricing_engine import (
    get_location_rules,
    DynamicPricingTier,
    LocationData,
    PricingRules,
    load_pricing_rules,
)
from pricing.calculator import PricingCalculator

if __name__ == "__main__":
    print("Testing Zoho Analytics Integration with real credentials...")
    try:
        token = get_access_token()
        print(f"Access token retrieved: {token[:8]}... (truncated)")
    except Exception as e:
        print(f"Failed to get access token: {e}")
        sys.exit(1)

    # TODO: Replace with your actual API path and params
    api_path = "workspaces/<workspace_id>/views/<view_name>/data"
    params = {}  # Add any required query params here
    try:
        data = get_zoho_data(api_path, params=params)
        print("Data retrieved from Zoho Analytics:")
        print(data)
    except Exception as e:
        print(f"Failed to get data from Zoho Analytics: {e}")
        sys.exit(1)

    print("Test completed.")

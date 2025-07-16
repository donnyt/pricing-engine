import pandas as pd
from src.pricing_pipeline import run_pricing_pipeline


def mock_config():
    return {
        "margin_of_safety": 0.5,
        "dynamic_pricing_tiers": [
            {"min_occupancy": 0.0, "max_occupancy": 1.0, "multiplier": 1.0}
        ],
        "locations": {
            "Test Tower": {
                "min_price": 0,
                "max_price": 2900000,
                "margin_of_safety": 0.5,
                "dynamic_pricing_tiers": [
                    {"min_occupancy": 0.0, "max_occupancy": 1.0, "multiplier": 1.0}
                ],
                "target_breakeven_occupancy": 0.5,
            }
        },
    }


def test_three_month_average_and_no_negative_price():
    # 4 months of negative expenses, should use abs values for average
    data = [
        {
            "year": 2025,
            "month": 4,
            "building_name": "Test Tower",
            "exp_total_po_expense_amount": -100000000,
            "po_seats_actual_occupied_pct": 0.8,
            "total_po_seats": 200,
            "po_seats_occupied_pct": 0.8,
        },
        {
            "year": 2025,
            "month": 5,
            "building_name": "Test Tower",
            "exp_total_po_expense_amount": -100000000,
            "po_seats_actual_occupied_pct": 0.8,
            "total_po_seats": 200,
            "po_seats_occupied_pct": 0.8,
        },
        {
            "year": 2025,
            "month": 6,
            "building_name": "Test Tower",
            "exp_total_po_expense_amount": -100000000,
            "po_seats_actual_occupied_pct": 0.8,
            "total_po_seats": 200,
            "po_seats_occupied_pct": 0.8,
        },
        {
            "year": 2025,
            "month": 7,
            "building_name": "Test Tower",
            "exp_total_po_expense_amount": -100000000,
            "po_seats_actual_occupied_pct": 0.8,
            "total_po_seats": 200,
            "po_seats_occupied_pct": 0.8,
        },
    ]
    df = pd.DataFrame(data)
    config = mock_config()
    outputs = run_pricing_pipeline(
        df, config, target_year=2025, target_month=7, verbose=False
    )
    assert len(outputs) == 1
    output = outputs[0]
    # The average should be abs(-1000)+abs(-2000)+abs(-3000) / 3 = 2000
    # Breakeven = 2000 / (10 * 0.7) = ~285.71, rounded to nearest 50,000 = 0
    assert output.recommended_price == 1_500_000


def test_average_with_missing_months():
    # Only 2 months available before target
    data = [
        {
            "year": 2025,
            "month": 5,
            "building_name": "Test Tower",
            "exp_total_po_expense_amount": -100000000,
            "po_seats_actual_occupied_pct": 0.8,
            "total_po_seats": 200,
            "po_seats_occupied_pct": 0.8,
        },
        {
            "year": 2025,
            "month": 6,
            "building_name": "Test Tower",
            "exp_total_po_expense_amount": -100000000,
            "po_seats_actual_occupied_pct": 0.8,
            "total_po_seats": 200,
            "po_seats_occupied_pct": 0.8,
        },
        {
            "year": 2025,
            "month": 7,
            "building_name": "Test Tower",
            "exp_total_po_expense_amount": -100000000,
            "po_seats_actual_occupied_pct": 0.8,
            "total_po_seats": 200,
            "po_seats_occupied_pct": 0.8,
        },
    ]
    df = pd.DataFrame(data)
    config = mock_config()
    outputs = run_pricing_pipeline(
        df, config, target_year=2025, target_month=7, verbose=False
    )
    assert len(outputs) == 1
    output = outputs[0]
    assert output.recommended_price == 1_000_000

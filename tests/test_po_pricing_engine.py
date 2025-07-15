import pytest
from src.po_pricing_engine import (
    calculate_breakeven_price_per_pax,
    apply_dynamic_pricing,
    apply_margin_of_safety,
    enforce_min_max_price,
    get_location_rules,
    DynamicPricingTier,
    LocationData,
    PricingRules,
    load_pricing_rules,
)


def test_calculate_breakeven_price_per_pax():
    data = LocationData(
        name="Test Location",
        exp_total_po_expense_amount=1000000,
        po_seats_actual_occupied_pct=0.5,
        total_po_seats=10,
    )
    # 1000000 / (10 * 0.5) = 200000, rounded to 200000
    assert calculate_breakeven_price_per_pax(data, 0.5) == 200000


def test_apply_dynamic_pricing():
    tiers = [
        DynamicPricingTier(min_occupancy=0.0, max_occupancy=0.5, multiplier=0.8),
        DynamicPricingTier(min_occupancy=0.5, max_occupancy=1.0, multiplier=1.2),
    ]
    # 200000 * 0.8 = 160000, rounded to 150000
    assert apply_dynamic_pricing(200000, 0.4, tiers) == 150000
    # 200000 * 1.2 = 240000, rounded to 250000
    assert apply_dynamic_pricing(200000, 0.6, tiers) == 250000


def test_apply_margin_of_safety():
    # 200000 * 1.5 = 300000, rounded to 300000
    assert apply_margin_of_safety(200000, 0.5) == 300000
    # 200000 * 0.2 = 40000, 200000+40000=240000, rounded to 250000
    assert apply_margin_of_safety(200000, 0.2) == 250000


def test_enforce_min_max_price():
    # Price below min
    assert enforce_min_max_price(100000, 200000, 300000) == 200000
    # Price above max
    assert enforce_min_max_price(400000, 200000, 300000) == 300000
    # Price within range
    assert enforce_min_max_price(250000, 200000, 300000) == 250000
    # No min
    assert enforce_min_max_price(100000, None, 300000) == 100000
    # No max
    assert enforce_min_max_price(400000, 200000, None) == 400000


def test_get_location_rules():
    config = {
        "locations": {
            "Test Location": {
                "min_price": 100000,
                "max_price": 300000,
                "margin_of_safety": 0.5,
                "dynamic_pricing_tiers": [
                    {"min_occupancy": 0.0, "max_occupancy": 0.5, "multiplier": 0.8},
                    {"min_occupancy": 0.5, "max_occupancy": 1.0, "multiplier": 1.2},
                ],
                "target_breakeven_occupancy": 0.6,
            }
        },
        "margin_of_safety": 0.4,
        "dynamic_pricing_tiers": [],
    }
    rules = get_location_rules("Test Location", config)
    assert rules["min_price"] == 100000
    assert rules["max_price"] == 300000
    assert rules["margin_of_safety"] == 0.5
    assert rules["target_breakeven_occupancy"] == 0.6
    assert isinstance(rules["dynamic_pricing_tiers"], list)

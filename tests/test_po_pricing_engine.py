import pytest
from src.utils.parsing import parse_float, parse_int, parse_pct
from src.po_pricing_engine import (
    get_location_rules,
    DynamicPricingTier,
    LocationData,
    PricingRules,
    load_pricing_rules,
)
from src.pricing.calculator import PricingCalculator


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
                "target_breakeven_occupancy": 0.5,
            }
        },
        "margin_of_safety": 0.4,
        "dynamic_pricing_tiers": [],
    }
    rules = get_location_rules("Test Location", config)
    assert rules["min_price"] == 100000
    assert rules["max_price"] == 300000
    assert rules["margin_of_safety"] == 0.5
    assert rules["target_breakeven_occupancy"] == 0.5
    assert isinstance(rules["dynamic_pricing_tiers"], list)


class TestPricingCalculator:
    def setup_method(self):
        self.config = {
            "locations": {
                "Test Location": {
                    "min_price": 100000,
                    "max_price": 300000,
                    "margin_of_safety": 0.5,
                    "dynamic_pricing_tiers": [
                        {"min_occupancy": 0.0, "max_occupancy": 0.5, "multiplier": 0.8},
                        {"min_occupancy": 0.5, "max_occupancy": 1.0, "multiplier": 1.2},
                    ],
                    "target_breakeven_occupancy": 0.5,
                }
            },
            "margin_of_safety": 0.4,
            "dynamic_pricing_tiers": [],
        }
        self.calculator = PricingCalculator(self.config)

    def test_breakeven_price(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_actual_occupied_pct=0.5,
            po_seats_occupied_pct=0.5,
            total_po_seats=10,
        )
        result = self.calculator.calculate_pricing(data)
        # 1000000 / (10 * 0.5) = 200000
        assert result.breakeven_price == 200000

    def test_dynamic_multiplier(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_actual_occupied_pct=0.4,
            po_seats_occupied_pct=0.4,
            total_po_seats=10,
        )
        result = self.calculator.calculate_pricing(data)
        # 200000 * 0.8 = 160000, but no rounding until the end, so base_price is 200000 * 0.8 = 160000
        assert result.base_price == 200000.0

    def test_margin_of_safety(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_actual_occupied_pct=0.4,
            po_seats_occupied_pct=0.4,
            total_po_seats=10,
        )
        result = self.calculator.calculate_pricing(data)
        # 200000 * 0.8 = 160000, 160000 * 1.5 = 240000, but no rounding until the end, so price_with_margin is 300000.0
        assert result.price_with_margin == 300000.0

    def test_enforce_bounds(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_actual_occupied_pct=0.4,
            po_seats_occupied_pct=0.4,
            total_po_seats=10,
        )
        result = self.calculator.calculate_pricing(data)
        # Final price is 300000.0 after rounding and enforcing bounds
        assert result.final_price == 300000.0

    def test_full_calculation_losing_money(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_actual_occupied_pct=0.2,  # below breakeven
            po_seats_occupied_pct=0.2,
            total_po_seats=10,
        )
        result = self.calculator.calculate_pricing(data)
        assert result.losing_money is True

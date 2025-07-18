import pytest
from src.utils.parsing import parse_float, parse_int, parse_pct
from src.config.rules import load_pricing_rules
from src.pricing.models import (
    DynamicPricingTier,
    LocationData,
)
from src.pricing.rules import PricingRules
from src.pricing.rules import build_rules
from src.pricing.calculator import PricingCalculator


def test_build_rules():
    config = {
        "locations": {
            "Test Location": {
                "min_price": 100000,
                "max_price": 300000,
                "margin_of_safety": 0.5,
                "target_breakeven_occupancy": 50.0,
            }
        },
        "margin_of_safety": 0.4,
        "dynamic_pricing_tiers": [
            {"min_occupancy": 0.0, "max_occupancy": 50.0, "multiplier": 0.8},
            {"min_occupancy": 50.0, "max_occupancy": 100.0, "multiplier": 1.2},
        ],
    }
    rules = build_rules("Test Location", config)
    assert rules.min_price == 100000
    assert rules.max_price == 300000
    assert rules.margin_of_safety == 0.5
    assert len(rules.dynamic_pricing_tiers) == 2


class TestPricingCalculator:
    def setup_method(self):
        self.config = {
            "locations": {
                "Test Location": {
                    "min_price": 100000,
                    "max_price": 300000,
                    "margin_of_safety": 0.5,
                    "target_breakeven_occupancy": 50.0,
                }
            },
            "margin_of_safety": 0.4,
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 50.0, "multiplier": 0.8},
                {"min_occupancy": 50.0, "max_occupancy": 100.0, "multiplier": 1.2},
            ],
        }
        self.calculator = PricingCalculator(self.config)

    def test_breakeven_price(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=50.0,
            po_seats_occupied_pct=50.0,
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
            po_seats_occupied_actual_pct=40.0,
            po_seats_occupied_pct=40.0,
            total_po_seats=10,
        )
        result = self.calculator.calculate_pricing(data)
        # 40% occupancy falls in the 0-50% tier with 0.8 multiplier
        # Breakeven = 1000000 / (10 * 0.5) = 200000
        # Base price = 200000 * 0.8 = 160000
        assert result.base_price == 160000.0

    def test_margin_of_safety(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=40.0,
            po_seats_occupied_pct=40.0,
            total_po_seats=10,
        )
        result = self.calculator.calculate_pricing(data)
        # 40% occupancy falls in the 0-50% tier with 0.8 multiplier
        # Breakeven = 1000000 / (10 * 0.5) = 200000
        # Base price = 200000 * 0.8 = 160000
        # Price with margin = 160000 * 1.5 = 240000
        assert result.price_with_margin == 240000.0

    def test_enforce_bounds(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=40.0,
            po_seats_occupied_pct=40.0,
            total_po_seats=10,
        )
        result = self.calculator.calculate_pricing(data)
        # 40% occupancy falls in the 0-50% tier with 0.8 multiplier
        # Breakeven = 1000000 / (10 * 0.5) = 200000
        # Base price = 200000 * 0.8 = 160000
        # Price with margin = 160000 * 1.5 = 240000
        # Final price after rounding to nearest 50000 = 250000
        assert result.final_price == 250000.0

    def test_full_calculation_losing_money(self):
        data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=20.0,  # below breakeven
            po_seats_occupied_pct=20.0,
            total_po_seats=10,
            sold_price_per_po_seat_actual=500000,  # Add actual sold price for breakeven calculation
        )
        result = self.calculator.calculate_pricing(data)
        # With sold_price_per_po_seat_actual=500000, actual_breakeven = 1000000/(500000*10)*100 = 20%
        # Current occupancy is 20%, so it should be at breakeven, not losing money
        # Let's test with a lower occupancy to ensure losing money
        data2 = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=15.0,  # below actual breakeven
            po_seats_occupied_pct=15.0,
            total_po_seats=10,
            sold_price_per_po_seat_actual=500000,
        )
        result2 = self.calculator.calculate_pricing(data2)
        assert result2.losing_money is True

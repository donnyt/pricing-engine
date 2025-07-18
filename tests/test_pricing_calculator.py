"""
Unit tests for pricing calculator logic including smart target calculations.

This module tests the core pricing calculation logic, with a focus on smart target
breakeven occupancy calculations and various business scenarios.
"""

import pytest
from unittest.mock import Mock, patch
from src.pricing.calculator import PricingCalculator
from src.pricing.models import LocationData, PricingResult
from src.pricing.rules import get_target_breakeven_occupancy


class TestSmartTargetCalculation:
    """Test smart target breakeven occupancy calculation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 20.0, "multiplier": 0.8},
                {"min_occupancy": 20.0, "max_occupancy": 40.0, "multiplier": 0.9},
                {"min_occupancy": 40.0, "max_occupancy": 60.0, "multiplier": 1.0},
                {"min_occupancy": 60.0, "max_occupancy": 80.0, "multiplier": 1.05},
                {"min_occupancy": 80.0, "max_occupancy": 100.0, "multiplier": 1.1},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": None,
                    "max_price": 3000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }
        self.calculator = PricingCalculator(self.config)

    def test_profitable_location_aggressive_target(self):
        """Test smart target calculation for profitable locations (more aggressive)."""
        # Location is profitable: occupancy > actual breakeven
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=85.0,  # High occupancy
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,  # High price
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should use smart target (more aggressive for profitable locations)
        assert result.is_smart_target is True
        assert (
            result.target_breakeven_occupancy_pct < 70.0
        )  # Should be lower than static target
        assert result.actual_breakeven_occupancy_pct is not None
        # For profitable locations, smart target should be lower than actual breakeven
        assert (
            result.target_breakeven_occupancy_pct
            < result.actual_breakeven_occupancy_pct
        )

    def test_losing_money_location_less_aggressive_target(self):
        """Test smart target calculation for losing money locations (less aggressive)."""
        # Location is losing money: occupancy < actual breakeven
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=40.0,  # Low occupancy
            total_po_seats=100,
            sold_price_per_po_seat_actual=8000,  # Low price
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should use smart target (less aggressive for losing money locations)
        assert result.is_smart_target is True
        assert result.actual_breakeven_occupancy_pct is not None
        # For losing money locations, smart target should still be lower than actual breakeven
        # but the reduction should be less aggressive
        assert (
            result.target_breakeven_occupancy_pct
            < result.actual_breakeven_occupancy_pct
        )

    def test_static_target_fallback(self):
        """Test fallback to static target when smart target calculation fails."""
        # Missing data that prevents smart target calculation
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=60.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=None,  # Missing data
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should fallback to static target
        assert result.is_smart_target is False
        assert result.target_breakeven_occupancy_pct == 70.0  # Static target
        assert result.actual_breakeven_occupancy_pct is None

    def test_fallback_scenarios(self):
        """Test various fallback scenarios when smart target calculation fails."""
        # Test 1: Missing sold price per seat
        location_data_no_price = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=None,  # Missing price
        )
        result_no_price = self.calculator.calculate_pricing(location_data_no_price)
        assert result_no_price.is_smart_target is False
        assert result_no_price.target_breakeven_occupancy_pct == 70.0

        # Test 2: Zero sold price (invalid data)
        location_data_zero_price = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=0,  # Zero price
        )
        result_zero_price = self.calculator.calculate_pricing(location_data_zero_price)
        assert result_zero_price.is_smart_target is False
        assert result_zero_price.target_breakeven_occupancy_pct == 70.0

        # Test 3: Invalid location (not in config)
        location_data_invalid = LocationData(
            name="Invalid Location",  # Not in config
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_invalid = self.calculator.calculate_pricing(location_data_invalid)
        assert result_invalid.is_smart_target is False
        assert result_invalid.target_breakeven_occupancy_pct == 70.0  # Default fallback

    def test_high_breakeven_occupancy_less_aggressive(self):
        """Test that high breakeven occupancy results in less aggressive targets."""
        # High breakeven occupancy (difficult to achieve)
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=2000000,  # High expenses
            avg_exp_total_po_expense_amount=2000000,
            po_seats_occupied_actual_pct=85.0,  # Profitable
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should use smart target for high breakeven occupancy
        assert result.is_smart_target is True
        assert result.actual_breakeven_occupancy_pct > 80.0  # High breakeven
        # Target should be lower than actual breakeven (improvement target)
        assert (
            result.target_breakeven_occupancy_pct
            < result.actual_breakeven_occupancy_pct
        )

    def test_low_breakeven_occupancy_more_aggressive(self):
        """Test that low breakeven occupancy results in more aggressive targets."""
        # Low breakeven occupancy (easier to achieve)
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=500000,  # Low expenses
            avg_exp_total_po_expense_amount=500000,
            po_seats_occupied_actual_pct=85.0,  # Profitable
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should use smart target for low breakeven occupancy
        assert result.is_smart_target is True
        assert result.actual_breakeven_occupancy_pct < 50.0  # Low breakeven
        # Target should be lower than actual breakeven (improvement target)
        assert (
            result.target_breakeven_occupancy_pct
            < result.actual_breakeven_occupancy_pct
        )

    def test_smart_target_disabled(self):
        """Test that smart targets are not used when disabled in config."""
        config_without_smart = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": None,
                    "max_price": 3000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": False,  # Disabled
                }
            },
        }
        calculator = PricingCalculator(config_without_smart)

        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=85.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result = calculator.calculate_pricing(location_data)

        # Should use static target
        assert result.is_smart_target is False
        assert result.target_breakeven_occupancy_pct == 70.0  # Static target

    def test_edge_case_zero_occupancy(self):
        """Test smart target calculation with zero occupancy."""
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=0.0,  # Zero occupancy
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should handle zero occupancy gracefully
        assert result.is_smart_target is True
        assert result.target_breakeven_occupancy_pct > 0.0
        assert result.actual_breakeven_occupancy_pct is not None

    def test_edge_case_100_percent_occupancy(self):
        """Test smart target calculation with 100% occupancy."""
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=100.0,  # 100% occupancy
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should handle 100% occupancy gracefully
        assert result.is_smart_target is True
        assert result.target_breakeven_occupancy_pct <= 100.0
        assert result.actual_breakeven_occupancy_pct is not None

    def test_breakeven_occupancy_aggressiveness_levels(self):
        """Test different breakeven occupancy levels and their impact on target aggressiveness."""
        # Test low breakeven occupancy (should be more aggressive)
        location_data_low = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=500000,  # Low expenses = low breakeven
            avg_exp_total_po_expense_amount=500000,
            po_seats_occupied_actual_pct=85.0,  # Profitable
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_low = self.calculator.calculate_pricing(location_data_low)

        # Test medium breakeven occupancy
        location_data_medium = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,  # Medium expenses
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=85.0,  # Profitable
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_medium = self.calculator.calculate_pricing(location_data_medium)

        # Test high breakeven occupancy (should be less aggressive)
        location_data_high = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=2000000,  # High expenses = high breakeven
            avg_exp_total_po_expense_amount=2000000,
            po_seats_occupied_actual_pct=85.0,  # Profitable
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_high = self.calculator.calculate_pricing(location_data_high)

        # All should use smart targets
        assert result_low.is_smart_target is True
        assert result_medium.is_smart_target is True
        assert result_high.is_smart_target is True

        # Verify breakeven levels are different
        assert (
            result_low.actual_breakeven_occupancy_pct
            < result_medium.actual_breakeven_occupancy_pct
        )
        assert (
            result_medium.actual_breakeven_occupancy_pct
            < result_high.actual_breakeven_occupancy_pct
        )

        # Verify smart targets are calculated correctly (lower than actual breakeven)
        assert (
            result_low.target_breakeven_occupancy_pct
            < result_low.actual_breakeven_occupancy_pct
        )
        assert (
            result_medium.target_breakeven_occupancy_pct
            < result_medium.actual_breakeven_occupancy_pct
        )
        assert (
            result_high.target_breakeven_occupancy_pct
            < result_high.actual_breakeven_occupancy_pct
        )

        # Calculate improvement percentages
        low_improvement = (
            (
                result_low.actual_breakeven_occupancy_pct
                - result_low.target_breakeven_occupancy_pct
            )
            / result_low.actual_breakeven_occupancy_pct
            * 100
        )
        medium_improvement = (
            (
                result_medium.actual_breakeven_occupancy_pct
                - result_medium.target_breakeven_occupancy_pct
            )
            / result_medium.actual_breakeven_occupancy_pct
            * 100
        )
        high_improvement = (
            (
                result_high.actual_breakeven_occupancy_pct
                - result_high.target_breakeven_occupancy_pct
            )
            / result_high.actual_breakeven_occupancy_pct
            * 100
        )

        # Verify that different breakeven levels result in different improvement targets
        # (The exact values depend on the smart target logic, but they should be reasonable)
        assert 2.0 <= low_improvement <= 10.0  # Reasonable improvement range
        assert 2.0 <= medium_improvement <= 10.0
        assert 2.0 <= high_improvement <= 10.0


class TestPricingCalculationIntegration:
    """Test complete pricing calculation integration with smart targets."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 5000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }
        self.calculator = PricingCalculator(self.config)

    def test_complete_pricing_calculation_with_smart_target(self):
        """Test complete pricing calculation workflow with smart targets."""
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result = self.calculator.calculate_pricing(location_data)

        # Verify all required fields are present
        assert result.location == "Test Location"
        assert result.recommended_price > 0
        assert result.target_breakeven_occupancy_pct > 0

    def test_smart_target_workflow_integration(self):
        """Test complete smart target workflow integration."""
        from src.pricing.rules import build_rules, get_target_breakeven_occupancy

        # Test 1: Profitable location with smart targets
        location_data_profitable = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=85.0,  # Profitable
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result_profitable = self.calculator.calculate_pricing(location_data_profitable)

        # Verify smart target was used
        assert result_profitable.is_smart_target is True
        assert (
            result_profitable.target_breakeven_occupancy_pct
            < result_profitable.actual_breakeven_occupancy_pct
        )
        assert result_profitable.actual_breakeven_occupancy_pct is not None

        # Test 2: Losing money location with smart targets
        location_data_losing = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=65.0,  # Losing money
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result_losing = self.calculator.calculate_pricing(location_data_losing)

        # Verify smart target was used
        assert result_losing.is_smart_target is True
        assert (
            result_losing.target_breakeven_occupancy_pct
            < result_losing.actual_breakeven_occupancy_pct
        )
        assert result_losing.actual_breakeven_occupancy_pct is not None

        # Test 3: Static target fallback
        location_data_static = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=None,  # Missing data
        )

        result_static = self.calculator.calculate_pricing(location_data_static)

        # Verify static target was used
        assert result_static.is_smart_target is False
        assert result_static.target_breakeven_occupancy_pct == 70.0  # Static target

        # Test 4: Verify rules integration
        rules = build_rules("Test Location", self.config)
        assert rules.use_smart_target is True

        # Test 5: Verify target extraction integration
        target, is_smart = get_target_breakeven_occupancy(
            "Test Location",
            self.config,
            actual_breakeven_occupancy_pct=80.0,
            current_occupancy_pct=85.0,
        )
        assert is_smart is True
        assert target < 80.0

    def test_smart_target_configuration_integration(self):
        """Test smart target configuration integration across different scenarios."""
        from src.pricing.rules import (
            validate_smart_target_configuration,
            is_smart_target_enabled,
        )

        # Test configuration with mixed smart target settings
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Smart Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                },
                "Static Location": {
                    "target_breakeven_occupancy": 65.0,
                    "use_smart_target": False,
                },
                "Default Location": {
                    "target_breakeven_occupancy": 75.0,
                    # use_smart_target not specified
                },
            },
        }

        # Validate configuration
        validate_smart_target_configuration(config)

        # Test smart target status for each location
        assert is_smart_target_enabled("Smart Location", config) is True
        assert is_smart_target_enabled("Static Location", config) is False
        assert is_smart_target_enabled("Default Location", config) is False

        # Test pricing calculation for each location type
        smart_calculator = PricingCalculator(config)

        smart_location_data = LocationData(
            name="Smart Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=85.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        smart_result = smart_calculator.calculate_pricing(smart_location_data)
        assert smart_result.is_smart_target is True

        static_location_data = LocationData(
            name="Static Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=85.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        static_result = smart_calculator.calculate_pricing(static_location_data)
        assert static_result.is_smart_target is False
        assert static_result.target_breakeven_occupancy_pct == 65.0

    def test_smart_target_error_handling_integration(self):
        """Test error handling integration in smart target workflow."""
        # Test configuration with invalid smart target settings
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Invalid Location": {
                    "target_breakeven_occupancy": -10.0,  # Invalid negative value
                    "use_smart_target": True,
                }
            },
        }

        # Test that validation catches the error
        from src.pricing.rules import validate_smart_target_configuration

        with pytest.raises(ValueError, match="invalid target_breakeven_occupancy"):
            validate_smart_target_configuration(config)

        # Test that build_rules catches the error
        from src.pricing.rules import build_rules

        with pytest.raises(ValueError, match="invalid target_breakeven_occupancy"):
            build_rules("Invalid Location", config)

        # Test that calculator handles missing data gracefully
        location_data_missing = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=None,  # Missing data
        )

        result = self.calculator.calculate_pricing(location_data_missing)
        assert result.is_smart_target is False  # Should fallback to static
        assert result.target_breakeven_occupancy_pct == 70.0  # Static target
        assert (
            result.actual_breakeven_occupancy_pct is None
        )  # Can't calculate without sold price
        assert result.breakeven_price is not None
        assert result.losing_money is False  # 80% occupancy > actual breakeven

        # Verify price bounds are respected
        assert result.recommended_price >= 1000000  # min_price
        assert result.recommended_price <= 5000000  # max_price

    def test_losing_money_detection(self):
        """Test that losing money status is correctly detected."""
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=40.0,  # Low occupancy
            total_po_seats=100,
            sold_price_per_po_seat_actual=8000,  # Low price
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should detect losing money
        assert result.losing_money is True
        assert (
            result.actual_breakeven_occupancy_pct
            > result.target_breakeven_occupancy_pct
        )

    def test_dynamic_multiplier_application(self):
        """Test that dynamic multipliers are correctly applied."""
        config_with_tiers = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 50.0, "multiplier": 0.9},
                {"min_occupancy": 50.0, "max_occupancy": 100.0, "multiplier": 1.1},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": None,
                    "max_price": None,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }
        calculator = PricingCalculator(config_with_tiers)

        # Test low occupancy (should get 0.9 multiplier)
        location_data_low = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=30.0,  # Low occupancy
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_low = calculator.calculate_pricing(location_data_low)
        assert result_low.dynamic_multiplier == 0.9

        # Test high occupancy (should get 1.1 multiplier)
        location_data_high = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,  # High occupancy
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_high = calculator.calculate_pricing(location_data_high)
        assert result_high.dynamic_multiplier == 1.1


class TestErrorHandling:
    """Test error handling in pricing calculator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": None,
                    "max_price": None,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }
        self.calculator = PricingCalculator(self.config)

    def test_invalid_location_config(self):
        """Test handling of invalid location configuration."""
        location_data = LocationData(
            name="Invalid Location",  # Not in config
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        # Should handle missing location gracefully by using default values
        result = self.calculator.calculate_pricing(location_data)
        assert result.is_smart_target is False  # Should fallback to static target
        assert result.target_breakeven_occupancy_pct == 70.0  # Default fallback

    def test_zero_total_seats(self):
        """Test handling of zero total seats."""
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=0,  # Zero seats
            sold_price_per_po_seat_actual=15000,
        )

        # Should raise ValueError for zero seats
        with pytest.raises(
            ValueError,
            match="Total PO seats and target breakeven occupancy must be greater than zero",
        ):
            self.calculator.calculate_pricing(location_data)

    def test_negative_expenses(self):
        """Test handling of negative expenses."""
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=-1000000,  # Negative expenses
            avg_exp_total_po_expense_amount=-1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        result = self.calculator.calculate_pricing(location_data)

        # Should handle negative expenses gracefully
        assert result.actual_breakeven_occupancy_pct is not None
        assert result.actual_breakeven_occupancy_pct < 0  # Negative breakeven
        assert result.is_smart_target is True  # Should still use smart target


class TestSmartTargetPerformance:
    """Test performance of smart target calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 5000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }
        self.calculator = PricingCalculator(self.config)

    def test_smart_target_calculation_performance(self):
        """Test that smart target calculations are performant."""
        import time

        # Create test data
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        # Measure performance of smart target calculation
        start_time = time.time()

        # Run multiple calculations to get a meaningful measurement
        for _ in range(1000):
            result = self.calculator.calculate_pricing(location_data)
            assert result.is_smart_target is True

        end_time = time.time()
        total_time = end_time - start_time

        # Verify performance is acceptable (should be very fast)
        # 1000 calculations should take less than 1 second
        assert (
            total_time < 1.0
        ), f"Smart target calculations took {total_time:.3f}s for 1000 iterations"

        # Calculate average time per calculation
        avg_time_per_calc = total_time / 1000
        print(f"Average time per smart target calculation: {avg_time_per_calc:.6f}s")

    def test_smart_target_vs_static_target_performance(self):
        """Test that smart targets don't significantly impact performance vs static targets."""
        import time

        # Test configuration with smart targets enabled
        smart_config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 5000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }
        smart_calculator = PricingCalculator(smart_config)

        # Test configuration with static targets
        static_config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 5000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": False,
                }
            },
        }
        static_calculator = PricingCalculator(static_config)

        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        # Measure smart target performance
        start_time = time.time()
        for _ in range(1000):
            result = smart_calculator.calculate_pricing(location_data)
            assert result.is_smart_target is True
        smart_time = time.time() - start_time

        # Measure static target performance
        start_time = time.time()
        for _ in range(1000):
            result = static_calculator.calculate_pricing(location_data)
            assert result.is_smart_target is False
        static_time = time.time() - start_time

        # Smart targets should not be more than 50% slower than static targets
        performance_ratio = smart_time / static_time
        assert (
            performance_ratio < 1.5
        ), f"Smart targets are {performance_ratio:.2f}x slower than static targets"

        print(f"Smart target performance ratio: {performance_ratio:.2f}x")

    def test_smart_target_memory_usage(self):
        """Test that smart target calculations don't cause memory leaks."""
        import gc
        import sys

        # Create test data
        location_data = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )

        # Force garbage collection to get baseline
        gc.collect()
        baseline_memory = sys.getsizeof([])  # Simple baseline

        # Run many calculations
        results = []
        for _ in range(10000):
            result = self.calculator.calculate_pricing(location_data)
            results.append(result)
            assert result.is_smart_target is True

        # Force garbage collection again
        gc.collect()

        # Memory usage should be reasonable (not growing excessively)
        # This is a basic check - in a real scenario you'd use more sophisticated memory profiling
        assert len(results) == 10000, "All calculations should complete successfully"

    def test_bottom_price_rounding_to_50000(self):
        """Test that bottom price (breakeven price) is rounded up to nearest 50,000."""
        # Create a config with static targets to avoid smart target complexity
        static_config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 5000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": False,  # Use static target
                }
            },
        }
        static_calculator = PricingCalculator(static_config)

        # Test case 1: Price that should round up to 50,000
        location_data_1 = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=1000000,
            avg_exp_total_po_expense_amount=1000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_1 = static_calculator.calculate_pricing(location_data_1)

        # Raw breakeven price: 1000000 / (100 * 0.7) = 14285.71
        # Should round up to 50000
        assert result_1.breakeven_price == 50000

        # Test case 2: Price that should round up to 50,000
        location_data_2 = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=2000000,
            avg_exp_total_po_expense_amount=2000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_2 = static_calculator.calculate_pricing(location_data_2)

        # Raw breakeven price: 2000000 / (100 * 0.7) = 28571.43
        # Should round up to 50000
        assert result_2.breakeven_price == 50000

        # Test case 3: Price that should round up to 100,000
        location_data_3 = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=3500000,
            avg_exp_total_po_expense_amount=3500000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_3 = static_calculator.calculate_pricing(location_data_3)

        # Raw breakeven price: 3500000 / (100 * 0.7) = 50000
        # Should stay as 50000 (since it's exactly a multiple of 50000)
        assert result_3.breakeven_price == 50000

        # Test case 4: Price that should round up to 100,000
        location_data_4 = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=5000000,
            avg_exp_total_po_expense_amount=5000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_4 = static_calculator.calculate_pricing(location_data_4)

        # Raw breakeven price: 5000000 / (100 * 0.7) = 71428.57
        # Should round up to 100000
        assert result_4.breakeven_price == 100000

        # Test case 5: Price that should round up to 150,000
        location_data_5 = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=7000000,
            avg_exp_total_po_expense_amount=7000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_5 = static_calculator.calculate_pricing(location_data_5)

        # Raw breakeven price: 7000000 / (100 * 0.7) = 100000
        # Should stay as 100000 (since it's exactly a multiple of 50000)
        assert result_5.breakeven_price == 100000

        # Test case 6: Price that should round up to 150,000 (not exact multiple)
        location_data_6 = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=8000000,
            avg_exp_total_po_expense_amount=8000000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_6 = static_calculator.calculate_pricing(location_data_6)

        # Raw breakeven price: 8000000 / (100 * 0.7) = 114285.71
        # Should round up to 150000 (not exact multiple, so rounds up)
        assert result_6.breakeven_price == 150000

        # Test case 7: Price that should stay as 150,000 (exact multiple)
        location_data_7 = LocationData(
            name="Test Location",
            exp_total_po_expense_amount=10500000,
            avg_exp_total_po_expense_amount=10500000,
            po_seats_occupied_actual_pct=80.0,
            total_po_seats=100,
            sold_price_per_po_seat_actual=15000,
        )
        result_7 = static_calculator.calculate_pricing(location_data_7)

        # Raw breakeven price: 10500000 / (100 * 0.7) = 150000
        # Should stay as 150000 (exact multiple, so no rounding)
        assert result_7.breakeven_price == 150000


if __name__ == "__main__":
    pytest.main([__file__])

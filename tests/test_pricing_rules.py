"""
Unit tests for pricing rules configuration parsing and validation.

This module tests the configuration parsing logic, with a focus on smart target
settings validation and error handling.
"""

import pytest
from src.pricing.rules import (
    build_rules,
    get_target_breakeven_occupancy,
    is_smart_target_enabled,
    validate_smart_target_configuration,
)


class TestConfigurationParsing:
    """Test configuration parsing and validation."""

    def test_build_rules_with_smart_targets_enabled(self):
        """Test building rules with smart targets enabled."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 3000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }

        rules = build_rules("Test Location", config)

        assert rules.min_price == 1000000
        assert rules.max_price == 3000000
        assert rules.margin_of_safety == 0.5
        assert rules.use_smart_target is True
        assert len(rules.dynamic_pricing_tiers) == 1

    def test_build_rules_with_smart_targets_disabled(self):
        """Test building rules with smart targets disabled."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 3000000,
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": False,
                }
            },
        }

        rules = build_rules("Test Location", config)

        assert rules.use_smart_target is False

    def test_build_rules_without_smart_target_setting(self):
        """Test building rules when use_smart_target is not specified."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 3000000,
                    "target_breakeven_occupancy": 70.0,
                    # use_smart_target not specified
                }
            },
        }

        rules = build_rules("Test Location", config)

        assert rules.use_smart_target is False  # Should default to False

    def test_build_rules_with_invalid_target_breakeven_occupancy(self):
        """Test building rules with invalid target breakeven occupancy."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 3000000,
                    "target_breakeven_occupancy": -10.0,  # Invalid negative value
                    "use_smart_target": True,
                }
            },
        }

        with pytest.raises(ValueError, match="invalid target_breakeven_occupancy"):
            build_rules("Test Location", config)

    def test_build_rules_with_zero_target_breakeven_occupancy(self):
        """Test building rules with zero target breakeven occupancy."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 3000000,
                    "target_breakeven_occupancy": 0.0,  # Invalid zero value
                    "use_smart_target": True,
                }
            },
        }

        with pytest.raises(ValueError, match="invalid target_breakeven_occupancy"):
            build_rules("Test Location", config)

    def test_build_rules_with_string_target_breakeven_occupancy(self):
        """Test building rules with string target breakeven occupancy."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "min_price": 1000000,
                    "max_price": 3000000,
                    "target_breakeven_occupancy": "70.0",  # Invalid string value
                    "use_smart_target": True,
                }
            },
        }

        with pytest.raises(ValueError, match="invalid target_breakeven_occupancy"):
            build_rules("Test Location", config)


class TestSmartTargetConfiguration:
    """Test smart target configuration validation."""

    def test_validate_smart_target_configuration_valid(self):
        """Test validation of valid smart target configuration."""
        config = {
            "locations": {
                "Location 1": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                },
                "Location 2": {
                    "target_breakeven_occupancy": 60.0,
                    "use_smart_target": False,
                },
                "Location 3": {
                    "use_smart_target": True,
                    # No target_breakeven_occupancy specified
                },
            }
        }

        # Should not raise any exceptions
        validate_smart_target_configuration(config)

    def test_validate_smart_target_configuration_invalid(self):
        """Test validation of invalid smart target configuration."""
        config = {
            "locations": {
                "Location 1": {
                    "target_breakeven_occupancy": -10.0,  # Invalid negative value
                    "use_smart_target": True,
                }
            }
        }

        with pytest.raises(ValueError, match="invalid target_breakeven_occupancy"):
            validate_smart_target_configuration(config)

    def test_is_smart_target_enabled(self):
        """Test checking if smart targets are enabled for a location."""
        config = {
            "locations": {
                "Smart Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                },
                "Static Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": False,
                },
                "Default Location": {
                    "target_breakeven_occupancy": 70.0,
                    # use_smart_target not specified
                },
            }
        }

        assert is_smart_target_enabled("Smart Location", config) is True
        assert is_smart_target_enabled("Static Location", config) is False
        assert is_smart_target_enabled("Default Location", config) is False
        assert is_smart_target_enabled("Non-existent Location", config) is False


class TestTargetBreakevenOccupancyExtraction:
    """Test target breakeven occupancy extraction logic."""

    def test_get_target_breakeven_occupancy_static_target(self):
        """Test getting static target breakeven occupancy."""
        config = {
            "locations": {
                "Test Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": False,
                }
            }
        }

        target, is_smart = get_target_breakeven_occupancy("Test Location", config)

        assert target == 70.0
        assert is_smart is False

    def test_get_target_breakeven_occupancy_smart_target(self):
        """Test getting smart target breakeven occupancy."""
        config = {
            "locations": {
                "Test Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            }
        }

        # With valid data for smart target calculation
        target, is_smart = get_target_breakeven_occupancy(
            "Test Location",
            config,
            actual_breakeven_occupancy_pct=80.0,
            current_occupancy_pct=85.0,
        )

        assert target < 80.0  # Smart target should be lower than actual breakeven
        assert is_smart is True

    def test_get_target_breakeven_occupancy_smart_target_missing_data(self):
        """Test getting smart target when required data is missing."""
        config = {
            "locations": {
                "Test Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            }
        }

        # Missing data should fallback to static target
        target, is_smart = get_target_breakeven_occupancy(
            "Test Location",
            config,
            actual_breakeven_occupancy_pct=None,
            current_occupancy_pct=85.0,
        )

        assert target == 70.0  # Should fallback to static target
        assert is_smart is False

    def test_get_target_breakeven_occupancy_location_not_in_config(self):
        """Test getting target breakeven occupancy for location not in config."""
        config = {
            "locations": {
                "Other Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            }
        }

        target, is_smart = get_target_breakeven_occupancy("Test Location", config)

        assert target == 70.0  # Should use default fallback
        assert is_smart is False

    def test_get_target_breakeven_occupancy_profitable_location(self):
        """Test smart target calculation for profitable location."""
        config = {
            "locations": {
                "Test Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            }
        }

        # Profitable location: occupancy > actual breakeven
        target, is_smart = get_target_breakeven_occupancy(
            "Test Location",
            config,
            actual_breakeven_occupancy_pct=75.0,
            current_occupancy_pct=85.0,
        )

        assert is_smart is True
        assert target < 75.0  # Should be lower than actual breakeven
        assert target > 0.0  # Should be positive

    def test_get_target_breakeven_occupancy_losing_money_location(self):
        """Test smart target calculation for losing money location."""
        config = {
            "locations": {
                "Test Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            }
        }

        # Losing money location: occupancy < actual breakeven
        target, is_smart = get_target_breakeven_occupancy(
            "Test Location",
            config,
            actual_breakeven_occupancy_pct=85.0,
            current_occupancy_pct=75.0,
        )

        assert is_smart is True
        assert target < 85.0  # Should be lower than actual breakeven
        assert target > 0.0  # Should be positive


class TestConfigurationEdgeCases:
    """Test configuration edge cases and error handling."""

    def test_empty_config(self):
        """Test handling of empty configuration."""
        config = {}

        rules = build_rules("Test Location", config)

        assert rules.min_price is None
        assert rules.max_price is None
        assert rules.margin_of_safety == 0.5  # Should use default
        assert rules.use_smart_target is False
        assert len(rules.dynamic_pricing_tiers) == 0

    def test_config_without_locations(self):
        """Test handling of configuration without locations section."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
        }

        rules = build_rules("Test Location", config)

        assert rules.min_price is None
        assert rules.max_price is None
        assert rules.margin_of_safety == 0.5
        assert rules.use_smart_target is False

    def test_config_with_empty_locations(self):
        """Test handling of configuration with empty locations section."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "margin_of_safety": 0.5,
            "locations": {},
        }

        rules = build_rules("Test Location", config)

        assert rules.min_price is None
        assert rules.max_price is None
        assert rules.margin_of_safety == 0.5
        assert rules.use_smart_target is False

    def test_config_with_missing_dynamic_pricing_tiers(self):
        """Test handling of configuration without dynamic pricing tiers."""
        config = {
            "margin_of_safety": 0.5,
            "locations": {
                "Test Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }

        rules = build_rules("Test Location", config)

        assert rules.use_smart_target is True
        assert len(rules.dynamic_pricing_tiers) == 0

    def test_config_with_missing_margin_of_safety(self):
        """Test handling of configuration without margin of safety."""
        config = {
            "dynamic_pricing_tiers": [
                {"min_occupancy": 0.0, "max_occupancy": 100.0, "multiplier": 1.0},
            ],
            "locations": {
                "Test Location": {
                    "target_breakeven_occupancy": 70.0,
                    "use_smart_target": True,
                }
            },
        }

        rules = build_rules("Test Location", config)

        assert rules.use_smart_target is True
        # Should use default margin of safety (0.5)
        assert rules.margin_of_safety == 0.5


if __name__ == "__main__":
    pytest.main([__file__])

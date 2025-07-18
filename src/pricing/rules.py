# src/pricing/rules.py
from typing import Dict, Any
from .models import PricingRules, DynamicPricingTier


def build_rules(location: str, cfg: Dict[str, Any]) -> PricingRules:
    """Translate raw YAML config into a strongly-typed PricingRules object."""
    loc_cfg = cfg.get("locations", {}).get(location, {})

    # Validate smart target configuration
    use_smart_target = loc_cfg.get("use_smart_target")
    if use_smart_target is None:
        raise ValueError(
            f"Location '{location}' must have 'use_smart_target' configured"
        )
    static_target = loc_cfg.get("target_breakeven_occupancy")

    # Only validate if smart targets are enabled AND we have a static target to validate
    if use_smart_target and static_target is not None:
        if not isinstance(static_target, (int, float)) or static_target <= 0:
            raise ValueError(
                f"Location '{location}' has invalid target_breakeven_occupancy "
                f"value: {static_target}. Must be a positive number."
            )

    return PricingRules(
        min_price=loc_cfg.get("min_price"),
        max_price=loc_cfg.get("max_price"),
        margin_of_safety=loc_cfg.get(
            "margin_of_safety", cfg.get("margin_of_safety", 0.5)
        ),
        dynamic_pricing_tiers=[
            DynamicPricingTier(**tier) for tier in cfg.get("dynamic_pricing_tiers", [])
        ],
        use_smart_target=use_smart_target,
    )


def get_target_breakeven_occupancy(
    location: str,
    cfg: Dict[str, Any],
    actual_breakeven_occupancy_pct: float = None,
    current_occupancy_pct: float = None,
) -> tuple[float, bool]:
    """
    Extract target breakeven occupancy for a location from config.

    Args:
        location: Name of the location
        cfg: Configuration dictionary
        actual_breakeven_occupancy_pct: Current actual breakeven occupancy percentage (for smart targets)
        current_occupancy_pct: Current occupancy percentage (for smart targets)

    Returns:
        tuple[float, bool]: (target_breakeven_occupancy, is_smart_target)
    """
    loc_cfg = cfg.get("locations", {}).get(location, {})
    use_smart_target = loc_cfg.get("use_smart_target")
    if use_smart_target is None:
        raise ValueError(
            f"Location '{location}' must have 'use_smart_target' configured"
        )

    # If smart targets are enabled and we have the required data, calculate smart target
    if (
        use_smart_target
        and actual_breakeven_occupancy_pct is not None
        and current_occupancy_pct is not None
    ):
        # Calculate smart target directly to avoid circular imports
        try:
            # Calculate profitability status
            is_profitable = current_occupancy_pct >= actual_breakeven_occupancy_pct

            if is_profitable:
                # Profitable locations - More aggressive targets (3-7% reduction)
                if actual_breakeven_occupancy_pct <= 50:
                    improvement_multiplier = 0.97  # 3% reduction
                elif actual_breakeven_occupancy_pct <= 70:
                    improvement_multiplier = 0.95  # 5% reduction
                else:
                    improvement_multiplier = 0.93  # 7% reduction
            else:
                # Losing money locations - Less aggressive targets (3-10% reduction)
                loss_gap = actual_breakeven_occupancy_pct - current_occupancy_pct

                if loss_gap <= 15:
                    improvement_multiplier = 0.97  # 3% reduction
                elif loss_gap <= 25:
                    improvement_multiplier = 0.94  # 6% reduction
                else:
                    improvement_multiplier = 0.90  # 10% reduction

            smart_target = actual_breakeven_occupancy_pct * improvement_multiplier
            return smart_target, True

        except Exception:
            # Fallback to static target on any error
            pass

    # Fallback to static target
    static_target = loc_cfg.get("target_breakeven_occupancy", 70.0)  # Default fallback
    return static_target, False


def is_smart_target_enabled(location: str, cfg: Dict[str, Any]) -> bool:
    """Check if smart target breakeven occupancy is enabled for a location."""
    loc_cfg = cfg.get("locations", {}).get(location, {})
    use_smart_target = loc_cfg.get("use_smart_target")
    if use_smart_target is None:
        raise ValueError(
            f"Location '{location}' must have 'use_smart_target' configured"
        )
    return use_smart_target


def validate_smart_target_configuration(cfg: Dict[str, Any]) -> None:
    """Validate smart target configuration across all locations."""
    locations = cfg.get("locations", {})

    for location_name, loc_cfg in locations.items():
        use_smart_target = loc_cfg.get("use_smart_target")
        if use_smart_target is None:
            raise ValueError(
                f"Location '{location_name}' must have 'use_smart_target' configured"
            )

        if use_smart_target:
            # Only validate if we have a static target to validate
            target_value = loc_cfg.get("target_breakeven_occupancy")
            if target_value is not None:
                if not isinstance(target_value, (int, float)) or target_value <= 0:
                    raise ValueError(
                        f"Location '{location_name}' has invalid target_breakeven_occupancy "
                        f"value: {target_value}. Must be a positive number."
                    )

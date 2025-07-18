# src/pricing/rules.py
from typing import Dict, Any
from .models import PricingRules, DynamicPricingTier


def build_rules(location: str, cfg: Dict[str, Any]) -> PricingRules:
    """Translate raw YAML config into a strongly-typed PricingRules object."""
    loc_cfg = cfg.get("locations", {}).get(location, {})
    return PricingRules(
        min_price=loc_cfg.get("min_price"),
        max_price=loc_cfg.get("max_price"),
        margin_of_safety=loc_cfg.get("margin_of_safety", cfg.get("margin_of_safety")),
        dynamic_pricing_tiers=[
            DynamicPricingTier(**tier) for tier in cfg.get("dynamic_pricing_tiers", [])
        ],
    )


def get_target_breakeven_occupancy(location: str, cfg: Dict[str, Any]) -> float:
    """Extract target breakeven occupancy for a location from config."""
    loc_cfg = cfg.get("locations", {}).get(location, {})
    return loc_cfg.get("target_breakeven_occupancy", 70.0)  # Default fallback

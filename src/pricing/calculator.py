from src.pricing.models import (
    DynamicPricingTier,
    LocationData,
    PricingRules,
    PricingResult,
    ManualOverrideInfo,
    PricingCLIOutput,
)
from src.pricing.rules import build_rules, get_target_breakeven_occupancy
from src.utils.parsing import (
    parse_float,
    parse_int,
    parse_pct,
    pct_to_decimal,
    decimal_to_pct,
)
from typing import Any, Dict


class PricingCalculator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def calculate_pricing(self, location_data: LocationData) -> PricingResult:
        rules = build_rules(location_data.name, self.config)
        target_breakeven_occupancy = get_target_breakeven_occupancy(
            location_data.name, self.config
        )
        step1 = self._calculate_breakeven_price(
            location_data, target_breakeven_occupancy
        )
        step2, dynamic_multiplier = self._apply_dynamic_multiplier(
            step1,
            location_data.po_seats_actual_occupied_pct,
            rules.dynamic_pricing_tiers,
        )
        step3 = self._apply_margin_of_safety(step2, rules.margin_of_safety)
        # Only round at the end
        step4 = self._enforce_price_bounds(
            self._round_to_nearest(step3), rules.min_price, rules.max_price
        )
        losing_money = (location_data.po_seats_actual_occupied_pct or 0) < (
            target_breakeven_occupancy or 0
        )
        return PricingResult(
            location=location_data.name,
            recommended_price=step4,
            manual_override=None,
            latest_occupancy=location_data.po_seats_actual_occupied_pct,
            breakeven_occupancy_pct=target_breakeven_occupancy,
            is_losing_money=losing_money,
            reasoning=None,
            # Additional fields for debugging/intermediate steps:
            breakeven_price=step1,
            base_price=step2,
            price_with_margin=step3,
            final_price=step4,
            losing_money=losing_money,
            dynamic_multiplier=dynamic_multiplier,
        )

    def _calculate_breakeven_price(
        self, location_data: LocationData, target_breakeven_occupancy: float
    ) -> float:
        if location_data.total_po_seats == 0 or not target_breakeven_occupancy:
            raise ValueError(
                "Total PO seats and target breakeven occupancy must be greater than zero."
            )
        # Convert target_breakeven_occupancy from percentage to decimal for calculation
        target_breakeven_decimal = pct_to_decimal(target_breakeven_occupancy)
        return location_data.avg_exp_total_po_expense_amount / (
            location_data.total_po_seats * target_breakeven_decimal
        )

    def _apply_dynamic_multiplier(
        self, breakeven_price: float, occupancy_pct: float, tiers
    ) -> tuple[float, float]:
        multiplier = 1.0
        for tier in tiers:
            # Both occupancy_pct and tier values are now in percentage format (0-100)
            if tier.min_occupancy < occupancy_pct <= tier.max_occupancy:
                multiplier = tier.multiplier
                break
        return breakeven_price * multiplier, multiplier

    def _apply_margin_of_safety(
        self, base_price: float, margin_of_safety: float
    ) -> float:
        return base_price * (1 + margin_of_safety)

    def _enforce_price_bounds(
        self, price: float, min_price: float, max_price: float
    ) -> float:
        if min_price is not None and price < min_price:
            return min_price
        if max_price is not None and price > max_price:
            return max_price
        return price

    def _round_to_nearest(self, value: float, nearest: int = 50000) -> float:
        return round(value / nearest) * nearest

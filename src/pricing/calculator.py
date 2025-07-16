from pricing.models import (
    get_location_rules,
    PricingRules,
    DynamicPricingTier,
    LocationData,
    PricingResult,
)
from typing import Any, Dict


class PricingCalculator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def calculate_pricing(self, location_data: LocationData) -> PricingResult:
        rules_dict = get_location_rules(location_data.name, self.config)
        rules = PricingRules(
            min_price=rules_dict["min_price"],
            max_price=rules_dict["max_price"],
            margin_of_safety=rules_dict["margin_of_safety"],
            dynamic_pricing_tiers=[
                DynamicPricingTier(**tier)
                for tier in rules_dict["dynamic_pricing_tiers"]
            ],
        )
        target_breakeven_occupancy = rules_dict.get("target_breakeven_occupancy", 0.7)
        step1 = self._calculate_breakeven_price(
            location_data, target_breakeven_occupancy
        )
        step2 = self._apply_dynamic_multiplier(
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
        )

    def _calculate_breakeven_price(
        self, location_data: LocationData, target_breakeven_occupancy: float
    ) -> float:
        if location_data.total_po_seats == 0 or not target_breakeven_occupancy:
            raise ValueError(
                "Total PO seats and target breakeven occupancy must be greater than zero."
            )
        return location_data.avg_exp_total_po_expense_amount / (
            location_data.total_po_seats * target_breakeven_occupancy
        )

    def _apply_dynamic_multiplier(
        self, breakeven_price: float, occupancy_pct: float, tiers
    ) -> float:
        multiplier = 1.0
        for tier in tiers:
            if tier.min_occupancy < occupancy_pct <= tier.max_occupancy:
                multiplier = tier.multiplier
                break
        return breakeven_price * multiplier

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

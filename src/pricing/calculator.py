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
        import logging

        logger = logging.getLogger(__name__)

        rules = build_rules(location_data.name, self.config)

        # Calculate actual breakeven occupancy pct if possible
        actual_breakeven_occupancy_pct = None
        if (
            location_data.sold_price_per_po_seat_actual
            and location_data.total_po_seats
            and location_data.sold_price_per_po_seat_actual > 0
            and location_data.total_po_seats > 0
        ):
            try:
                actual_breakeven_occupancy_pct = (
                    location_data.avg_exp_total_po_expense_amount
                    / (
                        location_data.sold_price_per_po_seat_actual
                        * location_data.total_po_seats
                    )
                ) * 100
            except Exception:
                actual_breakeven_occupancy_pct = None

        # Get target breakeven occupancy (smart or static)
        target_breakeven_occupancy, is_smart_target = get_target_breakeven_occupancy(
            location_data.name,
            self.config,
            actual_breakeven_occupancy_pct,
            location_data.po_seats_occupied_actual_pct,
        )

        # Log smart target usage
        if is_smart_target:
            logger.info(
                f"Smart target used for {location_data.name}: "
                f"actual_breakeven={actual_breakeven_occupancy_pct:.1f}%, "
                f"current_occupancy={location_data.po_seats_occupied_actual_pct:.1f}%, "
                f"smart_target={target_breakeven_occupancy:.1f}%"
            )
        else:
            logger.debug(
                f"Static target used for {location_data.name}: "
                f"target={target_breakeven_occupancy:.1f}% "
                f"(smart_targets_enabled={rules.use_smart_target}, "
                f"has_actual_breakeven={actual_breakeven_occupancy_pct is not None}, "
                f"has_current_occupancy={location_data.po_seats_occupied_actual_pct is not None})"
            )

        step1 = self._calculate_breakeven_price(
            location_data, target_breakeven_occupancy
        )
        # Round breakeven_price up to the nearest 50000 for output
        breakeven_price_rounded = self._round_up_to_nearest(step1, 50000)
        step2, dynamic_multiplier = self._apply_dynamic_multiplier(
            step1,
            location_data.po_seats_occupied_actual_pct,
            rules.dynamic_pricing_tiers,
        )
        step3 = self._apply_margin_of_safety(step2, rules.margin_of_safety)
        step4_rounded = self._round_to_nearest(step3)
        step4 = self._enforce_price_bounds(
            step4_rounded, rules.min_price, rules.max_price
        )

        # Only determine losing_money if we have actual breakeven occupancy data
        losing_money = None
        if actual_breakeven_occupancy_pct is not None:
            losing_money = (
                location_data.po_seats_occupied_actual_pct or 0
            ) < actual_breakeven_occupancy_pct
        else:
            losing_money = (
                False  # Cannot determine if losing money without actual breakeven data
            )
        return PricingResult(
            location=location_data.name,
            recommended_price=step4,
            manual_override=None,
            latest_occupancy=location_data.po_seats_occupied_actual_pct,
            target_breakeven_occupancy_pct=target_breakeven_occupancy,
            actual_breakeven_occupancy_pct=actual_breakeven_occupancy_pct,
            is_losing_money=losing_money,
            reasoning=None,
            # Additional fields for debugging/intermediate steps:
            breakeven_price=breakeven_price_rounded,
            base_price=step2,
            price_with_margin=step3,
            final_price=step4,
            losing_money=losing_money,
            dynamic_multiplier=dynamic_multiplier,
            is_smart_target=is_smart_target,  # Add smart target indicator
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

    def _round_up_to_nearest(self, value: float, nearest: int) -> float:
        """Round value up to the nearest multiple of 'nearest'."""
        import math

        # If value is already a multiple of 'nearest', return as is
        if value % nearest == 0:
            return value

        # Otherwise, round up to the next multiple
        return math.ceil(value / nearest) * nearest

    def calculate_dynamic_improvement_pct(
        self, breakeven_occupancy_pct: float, current_occupancy_pct: float
    ) -> float:
        """
        Calculate smart target improvement multiplier based on current profitability status.

        Args:
            breakeven_occupancy_pct: Current actual breakeven occupancy percentage
            current_occupancy_pct: Current occupancy percentage

        Returns:
            float: Improvement multiplier (e.g., 0.95 means 5% reduction in target)
        """
        # Calculate profitability status
        is_profitable = current_occupancy_pct >= breakeven_occupancy_pct

        if is_profitable:
            # Profitable locations - More aggressive targets (3-7% reduction)
            if breakeven_occupancy_pct <= 50:
                return 0.97  # 3% reduction (already very efficient)
            elif breakeven_occupancy_pct <= 70:
                return 0.95  # 5% reduction (good room for improvement)
            else:
                return 0.93  # 7% reduction (high breakeven = lots of room)
        else:
            # Losing money locations - Less aggressive targets (3-10% reduction)
            loss_gap = breakeven_occupancy_pct - current_occupancy_pct

            if loss_gap <= 15:
                return 0.97  # 3% reduction (achievable target)
            elif loss_gap <= 25:
                return 0.94  # 6% reduction (challenging but realistic)
            else:
                return 0.90  # 10% reduction (aggressive but not impossible)

    def calculate_smart_target_with_fallback(
        self,
        location_name: str,
        actual_breakeven_occupancy_pct: float,
        current_occupancy_pct: float,
    ) -> tuple[float, bool]:
        """
        Calculate smart target breakeven occupancy with fallback to static target.

        Args:
            location_name: Name of the location
            actual_breakeven_occupancy_pct: Current actual breakeven occupancy percentage
            current_occupancy_pct: Current occupancy percentage

        Returns:
            tuple[float, bool]: (target_breakeven_occupancy, is_smart_target)
        """
        try:
            # Check if smart targets are enabled for this location
            rules = build_rules(location_name, self.config)
            if not rules.use_smart_target:
                # Use static target
                static_target = get_target_breakeven_occupancy(
                    location_name, self.config
                )
                return static_target, False

            # Validate inputs for smart target calculation
            if actual_breakeven_occupancy_pct is None or current_occupancy_pct is None:
                raise ValueError("Missing required data for smart target calculation")

            if actual_breakeven_occupancy_pct <= 0:
                raise ValueError("Actual breakeven occupancy must be positive")

            # Calculate smart target
            improvement_multiplier = self.calculate_dynamic_improvement_pct(
                actual_breakeven_occupancy_pct, current_occupancy_pct
            )
            smart_target = actual_breakeven_occupancy_pct * improvement_multiplier

            return smart_target, True

        except Exception as e:
            # Fallback to static target on any error
            static_target = get_target_breakeven_occupancy(location_name, self.config)
            return static_target, False

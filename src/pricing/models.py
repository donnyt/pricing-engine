from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class DynamicPricingTier(BaseModel):
    min_occupancy: float
    max_occupancy: float
    multiplier: float


class LocationData(BaseModel):
    name: str
    exp_total_po_expense_amount: float
    avg_exp_total_po_expense_amount: float
    # Updated to use daily occupancy data from private_office_occupancies_by_building table
    po_seats_occupied_actual_pct: float  # Daily occupancy percentage
    po_seats_occupied_pct: Optional[float] = None  # Keep for backward compatibility
    total_po_seats: int
    published_price: Optional[float] = None


class PricingRules(BaseModel):
    min_price: Optional[float]
    max_price: Optional[float]
    margin_of_safety: float
    dynamic_pricing_tiers: List[DynamicPricingTier]


class PricingResult(BaseModel):
    location: str
    recommended_price: float
    manual_override: Optional[Dict[str, Any]] = None
    latest_occupancy: float
    breakeven_occupancy_pct: float
    is_losing_money: bool
    reasoning: Optional[str]
    breakeven_price: Optional[float] = None
    base_price: Optional[float] = None
    price_with_margin: Optional[float] = None
    final_price: Optional[float] = None
    losing_money: Optional[bool] = None
    dynamic_multiplier: Optional[float] = None


class ManualOverrideInfo(BaseModel):
    overridden_price: float
    overridden_by: str
    overridden_at: str
    reason: str
    original_price: float


class PricingCLIOutput(BaseModel):
    building_name: str
    occupancy_pct: float
    breakeven_occupancy_pct: float
    recommended_price: float
    losing_money: bool
    manual_override: Optional[ManualOverrideInfo] = None
    llm_reasoning: Optional[str] = None
    published_price: Optional[float] = None
    dynamic_multiplier: Optional[float] = None

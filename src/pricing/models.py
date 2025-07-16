from pydantic import BaseModel
from typing import Optional, List, Dict, Any


def get_location_rules(location: str, config: Dict[str, Any]) -> Dict[str, Any]:
    loc_rules = config.get("locations", {}).get(location, {})
    margin_of_safety = loc_rules.get("margin_of_safety", config.get("margin_of_safety"))
    min_price = loc_rules.get("min_price")
    max_price = loc_rules.get("max_price")
    tiers = config.get("dynamic_pricing_tiers", [])
    target_breakeven_occupancy = loc_rules.get("target_breakeven_occupancy")
    return {
        "min_price": min_price,
        "max_price": max_price,
        "margin_of_safety": margin_of_safety,
        "dynamic_pricing_tiers": tiers,
        "target_breakeven_occupancy": target_breakeven_occupancy,
    }


class DynamicPricingTier(BaseModel):
    min_occupancy: float
    max_occupancy: float
    multiplier: float


class LocationData(BaseModel):
    name: str
    exp_total_po_expense_amount: float
    avg_exp_total_po_expense_amount: float
    po_seats_actual_occupied_pct: float
    po_seats_occupied_pct: Optional[float] = None
    total_po_seats: int


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

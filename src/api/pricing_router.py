from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from src.pricing.service import get_pricing_service
from src.pricing.models import PricingCLIOutput

router = APIRouter(prefix="/api/v1")


@router.get("/pricing/{location}", response_model=Optional[PricingCLIOutput])
async def get_pricing_for_location(
    location: str,
    year: Optional[int] = Query(
        None, description="Year for pricing (default: current year)"
    ),
    month: Optional[int] = Query(
        None, description="Month for pricing (default: current month)"
    ),
):
    try:
        pricing_service = get_pricing_service()
        result = await pricing_service.get_pricing_for_location(location, year, month)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"No data for location '{location}'."
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing: {e}")


@router.get("/pricing", response_model=List[PricingCLIOutput])
async def get_pricing_for_all_locations(
    year: Optional[int] = Query(
        None, description="Year for pricing (default: current year)"
    ),
    month: Optional[int] = Query(
        None, description="Month for pricing (default: current month)"
    ),
):
    try:
        pricing_service = get_pricing_service()
        results = await pricing_service.get_pricing_for_all_locations(year, month)
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No pricing results found for the specified period.",
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing: {e}")

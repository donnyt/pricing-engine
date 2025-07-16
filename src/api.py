"""
FastAPI API for Pricing Engine

How to run locally:
    PYTHONPATH=src uvicorn src.api:app --reload

- Health check: GET /health
- GET /pricing/{location}: PO pricing for a single location (current or specified month)
- GET /pricing: PO pricing for all locations (current or specified month)
"""

from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
import datetime
import pandas as pd
from sqlite_storage import load_from_sqlite
from po_pricing_engine import load_pricing_rules, PricingCLIOutput
from pricing_pipeline import run_pricing_pipeline

app = FastAPI(title="Pricing Engine API", version="0.1.0")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/pricing/{location}", response_model=Optional[PricingCLIOutput])
def get_pricing_for_location(
    location: str,
    year: Optional[int] = Query(
        None, description="Year for pricing (default: current year)"
    ),
    month: Optional[int] = Query(
        None, description="Month for pricing (default: current month)"
    ),
):
    """Get private office pricing for a single location for the specified or current month."""
    try:
        df = load_from_sqlite("pnl_sms_by_month")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {e}")
    if df.empty:
        raise HTTPException(status_code=404, detail="No data available.")
    now = datetime.datetime.now()
    target_year = int(year) if year is not None else now.year
    target_month = int(month) if month is not None else now.month
    # Normalize location: replace dashes with spaces, strip, lowercase
    normalized_location = location.replace("-", " ").strip().lower()
    df = df[
        df["building_name"].astype(str).str.strip().str.lower() == normalized_location
    ]
    if df.empty:
        raise HTTPException(
            status_code=404, detail=f"No data for location '{location}'."
        )
    config = load_pricing_rules()
    outputs = run_pricing_pipeline(
        df, config, target_year=target_year, target_month=target_month, verbose=False
    )
    if not outputs:
        raise HTTPException(
            status_code=404,
            detail=f"No pricing result for location '{location}' in {target_year}-{target_month:02d}.",
        )
    return outputs[0]


@app.get("/pricing", response_model=List[PricingCLIOutput])
def get_pricing_for_all_locations(
    year: Optional[int] = Query(
        None, description="Year for pricing (default: current year)"
    ),
    month: Optional[int] = Query(
        None, description="Month for pricing (default: current month)"
    ),
):
    """Get private office pricing for all locations for the specified or current month."""
    try:
        df = load_from_sqlite("pnl_sms_by_month")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {e}")
    if df.empty:
        raise HTTPException(status_code=404, detail="No data available.")
    now = datetime.datetime.now()
    target_year = int(year) if year is not None else now.year
    target_month = int(month) if month is not None else now.month
    config = load_pricing_rules()
    outputs = run_pricing_pipeline(
        df, config, target_year=target_year, target_month=target_month, verbose=False
    )
    if not outputs:
        raise HTTPException(
            status_code=404,
            detail=f"No pricing results found for {target_year}-{target_month:02d}.",
        )
    return outputs

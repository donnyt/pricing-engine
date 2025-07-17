"""
Unified FastAPI Application for Pricing Engine

Combines both API endpoints and Google Chat webhook functionality.

How to run locally:
    PYTHONPATH=. uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

API Endpoints:
- Health check: GET /api/v1/health
- GET /api/v1/pricing/{location}: PO pricing for a single location
- GET /api/v1/pricing: PO pricing for all locations

Webhook Endpoints:
- POST /webhook/google-chat: Google Chat bot webhook
"""

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from google.oauth2 import service_account
from pydantic import BaseModel
from typing import List, Optional, Literal, Tuple
import os
import json
import re
from datetime import datetime

from src.pricing.service import get_pricing_service
from src.pricing.formatter import get_formatter
from src.pricing.models import PricingCLIOutput

# Create the main FastAPI app
app = FastAPI(
    title="Pricing Engine",
    description="Unified API for pricing engine with Google Chat integration",
    version="1.0.0",
)

# Load Google service account credentials
SERVICE_ACCOUNT_FILE = "config/credentials/service-account.json"
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/chat.bot"]
)


# ============================================================================
# Pydantic Models
# ============================================================================


class GoogleChatEvent(BaseModel):
    """Pydantic model for Google Chat event payload."""

    type: Literal["MESSAGE", "ADDED_TO_SPACE", "REMOVED_FROM_SPACE", "CARD_CLICKED"]
    eventTime: Optional[str]
    message: Optional[dict]
    space: Optional[dict]
    user: Optional[dict]


# ============================================================================
# API Endpoints (REST API)
# ============================================================================


@app.get("/api/v1/health")
def health_check():
    """Health check endpoint for the unified API."""
    return {"status": "ok", "service": "pricing-engine"}


@app.get("/api/v1/pricing/{location}", response_model=Optional[PricingCLIOutput])
async def get_pricing_for_location(
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
        pricing_service = get_pricing_service()
        result = await pricing_service.get_pricing_for_location(location, year, month)

        if result is None:
            raise HTTPException(
                status_code=404, detail=f"No data for location '{location}'."
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing: {e}")


@app.get("/api/v1/pricing", response_model=List[PricingCLIOutput])
async def get_pricing_for_all_locations(
    year: Optional[int] = Query(
        None, description="Year for pricing (default: current year)"
    ),
    month: Optional[int] = Query(
        None, description="Month for pricing (default: current month)"
    ),
):
    """Get private office pricing for all locations for the specified or current month."""
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


# ============================================================================
# Webhook Endpoints (Google Chat)
# ============================================================================


def parse_po_price_command(message_text: str) -> Tuple[str, Optional[str]]:
    """
    Parse /po-price command to extract location and optional month.

    Args:
        message_text: Raw message text from Google Chat

    Returns:
        Tuple of (location, month) where month is YYYY-MM format or None

    Raises:
        ValueError: If command format is invalid or location is missing
    """
    # Remove leading/trailing whitespace and convert to lowercase
    text = message_text.strip().lower()

    # Check if it's a po-price command
    if not text.startswith("/po-price"):
        raise ValueError("Not a po-price command")

    # Extract the arguments after /po-price
    args_text = text[len("/po-price") :].strip()
    if not args_text:
        raise ValueError("Location is required. Usage: /po-price <location> [month]")

    # Split by whitespace to get location and optional month
    parts = args_text.split()
    if len(parts) < 1:
        raise ValueError("Location is required. Usage: /po-price <location> [month]")

    # Location is everything except the last part (if it looks like a month)
    location_parts = (
        parts[:-1]
        if len(parts) > 1 and re.match(r"^\d{4}-\d{2}$", parts[-1])
        else parts
    )
    location = " ".join(location_parts)
    month = None

    # Check if month is provided (last part matches YYYY-MM format)
    if len(parts) > 1 and re.match(r"^\d{4}-\d{2}$", parts[-1]):
        month = parts[-1]
        # Validate month number (01-12)
        year, month_num = month.split("-")
        if not (1 <= int(month_num) <= 12):
            raise ValueError("Month must be between 01-12")

        # Validate year (reasonable range)
        year_int = int(year)
        if not (2020 <= year_int <= 2030):
            raise ValueError("Year must be between 2020-2030")

    return location, month


async def get_pricing_data_for_chat(location: str, month: Optional[str] = None):
    """
    Get pricing data using the pricing service for Google Chat responses.

    Args:
        location: Location name
        month: Optional month in YYYY-MM format

    Returns:
        Pricing data from service

    Raises:
        HTTPException: If location not found or service error
    """
    # Parse month to year and month parameters
    year_param = None
    month_param = None
    if month:
        year_str, month_str = month.split("-")
        year_param = int(year_str)
        month_param = int(month_str)

    try:
        pricing_service = get_pricing_service()
        result = await pricing_service.get_pricing_for_location(
            location, year_param, month_param
        )

        if result is None:
            raise HTTPException(
                status_code=404, detail=f"Location '{location}' not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing data: {e}")


@app.post("/webhook/google-chat")
async def receive_google_chat_event(request: Request) -> JSONResponse:
    """Receives and parses Google Chat events using service account authentication."""
    # For Google Chat bots, we typically don't need to verify the request
    # as Google handles authentication at the platform level
    # But we can add basic validation if needed

    payload = await request.json()
    try:
        event = GoogleChatEvent(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid event payload: {e}")

    # Basic event type routing (expand in future tasks)
    if event.type == "MESSAGE":
        # Extract message text
        message_text = event.message.get("text", "") if event.message else ""

        try:
            location, month = parse_po_price_command(message_text)

            # Get pricing data using service
            pricing_data = await get_pricing_data_for_chat(location, month)

            # Format response using formatter
            formatter = get_formatter("google_chat")
            formatted_response = formatter.format_pricing_response(pricing_data)

            return JSONResponse({"text": formatted_response})

        except ValueError as e:
            return JSONResponse({"text": f"**Error:** {str(e)}"})
        except HTTPException as e:
            return JSONResponse({"text": f"**Error:** {e.detail}"})
        except Exception as e:
            return JSONResponse({"text": f"**Unexpected error:** {str(e)}"})

    elif event.type == "ADDED_TO_SPACE":
        return JSONResponse({"text": "Bot added to space"})
    elif event.type == "REMOVED_FROM_SPACE":
        return JSONResponse({"text": "Bot removed from space"})
    elif event.type == "CARD_CLICKED":
        return JSONResponse({"text": "Card clicked event"})
    else:
        return JSONResponse({"text": f"Unknown event type: {event.type}"})


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Pricing Engine",
        "version": "1.0.0",
        "endpoints": {
            "api": "/api/v1/",
            "webhook": "/webhook/google-chat",
            "docs": "/docs",
        },
    }

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Literal, Tuple
from pydantic import BaseModel
import re
from src.pricing.service import get_pricing_service
from src.pricing.formatter import get_formatter

router = APIRouter(prefix="/webhook")


class GoogleChatEvent(BaseModel):
    type: Literal["MESSAGE", "ADDED_TO_SPACE", "REMOVED_FROM_SPACE", "CARD_CLICKED"]
    eventTime: Optional[str]
    message: Optional[dict]
    space: Optional[dict]
    user: Optional[dict]


def parse_po_price_command(message_text: str) -> Tuple[str, Optional[str]]:
    text = message_text.strip().lower()
    if not text.startswith("/po-price"):
        raise ValueError("Not a po-price command")
    args_text = text[len("/po-price") :].strip()
    if not args_text:
        raise ValueError("Location is required. Usage: /po-price <location> [month]")
    parts = args_text.split()
    location_parts = (
        parts[:-1]
        if len(parts) > 1 and re.match(r"^\d{4}-\d{2}$", parts[-1])
        else parts
    )
    location = " ".join(location_parts)
    month = None
    if len(parts) > 1 and re.match(r"^\d{4}-\d{2}$", parts[-1]):
        month = parts[-1]
        year, month_num = month.split("-")
        if not (1 <= int(month_num) <= 12):
            raise ValueError("Month must be between 01-12")
        year_int = int(year)
        if not (2020 <= year_int <= 2030):
            raise ValueError("Year must be between 2020-2030")
    return location, month


async def get_pricing_data_for_chat(location: str, month: Optional[str] = None):
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


@router.post("/google-chat")
async def receive_google_chat_event(request: Request) -> JSONResponse:
    payload = await request.json()
    try:
        event = GoogleChatEvent(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid event payload: {e}")
    if event.type == "MESSAGE":
        message_text = event.message.get("text", "") if event.message else ""
        try:
            location, month = parse_po_price_command(message_text)
            pricing_data = await get_pricing_data_for_chat(location, month)
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

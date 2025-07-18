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

from fastapi import FastAPI
from src.api.pricing_router import router as pricing_router
from src.webhooks.google_chat_router import router as google_chat_router

app = FastAPI(
    title="Pricing Engine",
    description="Unified API for pricing engine with Google Chat integration",
    version="1.0.0",
)

app.include_router(pricing_router)
app.include_router(google_chat_router)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "pricing-engine"}


@app.get("/")
async def root():
    return {
        "service": "Pricing Engine",
        "version": "1.0.0",
        "endpoints": {
            "api": "/api/v1/",
            "webhook": "/webhook/google-chat",
            "docs": "/docs",
        },
    }

"""
FastAPI API for Pricing Engine

How to run locally:
    uvicorn src.api:app --reload

- Health check: GET /health
- Ready for additional endpoints (see TODOs)
"""

from fastapi import FastAPI

app = FastAPI(title="Pricing Engine API", version="0.1.0")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# TODO: Add endpoints for pricing, data retrieval, etc.

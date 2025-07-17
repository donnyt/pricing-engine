"""
Pricing Service Layer

This module provides a clean abstraction for pricing operations that can be used
by both the API and Google Chat app, eliminating code duplication and following
SOLID principles.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd
from pydantic import BaseModel

from src.pricing.models import PricingCLIOutput, LocationData, PricingRules
from src.pricing.calculator import PricingCalculator
from src.sqlite_storage import load_from_sqlite
from src.po_pricing_engine import load_pricing_rules
from src.pricing_pipeline import run_pricing_pipeline


class PricingServiceInterface(ABC):
    """Abstract interface for pricing operations following Interface Segregation Principle."""

    @abstractmethod
    async def get_pricing_for_location(
        self, location: str, year: Optional[int] = None, month: Optional[int] = None
    ) -> Optional[PricingCLIOutput]:
        """Get pricing data for a specific location and time period."""
        pass

    @abstractmethod
    async def get_pricing_for_all_locations(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> List[PricingCLIOutput]:
        """Get pricing data for all locations in a time period."""
        pass


class PricingService(PricingServiceInterface):
    """
    Concrete implementation of pricing service.

    Follows Single Responsibility Principle - only handles pricing operations.
    Follows Dependency Inversion Principle - depends on abstractions.
    """

    def __init__(self):
        """Initialize the pricing service with required dependencies."""
        self._config = None
        self._data = None

    def _load_config(self) -> Dict[str, Any]:
        """Load pricing configuration (lazy loading)."""
        if self._config is None:
            self._config = load_pricing_rules()
        return self._config

    def _load_data(self) -> pd.DataFrame:
        """Load pricing data (lazy loading)."""
        if self._data is None:
            self._data = load_from_sqlite("pnl_sms_by_month")
        return self._data

    async def get_pricing_for_location(
        self, location: str, year: Optional[int] = None, month: Optional[int] = None
    ) -> Optional[PricingCLIOutput]:
        """
        Get pricing data for a specific location and time period.

        Args:
            location: Location name
            year: Target year (defaults to current year)
            month: Target month (defaults to current month)

        Returns:
            PricingCLIOutput or None if location not found
        """
        # Set default year/month if not provided
        now = datetime.now()
        target_year = year if year is not None else now.year
        target_month = month if month is not None else now.month

        # Load data and config
        df = self._load_data()
        config = self._load_config()

        if df.empty:
            return None

        # Normalize location name for matching
        normalized_location = location.replace("-", " ").strip().lower()
        location_data = df[
            df["building_name"].astype(str).str.strip().str.lower()
            == normalized_location
        ]

        if location_data.empty:
            return None

        # Run pricing pipeline
        outputs = run_pricing_pipeline(
            location_data,
            config,
            target_year=target_year,
            target_month=target_month,
            verbose=False,
        )

        return outputs[0] if outputs else None

    async def get_pricing_for_all_locations(
        self, year: Optional[int] = None, month: Optional[int] = None
    ) -> List[PricingCLIOutput]:
        """
        Get pricing data for all locations in a time period.

        Args:
            year: Target year (defaults to current year)
            month: Target month (defaults to current month)

        Returns:
            List of PricingCLIOutput objects
        """
        # Set default year/month if not provided
        now = datetime.now()
        target_year = year if year is not None else now.year
        target_month = month if month is not None else now.month

        # Load data and config
        df = self._load_data()
        config = self._load_config()

        if df.empty:
            return []

        # Run pricing pipeline for all locations
        outputs = run_pricing_pipeline(
            df,
            config,
            target_year=target_year,
            target_month=target_month,
            verbose=False,
        )

        return outputs


# Global service instance (dependency injection)
_pricing_service: Optional[PricingService] = None


def get_pricing_service() -> PricingService:
    """
    Get the global pricing service instance (singleton pattern).

    This follows the Dependency Inversion Principle by providing
    a single point of access to the pricing service.
    """
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService()
    return _pricing_service

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
from src.data.loader import DataLoaderService


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
        self._data_loader = DataLoaderService()

    def _load_config(self) -> Dict[str, Any]:
        """Load pricing configuration (lazy loading)."""
        if self._config is None:
            self._config = load_pricing_rules()
        return self._config

    def _load_data(
        self, target_date: Optional[str] = None, location: Optional[str] = None
    ) -> pd.DataFrame:
        """Load pricing data using DataLoaderService (lazy loading)."""
        return self._data_loader.load_merged_pricing_data(
            target_date, location, auto_fetch=True
        )

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
        target_date = f"{target_year}-{target_month:02d}-01"  # Use first day of month
        df = self._load_data(target_date, location)
        config = self._load_config()

        if df.empty:
            return None

        # Run pricing pipeline with the loaded data
        outputs = run_pricing_pipeline(
            df,
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
        target_date = f"{target_year}-{target_month:02d}-01"  # Use first day of month
        df = self._load_data(target_date)
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

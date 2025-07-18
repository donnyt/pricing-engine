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
import logging
from pydantic import BaseModel

try:
    from src.pricing.models import PricingCLIOutput, LocationData, PricingRules
    from src.pricing.calculator import PricingCalculator
    from src.pricing.rules import build_rules
    from src.pricing.reasoning import generate_llm_reasoning
    from src.data.storage import load_from_sqlite, get_published_price
    from src.config.rules import load_pricing_rules
    from src.data.loader import DataLoaderService
    from src.utils.parsing import parse_float, parse_int, parse_pct
    from src.utils.error_handler import (
        handle_errors,
        error_boundary,
        safe_parse,
        validate_required_field,
        log_and_continue,
        create_error_context,
    )
    from src.exceptions import (
        DataNotFoundException,
        DataValidationException,
        CalculationException,
        LLMServiceException,
        ParsingException,
    )
except ImportError:
    # Fallback for when running the script directly
    from pricing.models import PricingCLIOutput, LocationData, PricingRules
    from pricing.calculator import PricingCalculator
    from pricing.rules import build_rules
    from pricing.reasoning import generate_llm_reasoning
    from data.storage import load_from_sqlite, get_published_price
    from config.rules import load_pricing_rules
    from data.loader import DataLoaderService
    from utils.parsing import parse_float, parse_int, parse_pct
    from utils.error_handler import (
        handle_errors,
        error_boundary,
        safe_parse,
        validate_required_field,
        log_and_continue,
        create_error_context,
    )
    from exceptions import (
        DataNotFoundException,
        DataValidationException,
        CalculationException,
        LLMServiceException,
        ParsingException,
    )


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

    @abstractmethod
    def run_pricing_pipeline(
        self,
        input_df: pd.DataFrame = None,
        config: dict = None,
        target_year: int = None,
        target_month: int = None,
        target_date: str = None,
        verbose: bool = False,
        auto_fetch: bool = True,
        target_location: str = None,
    ) -> List[PricingCLIOutput]:
        """Run the pricing pipeline with integrated logic."""
        pass


class PricingService(PricingServiceInterface):
    """
    Concrete implementation of pricing service with integrated pipeline logic.

    Follows Single Responsibility Principle - only handles pricing operations.
    Follows Dependency Inversion Principle - depends on abstractions.
    """

    def __init__(self):
        """Initialize the pricing service with required dependencies."""
        self._config = None
        self._data_loader = DataLoaderService()
        self._logger = logging.getLogger(__name__)

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

    def _get_occupancy_with_fallback(self, row, context=None):
        """
        Get occupancy percentage with fallback logic for different column names.

        Args:
            row: DataFrame row containing occupancy data
            context: Optional error context for better error reporting

        Returns:
            float: Parsed occupancy percentage or None if not available
        """
        # Try different column names in order of preference
        columns_to_try = [
            "po_seats_occupied_actual_pct",
            "po_seats_actual_occupied_pct",
            "po_seats_occupied_pct",
        ]

        for col in columns_to_try:
            if col in row and row[col] is not None:
                parsed = safe_parse(parse_pct, row[col], f"occupancy_{col}", context)
                if parsed is not None:
                    return parsed

        return None

    @handle_errors(
        operation="pricing_pipeline",
        default_return=[],
        log_level=logging.ERROR,
        reraise=False,
    )
    def run_pricing_pipeline(
        self,
        input_df: pd.DataFrame = None,
        config: dict = None,
        target_year: int = None,
        target_month: int = None,
        target_date: str = None,
        verbose: bool = False,
        auto_fetch: bool = True,
        target_location: str = None,
    ) -> List[PricingCLIOutput]:
        """
        Process the input data using pricing rules and return a list of PricingCLIOutput.
        Updated to use daily occupancy data from private_office_occupancies_by_building table.

        Args:
            input_df: Optional DataFrame. If None, will load merged data from both tables.
            config: Pricing configuration dictionary.
            target_year: Target year for monthly data (default: current year).
            target_month: Target month for monthly data (default: current month).
            target_date: Target date for daily occupancy data in 'YYYY-MM-DD' format (default: today).
            verbose: Whether to include LLM reasoning in output.
            auto_fetch: Whether to automatically fetch daily occupancy data from Zoho if not available (default: True).
        """
        outputs: List[PricingCLIOutput] = []

        # Load config if not provided
        if config is None:
            config = self._load_config()

        # Load merged data if not provided
        if input_df is None:
            # Default target_date to today if not provided
            if target_date is None:
                target_date = datetime.now().strftime("%Y-%m-%d")

            # Use DataLoaderService for consistent data loading
            with error_boundary(
                "load_merged_data", target_location, "DataLoaderService"
            ):
                input_df = self._data_loader.load_merged_pricing_data(
                    target_date, target_location, auto_fetch
                )

        if input_df.empty:
            self._logger.warning("No data available for pricing pipeline")
            return outputs

        # Default to current year/month if not provided
        now = datetime.now()
        if target_year is None:
            target_year = now.year
        if target_month is None:
            target_month = now.month

        # Normalize building names to avoid trailing spaces or invisible characters
        input_df["building_name"] = input_df["building_name"].astype(str).str.strip()

        calculator = PricingCalculator(config)

        # Process only unique locations to avoid duplicates
        processed_locations = set()

        for _, row in input_df.iterrows():
            loc = str(row["building_name"]).strip()

            # Skip if we've already processed this location
            if loc in processed_locations:
                continue
            processed_locations.add(loc)

            total_po_seats = (
                parse_int(row.get("total_po_seats"))
                if row.get("total_po_seats") not in [None, "None", "", "nan"]
                else 0
            )

            if not loc:
                continue
            if str(loc).strip().lower() == "holding":
                continue
            if total_po_seats == 0:
                continue

            # Calculate 7-day average occupancy for this location
            context = create_error_context("calculate_occupancy", loc, "daily_data")

            if "po_seats_occupied_actual_pct" in input_df.columns:
                location_daily_data = input_df[
                    (input_df["building_name"] == loc)
                    & (input_df["po_seats_occupied_actual_pct"].notna())
                ]
            else:
                # If the column doesn't exist, use empty DataFrame
                location_daily_data = pd.DataFrame()

            # Use daily occupancy data if available, fallback to monthly
            if not location_daily_data.empty:
                # Calculate 7-day average occupancy
                daily_occupancies = []
                for occ in location_daily_data["po_seats_occupied_actual_pct"]:
                    parsed = safe_parse(parse_pct, occ, "occupancy_percentage", context)
                    if parsed is not None:
                        daily_occupancies.append(parsed)
                    else:
                        log_and_continue(
                            ParsingException(
                                "occupancy_percentage", occ, "Invalid format", context
                            ),
                            "parse_occupancy",
                            loc,
                            logging.WARNING,
                        )

                if daily_occupancies:
                    occupancy_pct = round(
                        sum(daily_occupancies) / len(daily_occupancies), 1
                    )
                    data_source = "7-day average"
                    # Count unique dates to get actual number of days
                    unique_dates = location_daily_data["date"].nunique()
                    daily_occupancy = f"{unique_dates} days avg"
                else:
                    # Fallback to single day data with column fallback logic
                    occupancy_pct = self._get_occupancy_with_fallback(row, context)
                    data_source = "single day"
                    daily_occupancy = row.get("po_seats_occupied_actual_pct")
            else:
                # Fallback to single day data with column fallback logic
                occupancy_pct = self._get_occupancy_with_fallback(row, context)
                if occupancy_pct is not None:
                    occupancy_pct = round(occupancy_pct, 1)
                data_source = "single day"
                daily_occupancy = row.get("po_seats_occupied_actual_pct")

            monthly_occupancy = row.get("po_seats_actual_occupied_pct")

            # Fallback to monthly if no daily data available
            if occupancy_pct is None:
                occupancy_pct = self._get_occupancy_with_fallback(row, context)
                if occupancy_pct is not None:
                    occupancy_pct = round(occupancy_pct, 1)
                data_source = "monthly"
                if occupancy_pct is None:
                    self._logger.warning(f"No occupancy data available for {loc}")
                    continue

            if occupancy_pct is None:
                print(f"Warning: No occupancy data available for {loc}")
                continue

            # Calculate 3-month average expense for this location
            location_monthly_data = input_df[
                (input_df["building_name"] == loc)
                & (input_df["year"] == target_year)
                & (
                    input_df["month"].isin(
                        [target_month - 2, target_month - 1, target_month]
                    )
                )
            ]

            if location_monthly_data.empty:
                # Fallback to current month if no 3-month data available
                avg_exp = abs(parse_float(row.get("exp_total_po_expense_amount")))
            else:
                # Calculate 3-month average
                expenses = [
                    abs(parse_float(exp))
                    for exp in location_monthly_data["exp_total_po_expense_amount"]
                ]
                avg_exp = sum(expenses) / len(expenses)

            # Fetch published price for this location/month
            published_price = get_published_price(loc, target_year, target_month)

            location_data = LocationData(
                name=loc,
                exp_total_po_expense_amount=parse_float(
                    row.get("exp_total_po_expense_amount"), absolute=True
                ),
                avg_exp_total_po_expense_amount=avg_exp,
                po_seats_occupied_actual_pct=occupancy_pct,
                po_seats_occupied_pct=(
                    parse_pct(row.get("po_seats_occupied_pct"))
                    if row.get("po_seats_occupied_pct") not in [None, "None", ""]
                    else None
                ),
                total_po_seats=total_po_seats,
                published_price=published_price,
                sold_price_per_po_seat_actual=(
                    parse_float(row.get("sold_price_per_po_seat_actual"))
                    if row.get("sold_price_per_po_seat_actual")
                    not in [None, "None", ""]
                    else None
                ),
            )

            # Calculate pricing with proper error handling
            calc_context = create_error_context(
                "calculate_pricing", loc, "pricing_calculator"
            )

            with error_boundary(
                "pricing_calculation", loc, "PricingCalculator", reraise=False
            ):
                pricing_result = calculator.calculate_pricing(location_data)

                # Prepare context for LLM reasoning
                llm_context = {
                    "location": loc,
                    "recommended_price": pricing_result.final_price,
                    "occupancy_pct": location_data.po_seats_occupied_actual_pct,
                    "target_breakeven_occupancy_pct": pricing_result.target_breakeven_occupancy_pct,
                    "actual_breakeven_occupancy_pct": pricing_result.actual_breakeven_occupancy_pct,
                    "published_price": location_data.published_price,
                }

                # Generate LLM reasoning with error handling
                llm_reasoning = None
                if verbose:
                    with error_boundary(
                        "llm_reasoning", loc, "LLMService", reraise=False
                    ):
                        llm_reasoning = generate_llm_reasoning(llm_context)

                output = PricingCLIOutput(
                    building_name=loc,
                    occupancy_pct=round(location_data.po_seats_occupied_actual_pct, 2),
                    target_breakeven_occupancy_pct=round(
                        pricing_result.target_breakeven_occupancy_pct, 2
                    ),
                    actual_breakeven_occupancy_pct=(
                        round(pricing_result.actual_breakeven_occupancy_pct, 2)
                        if pricing_result.actual_breakeven_occupancy_pct is not None
                        else None
                    ),
                    dynamic_multiplier=pricing_result.dynamic_multiplier,
                    recommended_price=pricing_result.final_price,
                    losing_money=pricing_result.losing_money,
                    manual_override=None,
                    llm_reasoning=llm_reasoning,
                    published_price=location_data.published_price,
                    breakeven_price=pricing_result.breakeven_price,
                    sold_price_per_po_seat_actual=location_data.sold_price_per_po_seat_actual,
                    is_smart_target=pricing_result.is_smart_target,
                )
                outputs.append(output)

        return outputs

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
        outputs = self.run_pricing_pipeline(
            df,
            config=config,  # Pass the loaded config explicitly
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
        outputs = self.run_pricing_pipeline(
            df,
            config=config,  # Pass the loaded config explicitly
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

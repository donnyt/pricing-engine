"""
Data Loader Service

This module provides a centralized service for loading and merging pricing data
from multiple sources, following the Single Responsibility Principle.
"""

from typing import Optional
from datetime import date, datetime, timedelta
import pandas as pd
from src.sqlite_storage import load_from_sqlite


class DataLoaderService:
    """
    Centralized service for loading pricing data from multiple sources.

    Follows Single Responsibility Principle - only handles data loading operations.
    Eliminates code duplication between po_pricing_engine.py and pricing_pipeline.py.
    """

    def load_merged_pricing_data(
        self,
        target_date: Optional[str] = None,
        target_location: Optional[str] = None,
        auto_fetch: bool = True,
    ) -> pd.DataFrame:
        """
        Load and merge data from both monthly expense data and daily occupancy data.

        Args:
            target_date: Date in 'YYYY-MM-DD' format. If None, uses today's date.
            target_location: Specific location to load data for. If None, loads all locations.
            auto_fetch: Whether to automatically fetch daily occupancy data from Zoho if not available.

        Returns:
            DataFrame with merged data for pricing calculations.
        """
        # Use today's date if not specified
        if target_date is None:
            target_date = date.today().strftime("%Y-%m-%d")

        # Parse target date to get year and month
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        target_year = target_datetime.year
        target_month = target_datetime.month

        # Load monthly expense data
        monthly_df = self.load_monthly_expense_data(
            target_year, target_month, target_location
        )
        # Ensure sold_price_per_po_seat_actual is present for downstream use
        # (pnl_sms_by_month should have this column)

        # Load daily occupancy data
        daily_df = self.load_daily_occupancy_data(
            target_date, target_location, auto_fetch
        )

        # Merge the dataframes on building_name
        if not monthly_df.empty and not daily_df.empty:
            merged_df = pd.merge(
                monthly_df,
                daily_df,
                on="building_name",
                how="left",
                suffixes=("_monthly", "_daily"),
            )
            print(f"Merged data contains {len(merged_df)} rows.")
            return merged_df
        elif not monthly_df.empty:
            print("Using only monthly data (no daily occupancy data available).")
            return monthly_df
        else:
            print("No data available from either table.")
            return pd.DataFrame()

    def load_monthly_expense_data(
        self, target_year: int, target_month: int, location: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load monthly expense data for the last 3 months.

        Args:
            target_year: Target year for data
            target_month: Target month for data
            location: Specific location to filter by (optional)

        Returns:
            DataFrame with monthly expense data
        """
        # Calculate 3 months prior for expense averaging
        target_datetime = datetime(target_year, target_month, 1)
        three_months_ago = target_datetime - timedelta(days=90)
        start_year = three_months_ago.year
        start_month = three_months_ago.month

        try:
            # Load monthly expense data for the last 3 months
            monthly_df = load_from_sqlite("pnl_sms_by_month")

            # Filter to last 3 months
            monthly_df = monthly_df[
                (
                    (monthly_df["year"] == target_year)
                    & (monthly_df["month"] >= start_month)
                )
                | (
                    (monthly_df["year"] == start_year)
                    & (monthly_df["month"] >= start_month)
                )
            ]

            # Filter by location if specified
            if location:
                monthly_df = monthly_df[
                    monthly_df["building_name"].str.lower() == location.lower()
                ]

            print(
                f"Loaded {len(monthly_df)} rows from monthly expense data (last 3 months)."
            )
            return monthly_df
        except Exception as e:
            print(f"Error loading monthly expense data: {e}")
            return pd.DataFrame()

    def load_daily_occupancy_data(
        self, target_date: str, location: Optional[str] = None, auto_fetch: bool = True
    ) -> pd.DataFrame:
        """
        Load daily occupancy data for the past 7 days.

        Args:
            target_date: Target date in 'YYYY-MM-DD' format
            location: Specific location to filter by (optional)
            auto_fetch: Whether to automatically fetch from Zoho if data is missing

        Returns:
            DataFrame with daily occupancy data
        """
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")

        try:
            # Load daily occupancy data for last 7 days from target date
            daily_df = load_from_sqlite("private_office_occupancies_by_building")

            # Calculate date range for past 7 days (excluding target date)
            seven_days_ago = target_datetime - timedelta(days=7)

            # Generate list of dates for the past 7 days (excluding target date)
            date_range = []
            current_dt = seven_days_ago
            while (
                current_dt < target_datetime
            ):  # Use < instead of <= to exclude target date
                date_range.append(current_dt.strftime("%Y-%m-%d"))
                current_dt += timedelta(days=1)

            # Filter to last 7 days
            if not daily_df.empty and "date" in daily_df.columns:
                daily_df = daily_df[daily_df["date"].isin(date_range)]

                # Filter by location if specified
                if location:
                    daily_df = daily_df[
                        daily_df["building_name"].str.lower() == location.lower()
                    ]

                print(
                    f"Loaded {len(daily_df)} rows from daily occupancy data for past 7 days "
                    f"({seven_days_ago.strftime('%Y-%m-%d')} to {(target_datetime - timedelta(days=1)).strftime('%Y-%m-%d')})."
                )

                # Check if we have data for the target date in the entire table, if not fetch from Zoho
                if auto_fetch:
                    # Check the entire table for the target date, not just the filtered data
                    all_daily_df = load_from_sqlite(
                        "private_office_occupancies_by_building"
                    )
                    target_date_exists = (
                        not all_daily_df.empty
                        and "date" in all_daily_df.columns
                        and any(all_daily_df["date"] == target_date)
                    )

                    if not target_date_exists:
                        print(
                            f"No daily occupancy data found for {target_date} in SQLite. Fetching from Zoho Analytics..."
                        )
                        try:
                            from src.zoho_integration import (
                                upsert_private_office_occupancies_by_building,
                            )

                            upsert_private_office_occupancies_by_building(target_date)
                            print(
                                f"Successfully fetched and saved daily occupancy data for {target_date}."
                            )
                            # Reload the filtered data after fetching
                            daily_df = load_from_sqlite(
                                "private_office_occupancies_by_building"
                            )
                            daily_df = daily_df[daily_df["date"].isin(date_range)]
                            if location:
                                daily_df = daily_df[
                                    daily_df["building_name"].str.lower()
                                    == location.lower()
                                ]
                            print(
                                f"Reloaded {len(daily_df)} rows from daily occupancy data."
                            )
                        except Exception as e:
                            print(f"Error fetching daily occupancy data from Zoho: {e}")
                            print("Continuing with available data...")
                    else:
                        print(
                            f"Daily occupancy data for {target_date} already exists in SQLite. Skipping fetch."
                        )

                return daily_df
            else:
                print("No daily occupancy data available or missing 'date' column.")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading daily occupancy data: {e}")
            return pd.DataFrame()

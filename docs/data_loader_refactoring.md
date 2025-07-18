# Data Loader Service Refactoring

## Overview

This document describes the refactoring of data loading logic to eliminate code duplication and follow the Single Responsibility Principle (SRP).

## Problem

**SRP Violation**: Data loading logic was duplicated across multiple files:
- `po_pricing_engine.py` had `load_merged_pricing_data()`
- `pricing_pipeline.py` had `load_merged_pricing_data_simple()`

This violated the Single Responsibility Principle and created maintenance issues.

## Solution

Created a centralized `DataLoaderService` class in `src/data/loader.py` that consolidates all data loading operations.

### New Structure

```
src/
├── data/
│   ├── __init__.py
│   ├── loader.py          # Centralized data loader service
│   ├── storage.py         # SQLite database operations
│   └── zoho.py           # Zoho Analytics integration
├── pricing/
│   ├── __init__.py
│   ├── service.py         # Pricing service (uses DataLoaderService)
│   ├── calculator.py      # Pricing calculations
│   ├── models.py          # Data models
│   ├── rules.py           # Configuration rules
│   ├── reasoning.py       # LLM reasoning
│   └── formatter.py       # Output formatting
├── config/
│   ├── __init__.py
│   └── rules.py           # Configuration management
├── utils/
│   ├── __init__.py
│   ├── parsing.py         # Safe parsing utilities
│   └── error_handler.py   # Error handling utilities
├── exceptions/
│   ├── __init__.py
│   └── pricing_exceptions.py # Exception hierarchy
├── api/
│   └── pricing_router.py  # API endpoints
├── webhooks/
│   └── google_chat_router.py # Google Chat webhook
├── cli.py                 # Main CLI wrapper
├── zoho_cli.py           # Zoho CLI operations
├── pricing_cli.py        # Pricing CLI operations
└── app.py                # Unified FastAPI application
```

### DataLoaderService Interface

```python
class DataLoaderService:
    def load_merged_pricing_data(
        self,
        target_date: Optional[str] = None,
        target_location: Optional[str] = None,
        auto_fetch: bool = True
    ) -> pd.DataFrame:
        """Load and merge data from both monthly expense and daily occupancy data."""

    def load_monthly_expense_data(
        self,
        target_year: int,
        target_month: int,
        location: Optional[str] = None
    ) -> pd.DataFrame:
        """Load monthly expense data for the last 3 months."""

    def load_daily_occupancy_data(
        self,
        target_date: str,
        location: Optional[str] = None,
        auto_fetch: bool = True
    ) -> pd.DataFrame:
        """Load daily occupancy data for the past 7 days."""
```

## Benefits

1. **Single Responsibility**: DataLoaderService has one reason to change - data loading operations
2. **Eliminates Duplication**: Removed ~150 lines of duplicated code
3. **Consistent Interface**: All data loading goes through the same service
4. **Better Testability**: Centralized logic is easier to test
5. **Backward Compatibility**: Existing functions remain as thin wrappers

## Changes Made

### 1. Created `src/data/loader.py`
- New `DataLoaderService` class
- Consolidated all data loading logic
- Proper error handling and logging
- Type hints for better code clarity

### 2. Moved and Reorganized Data Layer
- Moved `src/sqlite_storage.py` to `src/data/storage.py`
- Moved `src/zoho_integration.py` to `src/data/zoho.py`
- Created proper data layer package structure

### 3. Removed Legacy Files
- Removed `src/po_pricing_engine.py` (legacy wrapper)
- Removed `src/pricing_pipeline.py` (integrated into service layer)
- Removed `src/llm_reasoning.py` (moved to `src/pricing/reasoning.py`)

### 4. Extracted Configuration Management
- Created `src/config/rules.py` for configuration loading
- Moved `load_pricing_rules()` function from legacy files
- Centralized configuration management

### 5. Enhanced Service Layer
- Updated `src/pricing/service.py` to use `DataLoaderService`
- Integrated pipeline logic into service layer
- Improved data loading with proper date handling
- Better separation of concerns

### 6. Added Tests
- Created `tests/test_data_loader.py`
- Tests cover initialization, data loading, and edge cases
- All tests pass successfully

## Usage Examples

### Direct Usage
```python
from src.data.loader import DataLoaderService

data_loader = DataLoaderService()
df = data_loader.load_merged_pricing_data(
    target_date="2024-01-15",
    target_location="Pacific Place",
    auto_fetch=True
)
```

### Service Layer Usage
```python
from src.pricing.service import get_pricing_service

pricing_service = get_pricing_service()
outputs = pricing_service.run_pricing_pipeline(
    target_date="2024-01-15",
    target_location="Pacific Place",
    verbose=True
)
```

### CLI Usage
```bash
# Run pricing pipeline for all locations
python3 src/pricing_cli.py run-pipeline

# Run for specific location with verbose output
python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --verbose

# Run for specific date
python3 src/pricing_cli.py run-pipeline --target-date 2024-01-15
```

## Testing

Run the tests to verify the refactoring:
```bash
cd /path/to/pricing-engine
source venv/bin/activate
PYTHONPATH=/path/to/pricing-engine python3 -m unittest tests.test_data_loader -v
```

## Verification

The refactoring has been verified to work correctly:
- ✅ All tests pass
- ✅ CLI commands work as expected
- ✅ API imports successfully
- ✅ No breaking changes to existing functionality

## Recent Improvements

### Auto-Fetch Optimization (Latest)
- **Smart Fetching**: Auto-fetch now only fetches from Zoho if data doesn't already exist in SQLite
- **Performance**: Eliminates unnecessary API calls when data is already available
- **User Feedback**: Clear messages indicate when data exists vs. when fetching is needed

## Future Improvements

1. **Dependency Injection**: Consider injecting the DataLoaderService into other classes
2. **Caching**: Add caching layer for frequently accessed data
3. **Async Support**: Consider async data loading for better performance
4. **Configuration**: Move hardcoded values to configuration files
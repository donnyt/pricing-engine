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
│   └── loader.py          # New centralized data loader
├── po_pricing_engine.py   # Updated to use DataLoaderService
├── pricing_pipeline.py    # Updated to use DataLoaderService
└── pricing/
    └── service.py         # Updated to use DataLoaderService
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

### 2. Updated `src/po_pricing_engine.py`
- `load_merged_pricing_data()` now uses `DataLoaderService`
- Maintains backward compatibility
- Reduced from ~150 lines to ~10 lines

### 3. Updated `src/pricing_pipeline.py`
- Removed duplicate `load_merged_pricing_data_simple()` function
- Updated to use `DataLoaderService` directly
- Simplified data loading logic

### 4. Updated `src/pricing/service.py`
- Updated `PricingService` to use `DataLoaderService`
- Improved data loading with proper date handling
- Better separation of concerns

### 5. Added Tests
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

### Backward Compatible Usage
```python
from src.po_pricing_engine import load_merged_pricing_data

df = load_merged_pricing_data("2024-01-15", "Pacific Place")
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
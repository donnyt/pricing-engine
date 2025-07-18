# Error Handling Strategy for Pricing Engine

## Overview

This document outlines the centralized error handling strategy implemented for the pricing engine, following Clean Code principles and SOLID design patterns.

## Problem Statement

The original codebase had several issues with error handling:

1. **Inconsistent Error Handling**: Different modules used different approaches
2. **Bare Exception Handling**: Many `except Exception` blocks that swallowed all errors
3. **Poor Error Context**: Missing information about what operation failed
4. **No Error Classification**: All errors treated the same way
5. **Poor Error Recovery**: Most errors just printed and continued

## Solution: Centralized Error Handling

### 1. Exception Hierarchy

We've created a comprehensive exception hierarchy in `src/exceptions/pricing_exceptions.py`:

```python
PricingEngineException (base)
├── DataNotFoundException
├── ConfigurationException
├── DataValidationException
├── ExternalServiceException
├── CalculationException
├── DatabaseException
├── LLMServiceException
└── ParsingException
```

### 2. Error Context

Each exception can carry rich context information:

```python
@dataclass
class ErrorContext:
    operation: str
    location: Optional[str] = None
    data_source: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
```

### 3. Error Handling Utilities

The `src/utils/error_handler.py` module provides:

#### Decorator Pattern
```python
@handle_errors(
    operation="pricing_calculation",
    location="Pacific Place",
    default_return=None,
    log_level=logging.ERROR,
    reraise=False
)
def calculate_pricing(location_data):
    # Function implementation
    pass
```

#### Context Manager
```python
with error_boundary("database_operation", "Pacific Place", "SQLite"):
    # Database operations
    pass
```

#### Safe Parsing
```python
parsed_value = safe_parse(
    parse_func=parse_float,
    value="123.45",
    data_type="float",
    context=error_context,
    default=0.0
)
```

## Usage Examples

### 1. Function-Level Error Handling

```python
from src.utils.error_handler import handle_errors
from src.exceptions import DataNotFoundException

@handle_errors(
    operation="load_location_data",
    default_return=pd.DataFrame(),
    reraise=False
)
def load_location_data(location: str) -> pd.DataFrame:
    # Implementation with specific exceptions
    if not data_exists(location):
        raise DataNotFoundException("location_data", location)
    return fetch_data(location)
```

### 2. Context Manager for Operations

```python
from src.utils.error_handler import error_boundary

def process_location(location: str):
    with error_boundary("process_location", location, "pricing_pipeline"):
        # All operations within this block are handled consistently
        data = load_data(location)
        result = calculate_pricing(data)
        save_result(result)
```

### 3. Safe Data Parsing

```python
from src.utils.error_handler import safe_parse, create_error_context

def parse_location_data(row):
    context = create_error_context("parse_location_data", row.get("location"))

    occupancy = safe_parse(
        parse_pct,
        row.get("occupancy"),
        "occupancy_percentage",
        context
    )

    seats = safe_parse(
        parse_int,
        row.get("seats"),
        "seat_count",
        context
    )

    return occupancy, seats
```

### 4. Validation with Context

```python
from src.utils.error_handler import validate_required_field

def validate_location_data(data):
    context = create_error_context("validate_location_data")

    validate_required_field(data.get("name"), "location_name", context)
    validate_required_field(data.get("seats"), "total_seats", context)
    validate_required_field(data.get("occupancy"), "occupancy_rate", context)
```

## Benefits

### 1. **Consistent Error Reporting**
- All errors follow the same format
- Rich context information for debugging
- Proper logging levels

### 2. **Better Error Recovery**
- Graceful degradation for non-critical errors
- Clear error boundaries
- Configurable error handling strategies

### 3. **Improved Debugging**
- Detailed error context
- Operation tracking
- Data source identification

### 4. **Clean Code Principles**
- Single Responsibility: Each exception type has one purpose
- Open/Closed: Easy to extend with new exception types
- Dependency Inversion: Depend on abstractions, not concretions

## Migration Guide

### Before (Old Pattern)
```python
try:
    result = some_operation(data)
except Exception as e:
    print(f"Error: {e}")
    return None
```

### After (New Pattern)
```python
from src.utils.error_handler import handle_errors

@handle_errors(
    operation="some_operation",
    default_return=None,
    reraise=False
)
def some_operation(data):
    # Implementation with specific exceptions
    pass
```

### Or Using Context Manager
```python
from src.utils.error_handler import error_boundary

with error_boundary("some_operation", reraise=False):
    result = some_operation(data)
```

## Best Practices

### 1. **Use Specific Exceptions**
```python
# Good
raise DataNotFoundException("location_data", location)

# Avoid
raise Exception("Data not found")
```

### 2. **Provide Rich Context**
```python
context = create_error_context(
    operation="calculate_pricing",
    location="Pacific Place",
    data_source="daily_occupancy",
    additional_info={"target_date": "2024-01-15"}
)
```

### 3. **Handle Errors at Appropriate Levels**
- Use `reraise=True` for critical errors that should stop execution
- Use `reraise=False` for non-critical errors that allow continuation
- Use `log_and_continue` for warnings that don't affect functionality

### 4. **Validate Input Data**
```python
validate_required_field(data.get("field"), "field_name", context)
```

### 5. **Use Safe Parsing for External Data**
```python
parsed_value = safe_parse(parse_func, raw_value, "data_type", context)
```

## Testing

The error handling system is designed to be testable:

```python
def test_error_handling():
    with pytest.raises(DataNotFoundException) as exc_info:
        load_nonexistent_data()

    assert exc_info.value.context.operation == "load_data"
    assert exc_info.value.context.location == "test_location"
```

## Monitoring and Logging

All errors are logged with appropriate levels:
- `ERROR`: Critical errors that affect functionality
- `WARNING`: Non-critical errors that allow continuation
- `INFO`: Informational messages about error recovery

The logging includes:
- Error type and message
- Operation context
- Location and data source
- Additional debugging information

## Future Enhancements

1. **Error Metrics**: Track error rates by type and location
2. **Error Recovery Strategies**: Automatic retry mechanisms
3. **Error Reporting**: Integration with external monitoring systems
4. **Error Documentation**: Auto-generated error documentation
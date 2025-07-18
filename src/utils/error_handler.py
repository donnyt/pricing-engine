"""
Centralized Error Handling Utilities

This module provides consistent error handling patterns and recovery strategies
for the pricing engine, following the Single Responsibility Principle.
"""

import logging
from typing import Optional, Callable, Any, TypeVar, Union
from functools import wraps
from contextlib import contextmanager

from src.exceptions.pricing_exceptions import (
    PricingEngineException,
    ErrorContext,
    DataNotFoundException,
    ConfigurationException,
    DataValidationException,
    ExternalServiceException,
    CalculationException,
    DatabaseException,
    LLMServiceException,
    ParsingException,
)

# Type variable for return type
T = TypeVar("T")

# Configure logging
logger = logging.getLogger(__name__)


def handle_errors(
    operation: str,
    location: Optional[str] = None,
    data_source: Optional[str] = None,
    default_return: Optional[Any] = None,
    log_level: int = logging.ERROR,
    reraise: bool = False,
) -> Callable:
    """
    Decorator for consistent error handling with context.

    Args:
        operation: Name of the operation being performed
        location: Optional location identifier
        data_source: Optional data source identifier
        default_return: Value to return on error (if not re-raising)
        log_level: Logging level for errors
        reraise: Whether to re-raise the exception after logging

    Returns:
        Decorated function with error handling
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Union[T, Any]:
            context = ErrorContext(
                operation=operation,
                location=location,
                data_source=data_source,
                additional_info={
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                },
            )

            try:
                return func(*args, **kwargs)
            except PricingEngineException as e:
                # Re-use existing context if available
                if not e.context:
                    e.context = context
                logger.log(log_level, f"Pricing engine error: {e}")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                # Convert generic exceptions to pricing engine exceptions
                logger.log(log_level, f"Unexpected error in {operation}: {e}")
                if reraise:
                    raise PricingEngineException(f"Unexpected error: {str(e)}", context)
                return default_return

        return wrapper

    return decorator


@contextmanager
def error_boundary(
    operation: str,
    location: Optional[str] = None,
    data_source: Optional[str] = None,
    log_level: int = logging.ERROR,
    reraise: bool = True,
):
    """
    Context manager for error handling with automatic cleanup.

    Args:
        operation: Name of the operation being performed
        location: Optional location identifier
        data_source: Optional data source identifier
        log_level: Logging level for errors
        reraise: Whether to re-raise the exception after logging
    """
    context = ErrorContext(
        operation=operation, location=location, data_source=data_source
    )

    try:
        yield
    except PricingEngineException as e:
        if not e.context:
            e.context = context
        logger.log(log_level, f"Pricing engine error: {e}")
        if reraise:
            raise
    except Exception as e:
        logger.log(log_level, f"Unexpected error in {operation}: {e}")
        if reraise:
            raise PricingEngineException(f"Unexpected error: {str(e)}", context)


def safe_parse(
    parse_func: Callable[[Any], T],
    value: Any,
    data_type: str,
    context: Optional[ErrorContext] = None,
    default: Optional[T] = None,
) -> Optional[T]:
    """
    Safely parse a value with proper error handling.

    Args:
        parse_func: Function to parse the value
        value: Value to parse
        data_type: Type description for error messages
        context: Error context
        default: Default value to return on parsing failure

    Returns:
        Parsed value or default
    """
    try:
        return parse_func(value)
    except Exception as e:
        if context:
            raise ParsingException(data_type, value, str(e), context)
        logger.warning(f"Failed to parse {data_type} from '{value}': {e}")
        return default


def validate_required_field(
    value: Any,
    field_name: str,
    context: Optional[ErrorContext] = None,
) -> None:
    """
    Validate that a required field has a value.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        context: Error context

    Raises:
        DataValidationException: If field is None, empty, or invalid
    """
    if value is None:
        raise DataValidationException(
            field_name, value, "Field is required but is None", context
        )

    if isinstance(value, str) and not value.strip():
        raise DataValidationException(
            field_name, value, "Field is required but is empty", context
        )

    if isinstance(value, (list, dict)) and len(value) == 0:
        raise DataValidationException(
            field_name, value, "Field is required but is empty", context
        )


def log_and_continue(
    error: Exception,
    operation: str,
    location: Optional[str] = None,
    log_level: int = logging.WARNING,
) -> None:
    """
    Log an error and continue execution (for non-critical errors).

    Args:
        error: The exception that occurred
        operation: Name of the operation that failed
        location: Optional location identifier
        log_level: Logging level for the error
    """
    context = ErrorContext(operation=operation, location=location)

    if isinstance(error, PricingEngineException):
        if not error.context:
            error.context = context
        logger.log(log_level, f"Non-critical error: {error}")
    else:
        logger.log(log_level, f"Non-critical error in {operation}: {error}")


def create_error_context(
    operation: str,
    location: Optional[str] = None,
    data_source: Optional[str] = None,
    **additional_info: Any,
) -> ErrorContext:
    """
    Create an error context with additional information.

    Args:
        operation: Name of the operation
        location: Optional location identifier
        data_source: Optional data source identifier
        **additional_info: Additional context information

    Returns:
        ErrorContext instance
    """
    return ErrorContext(
        operation=operation,
        location=location,
        data_source=data_source,
        additional_info=additional_info,
    )

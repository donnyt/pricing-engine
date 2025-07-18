"""
Centralized Exception Hierarchy for Pricing Engine

This module provides a comprehensive exception hierarchy for the pricing engine,
following the Single Responsibility Principle and enabling better error handling
and recovery strategies.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ErrorContext:
    """Context information for error reporting and debugging."""

    operation: str
    location: Optional[str] = None
    data_source: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class PricingEngineException(Exception):
    """Base exception for all pricing engine errors."""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.context = context or ErrorContext(operation="unknown")

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.context:
            return f"{base_msg} (Operation: {self.context.operation}, Location: {self.context.location or 'N/A'})"
        return base_msg


class DataNotFoundException(PricingEngineException):
    """Raised when required data is not found."""

    def __init__(
        self, data_type: str, identifier: str, context: Optional[ErrorContext] = None
    ):
        message = f"Data not found: {data_type} with identifier '{identifier}'"
        super().__init__(message, context)


class ConfigurationException(PricingEngineException):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self, config_key: str, reason: str, context: Optional[ErrorContext] = None
    ):
        message = f"Configuration error for '{config_key}': {reason}"
        super().__init__(message, context)


class DataValidationException(PricingEngineException):
    """Raised when data validation fails."""

    def __init__(
        self,
        field: str,
        value: Any,
        reason: str,
        context: Optional[ErrorContext] = None,
    ):
        message = (
            f"Data validation failed for field '{field}' with value '{value}': {reason}"
        )
        super().__init__(message, context)


class ExternalServiceException(PricingEngineException):
    """Raised when external service calls fail."""

    def __init__(
        self,
        service: str,
        operation: str,
        error: str,
        context: Optional[ErrorContext] = None,
    ):
        message = f"External service '{service}' failed during '{operation}': {error}"
        super().__init__(message, context)


class CalculationException(PricingEngineException):
    """Raised when pricing calculations fail."""

    def __init__(
        self, calculation_step: str, reason: str, context: Optional[ErrorContext] = None
    ):
        message = f"Calculation failed at step '{calculation_step}': {reason}"
        super().__init__(message, context)


class DatabaseException(PricingEngineException):
    """Raised when database operations fail."""

    def __init__(
        self,
        operation: str,
        table: str,
        error: str,
        context: Optional[ErrorContext] = None,
    ):
        message = f"Database operation '{operation}' on table '{table}' failed: {error}"
        super().__init__(message, context)


class LLMServiceException(PricingEngineException):
    """Raised when LLM service calls fail."""

    def __init__(
        self, operation: str, error: str, context: Optional[ErrorContext] = None
    ):
        message = f"LLM service failed during '{operation}': {error}"
        super().__init__(message, context)


class ParsingException(PricingEngineException):
    """Raised when data parsing fails."""

    def __init__(
        self,
        data_type: str,
        value: Any,
        reason: str,
        context: Optional[ErrorContext] = None,
    ):
        message = f"Failed to parse {data_type} from '{value}': {reason}"
        super().__init__(message, context)

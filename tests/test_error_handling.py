"""
Tests for the centralized error handling system.
"""

import pytest
import logging
from unittest.mock import patch

from src.exceptions import (
    PricingEngineException,
    DataNotFoundException,
    ConfigurationException,
    DataValidationException,
    ParsingException,
    ErrorContext,
)
from src.utils.error_handler import (
    handle_errors,
    error_boundary,
    safe_parse,
    validate_required_field,
    log_and_continue,
    create_error_context,
)
from src.utils.parsing import parse_float, parse_int, parse_pct


class TestErrorContext:
    """Test ErrorContext functionality."""

    def test_error_context_creation(self):
        """Test creating error context with various parameters."""
        context = create_error_context(
            operation="test_operation",
            location="test_location",
            data_source="test_source",
            additional_info={"key": "value"},
        )

        assert context.operation == "test_operation"
        assert context.location == "test_location"
        assert context.data_source == "test_source"
        assert context.additional_info["key"] == "value"

    def test_error_context_defaults(self):
        """Test error context with default values."""
        context = create_error_context("test_operation")

        assert context.operation == "test_operation"
        assert context.location is None
        assert context.data_source is None
        assert context.additional_info is None


class TestExceptionHierarchy:
    """Test the exception hierarchy."""

    def test_base_exception_inheritance(self):
        """Test that all exceptions inherit from PricingEngineException."""
        exceptions = [
            DataNotFoundException("test", "test"),
            ConfigurationException("test", "test"),
            DataValidationException("test", "test", "test"),
            ParsingException("test", "test", "test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, PricingEngineException)

    def test_exception_with_context(self):
        """Test exception creation with context."""
        context = create_error_context("test_operation", "test_location")
        exc = DataNotFoundException("test_data", "test_id", context)

        assert exc.context == context
        assert "test_operation" in str(exc)
        assert "test_location" in str(exc)


class TestSafeParse:
    """Test safe parsing functionality."""

    def test_safe_parse_success(self):
        """Test successful parsing."""
        result = safe_parse(parse_float, "123.45", "float")
        assert result == 123.45

    def test_safe_parse_failure_with_default(self):
        """Test parsing failure with default value."""
        result = safe_parse(parse_float, "invalid", "float", default=0.0)
        assert result == 0.0

    def test_safe_parse_failure_with_context(self):
        """Test parsing failure with context raises exception."""
        context = create_error_context("test_parse")

        with pytest.raises(ParsingException) as exc_info:
            safe_parse(parse_float, "invalid", "float", context)

        assert exc_info.value.context == context
        assert "float" in str(exc_info.value)


class TestValidation:
    """Test validation functionality."""

    def test_validate_required_field_success(self):
        """Test successful validation."""
        validate_required_field("valid_value", "test_field")
        # Should not raise any exception

    def test_validate_required_field_none(self):
        """Test validation failure with None value."""
        context = create_error_context("test_validation")

        with pytest.raises(DataValidationException) as exc_info:
            validate_required_field(None, "test_field", context)

        assert exc_info.value.context == context
        assert "test_field" in str(exc_info.value)

    def test_validate_required_field_empty_string(self):
        """Test validation failure with empty string."""
        with pytest.raises(DataValidationException):
            validate_required_field("", "test_field")

    def test_validate_required_field_empty_list(self):
        """Test validation failure with empty list."""
        with pytest.raises(DataValidationException):
            validate_required_field([], "test_field")


class TestErrorHandlingDecorator:
    """Test the handle_errors decorator."""

    @handle_errors(operation="test_function", default_return="default", reraise=False)
    def test_function_success(self):
        """Test function that succeeds."""
        return "success"

    @handle_errors(
        operation="test_function_failure", default_return="default", reraise=False
    )
    def test_function_failure(self):
        """Test function that raises an exception."""
        raise ValueError("test error")

    def test_decorator_success(self):
        """Test decorator with successful function."""
        result = self.test_function_success()
        assert result == "success"

    def test_decorator_failure(self):
        """Test decorator with failing function."""
        result = self.test_function_failure()
        assert result == "default"

    @handle_errors(operation="test_function_reraise", reraise=True)
    def test_function_reraise(self):
        """Test function that raises an exception with reraise=True."""
        raise ValueError("test error")

    def test_decorator_reraise(self):
        """Test decorator with reraise=True."""
        with pytest.raises(PricingEngineException):
            self.test_function_reraise()


class TestErrorBoundary:
    """Test the error_boundary context manager."""

    def test_error_boundary_success(self):
        """Test error boundary with successful operation."""
        with error_boundary("test_operation", reraise=False):
            result = "success"

        assert result == "success"

    def test_error_boundary_failure_no_reraise(self):
        """Test error boundary with failure and no reraise."""
        with error_boundary("test_operation", reraise=False):
            raise ValueError("test error")

        # Should not raise exception

    def test_error_boundary_failure_with_reraise(self):
        """Test error boundary with failure and reraise."""
        with pytest.raises(PricingEngineException):
            with error_boundary("test_operation", reraise=True):
                raise ValueError("test error")


class TestLogAndContinue:
    """Test log_and_continue functionality."""

    @patch("src.utils.error_handler.logger")
    def test_log_and_continue(self, mock_logger):
        """Test log_and_continue function."""
        error = ValueError("test error")
        log_and_continue(error, "test_operation", "test_location")

        # Verify that logger was called
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.WARNING  # Default log level
        assert "test_operation" in call_args[0][1]


class TestIntegration:
    """Integration tests for error handling."""

    def test_parsing_with_error_context(self):
        """Test parsing functions with error context."""
        context = create_error_context("test_integration")

        # Test successful parsing
        result = parse_float("123.45", context=context)
        assert result == 123.45

        # Test parsing with invalid data (should return default)
        result = parse_int("invalid", context=context)
        assert result == 0

        # Test percentage parsing
        result = parse_pct("75%", context=context)
        assert result == 75.0

    def test_error_handling_in_pipeline_context(self):
        """Test error handling in a pipeline-like context."""
        results = []

        test_data = [
            ("valid", "123.45"),
            ("invalid", "not_a_number"),
            ("valid", "67.89"),
        ]

        for name, value in test_data:
            with error_boundary(f"process_{name}", name, reraise=False):
                parsed = safe_parse(parse_float, value, "float", default=0.0)
                results.append(parsed)

        assert results == [123.45, 0.0, 67.89]

"""
Enhanced error management with centralized logging and structured error handling.
"""

from typing import Any

from src.agentic_crypto_influencer.config.logging_config import LoggerMixin
from src.agentic_crypto_influencer.error_management.exceptions import (
    AgenticCryptoError,
    APIConnectionError,
    APITimeoutError,
    ConfigurationError,
    ValidationError,
)
from src.agentic_crypto_influencer.error_management.retry import retry_manager


class ErrorManager(LoggerMixin):
    """
    Centralized error management with structured logging and context preservation.
    """

    def __init__(self) -> None:
        """Initialize the error manager."""
        self.logger.info("ErrorManager initialized")

    def handle_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> str:
        """
        Handle errors with structured logging and user-friendly messages.

        Args:
            error: The exception that occurred
            context: Additional context information
            user_message: Custom user-friendly message

        Returns:
            User-friendly error message
        """
        # Default user message
        if user_message is None:
            user_message = "An unexpected error occurred. Please try again later."

        # Prepare context for logging
        error_context: dict[str, Any] = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        if context:
            error_context.update(context)

        # Log with full context and traceback
        self.logger.error(
            f"Error handled: {type(error).__name__}: {error!s}",
            exc_info=True,
            extra=error_context,
        )

        return user_message

    def handle_api_error(
        self,
        error: Exception,
        service: str,
        endpoint: str,
        status_code: int | None = None,
    ) -> str:
        """
        Handle API-specific errors with service context.

        Args:
            error: The exception that occurred
            service: Service name (e.g., "x_api", "google_api")
            endpoint: API endpoint that failed
            status_code: HTTP status code if available

        Returns:
            User-friendly error message
        """
        context: dict[str, Any] = {
            "service": service,
            "endpoint": endpoint,
            "status_code": status_code,
        }

        user_message = f"Service temporarily unavailable ({service}). Please try again later."
        return self.handle_error(error, context, user_message)

    def handle_connection_error(
        self,
        error: Exception,
        service: str,
        retry_count: int = 0,
    ) -> str:
        """
        Handle connection errors with retry context.

        Args:
            error: The connection exception
            service: Service that failed to connect
            retry_count: Number of retries attempted

        Returns:
            User-friendly error message
        """
        context: dict[str, Any] = {
            "service": service,
            "retry_count": retry_count,
            "error_category": "connection",
        }

        user_message = f"Unable to connect to {service}. Please check your connection."
        return self.handle_error(error, context, user_message)

    def handle_validation_error(
        self,
        error: Exception,
        field: str,
        value: Any,
    ) -> str:
        """
        Handle validation errors with field context.

        Args:
            error: The validation exception
            field: Field that failed validation
            value: Value that failed validation (truncated for logging)

        Returns:
            User-friendly error message
        """
        context: dict[str, Any] = {
            "field": field,
            "value": str(value)[:100],  # Truncate long values
            "error_category": "validation",
        }

        user_message = f"Invalid {field}. Please check your input and try again."
        return self.handle_error(error, context, user_message)

    def handle_configuration_error(
        self,
        error: Exception,
        config_name: str,
        expected_type: str | None = None,
    ) -> str:
        """
        Handle configuration errors with context.

        Args:
            error: The configuration exception
            config_name: Name of the configuration that failed
            expected_type: Expected type/format of configuration

        Returns:
            User-friendly error message
        """
        context: dict[str, Any] = {
            "config_name": config_name,
            "expected_type": expected_type,
            "error_category": "configuration",
        }

        user_message = f"Configuration error: {config_name}. Please check your settings."
        return self.handle_error(error, context, user_message)

    def handle_workflow_error(
        self,
        error: Exception,
        workflow_step: str,
        step_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Handle workflow execution errors with step context.

        Args:
            error: The workflow exception
            workflow_step: Current workflow step that failed
            step_data: Data associated with the failing step

        Returns:
            User-friendly error message
        """
        context: dict[str, Any] = {
            "workflow_step": workflow_step,
            "error_category": "workflow",
        }
        if step_data:
            context["step_data"] = step_data

        user_message = f"Workflow failed at step: {workflow_step}. Please try again."
        return self.handle_error(error, context, user_message)

    def handle_data_processing_error(
        self,
        error: Exception,
        data_type: str,
        operation: str,
        data_size: int | None = None,
    ) -> str:
        """
        Handle data processing errors with context.

        Args:
            error: The data processing exception
            data_type: Type of data being processed
            operation: Operation that failed
            data_size: Size of data being processed

        Returns:
            User-friendly error message
        """
        context: dict[str, Any] = {
            "data_type": data_type,
            "operation": operation,
            "error_category": "data_processing",
        }
        if data_size is not None:
            context["data_size"] = data_size

        user_message = f"Failed to process {data_type}. Please try again with different data."
        return self.handle_error(error, context, user_message)

    def create_specific_error(self, error: Exception, **kwargs: Any) -> AgenticCryptoError:
        """
        Convert generic exceptions to specific application exceptions.

        Args:
            error: The original exception
            **kwargs: Additional context for the specific error

        Returns:
            Specific application exception
        """
        # Map common exceptions to specific types
        if isinstance(error, ConnectionError):
            return APIConnectionError(
                message=str(error),
                service=kwargs.get("service", "unknown"),
                endpoint=kwargs.get("endpoint", "unknown"),
                context=kwargs,
            )
        elif isinstance(error, TimeoutError):
            return APITimeoutError(
                message=str(error),
                service=kwargs.get("service", "unknown"),
                endpoint=kwargs.get("endpoint", "unknown"),
                timeout=kwargs.get("timeout", 30.0),
                context=kwargs,
            )
        elif isinstance(error, ValueError) and "validation" in str(error).lower():
            return ValidationError(
                message=str(error),
                field=kwargs.get("field", "unknown"),
                value=kwargs.get("value", ""),
                context=kwargs,
            )
        elif isinstance(error, KeyError) and "config" in str(error).lower():
            return ConfigurationError(
                message=str(error),
                missing_config=kwargs.get("config_name"),
                context=kwargs,
            )
        else:
            # Return as generic AgenticCryptoError for unknown types
            return AgenticCryptoError(
                message=str(error),
                error_code="UNKNOWN_ERROR",
                context=kwargs,
            )

    def get_circuit_breaker_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all circuit breakers."""
        service_status = retry_manager.get_service_status()
        return {"circuit_breakers": service_status}

    def call_with_circuit_breaker(
        self,
        service: str,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            service: Service name for circuit breaker
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            APIConnectionError: If circuit breaker is open
        """
        try:
            return retry_manager.call_with_circuit_breaker(service, func, *args, **kwargs)
        except Exception as e:
            # Log circuit breaker failures
            context: dict[str, Any] = {
                "service": service,
                "function": func.__name__ if hasattr(func, "__name__") else str(func),
                "circuit_breaker_status": retry_manager.get_service_status().get(service, {}),
            }
            self.handle_error(e, context)
            # Re-raise the original exception for proper error propagation
            raise


def main() -> None:
    """Main function that demonstrates error handling."""
    # Initialize logging first
    from src.agentic_crypto_influencer.config.logging_config import setup_logging

    setup_logging()

    error_manager = ErrorManager()

    try:
        raise ValueError("Sample error message")
    except Exception as e:
        user_message = error_manager.handle_error(
            e,
            context={"demo": True, "function": "main"},
            user_message="This is a demo error for testing.",
        )
        # In a real application, this would be returned to the user, not printed
        error_manager.logger.info(f"User received message: {user_message}")


if __name__ == "__main__":
    main()

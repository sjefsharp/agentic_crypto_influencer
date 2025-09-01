"""
Enhanced error management with centralized logging and structured error handling.
"""

from typing import Any, Dict, Optional

from src.agentic_crypto_influencer.config.logging_config import LoggerMixin


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
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
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
        error_context: Dict[str, Any] = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        if context:
            error_context.update(context)
        
        # Log with full context and traceback
        self.logger.error(
            f"Error handled: {type(error).__name__}: {str(error)}",
            exc_info=True,
            extra=error_context,
        )
        
        return user_message
    
    def handle_api_error(
        self,
        error: Exception,
        service: str,
        endpoint: str,
        status_code: Optional[int] = None,
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
        context: Dict[str, Any] = {
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
        context: Dict[str, Any] = {
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
        context: Dict[str, Any] = {
            "field": field,
            "value": str(value)[:100],  # Truncate long values
            "error_category": "validation",
        }
        
        user_message = f"Invalid {field}. Please check your input and try again."
        return self.handle_error(error, context, user_message)


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
            user_message="This is a demo error for testing."
        )
        # In a real application, this would be returned to the user, not printed
        error_manager.logger.info(f"User received message: {user_message}")


if __name__ == "__main__":
    main()

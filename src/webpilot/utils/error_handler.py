"""
Comprehensive error handling for WebPilot.

This module provides error handling utilities including retry logic,
error recovery, and detailed error reporting.
"""

import functools
import time
import traceback
from typing import Any, Callable, Optional, Type, TypeVar, Union, List
from datetime import datetime
import logging

from webpilot.utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class ErrorContext:
    """Context information for error handling."""
    
    def __init__(
        self,
        operation: str,
        details: Optional[dict] = None,
        user_message: Optional[str] = None
    ):
        """
        Initialize error context.
        
        Args:
            operation: Name of the operation that failed
            details: Additional details about the error
            user_message: User-friendly error message
        """
        self.operation = operation
        self.details = details or {}
        self.user_message = user_message
        self.timestamp = datetime.now()
        self.traceback = None
        
    def capture_traceback(self) -> None:
        """Capture the current traceback."""
        self.traceback = traceback.format_exc()
        
    def to_dict(self) -> dict:
        """Convert context to dictionary."""
        return {
            'operation': self.operation,
            'details': self.details,
            'user_message': self.user_message,
            'timestamp': self.timestamp.isoformat(),
            'traceback': self.traceback
        }


class ErrorHandler:
    """Central error handler for WebPilot."""
    
    def __init__(self):
        """Initialize error handler."""
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies = {}
        
    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        raise_error: bool = True
    ) -> Optional[Any]:
        """
        Handle an error with context.
        
        Args:
            error: The exception that occurred
            context: Error context information
            raise_error: Whether to re-raise the error
            
        Returns:
            Recovery result if available, None otherwise
            
        Raises:
            The original error if raise_error is True
        """
        # Capture traceback
        context.capture_traceback()
        
        # Log the error
        logger.error(
            f"Error in {context.operation}: {error}",
            extra={'error_context': context.to_dict()}
        )
        
        # Store in history
        self.error_history.append(context)
        
        # Try recovery strategy if available
        strategy = self.recovery_strategies.get(type(error))
        if strategy:
            try:
                result = strategy(error, context)
                logger.info(f"Recovery successful for {context.operation}")
                return result
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")
        
        # Re-raise if requested
        if raise_error:
            raise
            
        return None
    
    def register_recovery_strategy(
        self,
        error_type: Type[Exception],
        strategy: Callable[[Exception, ErrorContext], Any]
    ) -> None:
        """
        Register a recovery strategy for an error type.
        
        Args:
            error_type: Type of exception to handle
            strategy: Recovery function to call
        """
        self.recovery_strategies[error_type] = strategy
        
    def get_error_report(self) -> dict:
        """
        Get a report of all errors.
        
        Returns:
            Dictionary containing error statistics and history
        """
        error_types = {}
        for ctx in self.error_history:
            op = ctx.operation
            error_types[op] = error_types.get(op, 0) + 1
            
        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'recent_errors': [
                ctx.to_dict() for ctx in self.error_history[-10:]
            ]
        }


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
        on_retry: Optional callback function called on retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Max retries ({max_attempts}) exceeded for {func.__name__}"
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}"
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
                    
            return None  # Should never reach here
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable[..., T],
    default: Optional[T] = None,
    context: Optional[ErrorContext] = None,
    log_errors: bool = True
) -> Union[T, None]:
    """
    Safely execute a function and return default on error.
    
    Args:
        func: Function to execute
        default: Default value to return on error
        context: Optional error context
        log_errors: Whether to log errors
        
    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            operation = context.operation if context else func.__name__
            logger.error(f"Safe execution failed for {operation}: {e}")
        return default


def validate_input(
    value: Any,
    expected_type: Type,
    name: str,
    allow_none: bool = False,
    validator: Optional[Callable[[Any], bool]] = None
) -> Any:
    """
    Validate input parameters.
    
    Args:
        value: Value to validate
        expected_type: Expected type of the value
        name: Name of the parameter (for error messages)
        allow_none: Whether None is allowed
        validator: Optional custom validation function
        
    Returns:
        The validated value
        
    Raises:
        TypeError: If type doesn't match
        ValueError: If validation fails
    """
    if value is None:
        if allow_none:
            return value
        raise ValueError(f"{name} cannot be None")
    
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{name} must be {expected_type.__name__}, got {type(value).__name__}"
        )
    
    if validator and not validator(value):
        raise ValueError(f"{name} failed validation")
    
    return value


class ErrorAggregator:
    """Aggregate multiple errors for batch reporting."""
    
    def __init__(self):
        """Initialize error aggregator."""
        self.errors: List[tuple] = []
        
    def add_error(
        self,
        error: Exception,
        context: Optional[str] = None
    ) -> None:
        """
        Add an error to the aggregator.
        
        Args:
            error: The exception to add
            context: Optional context string
        """
        self.errors.append((error, context, datetime.now()))
        
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def raise_if_errors(self) -> None:
        """Raise an aggregate exception if there are errors."""
        if not self.has_errors():
            return
            
        error_messages = []
        for error, context, timestamp in self.errors:
            msg = f"[{timestamp.isoformat()}]"
            if context:
                msg += f" {context}:"
            msg += f" {error}"
            error_messages.append(msg)
        
        raise Exception(
            f"Multiple errors occurred ({len(self.errors)}):\n" +
            "\n".join(error_messages)
        )
    
    def clear(self) -> None:
        """Clear all errors."""
        self.errors = []
        
    def get_summary(self) -> dict:
        """Get error summary."""
        error_types = {}
        for error, _, _ in self.errors:
            error_type = type(error).__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
        return {
            'total': len(self.errors),
            'types': error_types,
            'errors': [
                {
                    'type': type(e).__name__,
                    'message': str(e),
                    'context': ctx,
                    'timestamp': ts.isoformat()
                }
                for e, ctx, ts in self.errors[-10:]  # Last 10 errors
            ]
        }


# Global error handler instance
error_handler = ErrorHandler()
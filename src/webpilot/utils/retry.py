#!/usr/bin/env python3
"""
Retry mechanism for flaky tests and operations.

Provides decorators and utilities for automatic retry with exponential backoff.
"""

import time
import functools
import random
from typing import Callable, Any, Optional, Type, Tuple, Union
import logging

logger = logging.getLogger(__name__)


def retry(
    times: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """
    Retry decorator with exponential backoff.
    
    Args:
        times: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on
        jitter: Add random jitter to prevent thundering herd
        on_retry: Callback function called on each retry with (exception, attempt_number)
    
    Example:
        @retry(times=3, delay=1, backoff=2)
        def flaky_test():
            element = pilot.click("#sometimes-there")
            
        @retry(exceptions=(ElementNotFoundError, TimeoutError))
        def specific_retry():
            pilot.wait_for_element("#dynamic-content")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == times - 1:
                        # Last attempt, re-raise
                        logger.error(f"Failed after {times} attempts: {e}")
                        raise
                    
                    # Calculate sleep time with optional jitter
                    sleep_time = current_delay
                    if jitter:
                        sleep_time += random.uniform(0, current_delay * 0.1)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{times} failed: {e}. "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(sleep_time)
                    current_delay *= backoff
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_with_result(
    predicate: Callable[[Any], bool],
    times: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
) -> Callable:
    """
    Retry decorator that checks the result with a predicate.
    
    Args:
        predicate: Function that returns True if result is acceptable
        times: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff: Multiplier for delay after each retry
    
    Example:
        @retry_with_result(lambda x: x is not None and x.success)
        def get_element():
            return pilot.find_element("#may-not-exist-yet")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            
            for attempt in range(times):
                result = func(*args, **kwargs)
                
                if predicate(result):
                    return result
                
                if attempt == times - 1:
                    logger.error(f"Result did not meet predicate after {times} attempts")
                    return result
                
                logger.warning(
                    f"Attempt {attempt + 1}/{times}: Result did not meet predicate. "
                    f"Retrying in {current_delay:.2f}s..."
                )
                
                time.sleep(current_delay)
                current_delay *= backoff
            
            return result
        return wrapper
    return decorator


class RetryableOperation:
    """
    Context manager for retryable operations.
    
    Example:
        with RetryableOperation(times=3) as retry:
            while retry.should_retry():
                try:
                    pilot.click("#flaky-button")
                    retry.success()
                except ElementNotFoundError:
                    retry.failed()
    """
    
    def __init__(
        self,
        times: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        jitter: bool = True
    ):
        self.times = times
        self.delay = delay
        self.backoff = backoff
        self.jitter = jitter
        self.attempt = 0
        self.current_delay = delay
        self._success = False
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not self._success:
            logger.error(f"Operation failed after {self.attempt} attempts: {exc_val}")
        return False
        
    def should_retry(self) -> bool:
        """Check if we should attempt the operation."""
        if self._success:
            return False
        if self.attempt >= self.times:
            return False
        if self.attempt > 0:
            # Sleep before retry
            sleep_time = self.current_delay
            if self.jitter:
                sleep_time += random.uniform(0, self.current_delay * 0.1)
            time.sleep(sleep_time)
            self.current_delay *= self.backoff
        self.attempt += 1
        return True
        
    def success(self):
        """Mark the operation as successful."""
        self._success = True
        
    def failed(self):
        """Mark the current attempt as failed."""
        logger.debug(f"Attempt {self.attempt} failed")


def with_retry(
    func: Callable,
    *args,
    times: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    **kwargs
) -> Any:
    """
    Execute a function with retry logic.
    
    Args:
        func: Function to execute
        *args: Positional arguments for func
        times: Number of retry attempts
        delay: Delay between retries
        exceptions: Exceptions to catch and retry
        **kwargs: Keyword arguments for func
    
    Returns:
        Result of func
        
    Example:
        result = with_retry(pilot.click, "#button", times=5, delay=0.5)
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(times):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt == times - 1:
                raise
            logger.warning(f"Attempt {attempt + 1}/{times} failed: {e}")
            time.sleep(current_delay)
            current_delay *= 2
    
    if last_exception:
        raise last_exception
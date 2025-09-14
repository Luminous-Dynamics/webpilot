"""
Enhanced error handling for MCP operations.

Provides detailed error messages and recovery suggestions.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import traceback
import logging


class ErrorCategory(Enum):
    """Categories of errors for better handling."""
    BROWSER = "browser_error"
    NETWORK = "network_error"
    ELEMENT = "element_not_found"
    TIMEOUT = "timeout"
    PERMISSION = "permission_denied"
    VALIDATION = "validation_error"
    RESOURCE = "resource_error"
    UNKNOWN = "unknown_error"


class MCPErrorHandler:
    """
    Intelligent error handler for MCP operations.
    
    Provides context-aware error messages and recovery suggestions.
    """
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an error with context and suggestions.
        
        Args:
            error: The exception that occurred
            context: Additional context about the operation
            
        Returns:
            Structured error response with recovery suggestions
        """
        error_type = type(error).__name__
        error_msg = str(error)
        category = self._categorize_error(error, error_msg)
        
        # Track error frequency
        self.error_counts[category] = self.error_counts.get(category, 0) + 1
        
        # Get recovery suggestions
        suggestions = self._get_recovery_suggestions(category, error_msg, context)
        
        # Build detailed error response
        response = {
            "success": False,
            "error": {
                "category": category.value,
                "type": error_type,
                "message": error_msg,
                "suggestions": suggestions,
                "context": context or {},
                "traceback": traceback.format_exc() if self.logger.level <= logging.DEBUG else None
            }
        }
        
        # Add retry information if applicable
        if self._should_retry(category):
            response["error"]["retry"] = {
                "should_retry": True,
                "wait_seconds": self._get_retry_wait(category),
                "max_attempts": 3
            }
        
        self.logger.error(f"MCP Error: {category.value} - {error_msg}")
        return response
    
    def _categorize_error(self, error: Exception, error_msg: str) -> ErrorCategory:
        """Categorize error for better handling."""
        error_type = type(error).__name__
        error_msg_lower = error_msg.lower()
        
        # Browser errors
        if "webdriver" in error_type.lower() or "browser" in error_msg_lower:
            return ErrorCategory.BROWSER
        
        # Network errors
        if any(word in error_msg_lower for word in ["connection", "network", "timeout", "dns"]):
            return ErrorCategory.NETWORK
        
        # Element not found
        if any(word in error_msg_lower for word in ["element", "selector", "xpath", "not found"]):
            return ErrorCategory.ELEMENT
        
        # Timeout
        if "timeout" in error_msg_lower:
            return ErrorCategory.TIMEOUT
        
        # Permission
        if any(word in error_msg_lower for word in ["permission", "denied", "access"]):
            return ErrorCategory.PERMISSION
        
        # Validation
        if any(word in error_msg_lower for word in ["invalid", "validation", "required"]):
            return ErrorCategory.VALIDATION
        
        return ErrorCategory.UNKNOWN
    
    def _get_recovery_suggestions(self, category: ErrorCategory, 
                                  error_msg: str, context: Dict[str, Any]) -> List[str]:
        """Get intelligent recovery suggestions based on error category."""
        suggestions = []
        
        if category == ErrorCategory.BROWSER:
            suggestions.extend([
                "Ensure browser driver (geckodriver/chromedriver) is installed",
                "Check if browser is installed on the system",
                "Try using a different browser (firefox/chrome)",
                "Restart the browser session with webpilot_close and webpilot_start"
            ])
            
        elif category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Check internet connection",
                "Verify the URL is correct and accessible",
                "Try increasing timeout values",
                "Check if the website requires VPN or specific network"
            ])
            
        elif category == ErrorCategory.ELEMENT:
            element = context.get("selector") if context else "element"
            suggestions.extend([
                f"Verify the selector '{element}' is correct",
                "Wait for the page to fully load with webpilot_wait",
                "Check if element is inside an iframe",
                "Try using a different selector strategy (CSS, XPath, text)",
                "Use webpilot_check_element_exists to verify element presence"
            ])
            
        elif category == ErrorCategory.TIMEOUT:
            suggestions.extend([
                "Increase the timeout duration",
                "Check if the page is loading slowly",
                "Verify network connection speed",
                "Try webpilot_wait before the operation"
            ])
            
        elif category == ErrorCategory.PERMISSION:
            suggestions.extend([
                "Check file/directory permissions",
                "Ensure WebPilot has necessary system permissions",
                "Try running with appropriate privileges",
                "Check browser security settings"
            ])
            
        elif category == ErrorCategory.VALIDATION:
            suggestions.extend([
                "Check the input parameters format",
                "Verify required fields are provided",
                "Ensure data types match expected format",
                "Review the tool documentation for correct usage"
            ])
            
        else:
            suggestions.extend([
                "Check the error message for details",
                "Review recent changes to the code",
                "Ensure all dependencies are installed",
                "Try restarting the browser session"
            ])
        
        # Add context-specific suggestions
        if context:
            if context.get("url") and "404" in error_msg:
                suggestions.insert(0, "The page was not found (404). Check if URL is correct.")
            elif context.get("headless") and category == ErrorCategory.BROWSER:
                suggestions.insert(0, "Try disabling headless mode for debugging.")
        
        return suggestions
    
    def _should_retry(self, category: ErrorCategory) -> bool:
        """Determine if the operation should be retried."""
        retryable = [
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.ELEMENT  # Element might appear after retry
        ]
        return category in retryable
    
    def _get_retry_wait(self, category: ErrorCategory) -> int:
        """Get wait time before retry based on error category."""
        wait_times = {
            ErrorCategory.NETWORK: 5,
            ErrorCategory.TIMEOUT: 3,
            ErrorCategory.ELEMENT: 2,
        }
        return wait_times.get(category, 1)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors encountered."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "by_category": dict(self.error_counts),
            "most_common": max(self.error_counts.items(), key=lambda x: x[1])[0].value 
                          if self.error_counts else None
        }


# Global error handler instance
error_handler = MCPErrorHandler()
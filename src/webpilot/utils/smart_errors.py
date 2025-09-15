#!/usr/bin/env python3
"""
Smart error messages with helpful suggestions.

Provides enhanced error messages that help developers quickly fix issues.
"""

import re
import difflib
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SmartElementNotFoundError(Exception):
    """
    Enhanced element not found error with suggestions.
    """
    
    def __init__(
        self,
        selector: str,
        similar_elements: List[str] = None,
        suggestions: List[str] = None,
        page_info: Dict[str, Any] = None
    ):
        self.selector = selector
        self.similar_elements = similar_elements or []
        self.suggestions = suggestions or []
        self.page_info = page_info or {}
        
        # Build detailed error message
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        """Build a helpful error message."""
        lines = [
            f"\n{'='*60}",
            f"❌ Element not found: {self.selector}",
            f"{'='*60}"
        ]
        
        # Add similar elements if found
        if self.similar_elements:
            lines.append("\n🔍 Did you mean one of these?")
            for i, elem in enumerate(self.similar_elements[:5], 1):
                similarity = difflib.SequenceMatcher(None, self.selector, elem).ratio()
                lines.append(f"   {i}. {elem} ({similarity*100:.0f}% match)")
        
        # Add page information
        if self.page_info:
            lines.append("\n📄 Page State:")
            if 'url' in self.page_info:
                lines.append(f"   • URL: {self.page_info['url']}")
            if 'title' in self.page_info:
                lines.append(f"   • Title: {self.page_info['title']}")
            if 'load_time' in self.page_info:
                lines.append(f"   • Loaded: {self.page_info['load_time']}s ago")
            if 'last_action' in self.page_info:
                lines.append(f"   • Last action: {self.page_info['last_action']}")
        
        # Add suggestions
        if self.suggestions or not self.similar_elements:
            lines.append("\n💡 Suggested fixes:")
            default_suggestions = [
                "Check if element is in an iframe",
                "Wait for dynamic content to load",
                "Verify selector syntax",
                "Check if element is hidden (display:none)",
                "Ensure you're on the correct page"
            ]
            
            for i, suggestion in enumerate(self.suggestions or default_suggestions, 1):
                lines.append(f"   {i}. {suggestion}")
        
        # Add code examples
        lines.extend([
            "\n📝 Example fixes:",
            "```python",
            "# Wait for element:",
            f"pilot.wait_for_element('{self.selector}', timeout=10)",
            "",
            "# Check iframe:",
            "pilot.switch_to_iframe('iframe_name')",
            f"pilot.click('{self.selector}')",
            "",
            "# Use text selector:",
            "pilot.click(text='Button Text')",
            "```"
        ])
        
        lines.append(f"{'='*60}\n")
        return "\n".join(lines)


class SmartTimeoutError(Exception):
    """
    Enhanced timeout error with context.
    """
    
    def __init__(
        self,
        operation: str,
        timeout: float,
        element: Optional[str] = None,
        suggestions: List[str] = None
    ):
        self.operation = operation
        self.timeout = timeout
        self.element = element
        self.suggestions = suggestions or []
        
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        """Build a helpful timeout error message."""
        lines = [
            f"\n{'='*60}",
            f"⏱️ Timeout after {self.timeout}s: {self.operation}",
        ]
        
        if self.element:
            lines.append(f"   Element: {self.element}")
        
        lines.append("\n💡 Suggested fixes:")
        
        suggestions = self.suggestions or [
            f"Increase timeout (current: {self.timeout}s)",
            "Check network connectivity",
            "Verify the element selector is correct",
            "Check if page requires authentication",
            "Look for JavaScript errors in console"
        ]
        
        for i, suggestion in enumerate(suggestions, 1):
            lines.append(f"   {i}. {suggestion}")
        
        lines.extend([
            "\n📝 Example fixes:",
            "```python",
            "# Increase timeout:",
            f"pilot.wait_for_element('{self.element or 'selector'}', timeout=30)",
            "",
            "# Wait for network idle:",
            "pilot.wait_for_network_idle()",
            "",
            "# Custom wait condition:",
            "pilot.wait_for(lambda: pilot.is_element_visible('#element'))",
            "```",
            f"{'='*60}\n"
        ])
        
        return "\n".join(lines)


class SmartNetworkError(Exception):
    """
    Enhanced network error with diagnostics.
    """
    
    def __init__(
        self,
        url: str,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
        suggestions: List[str] = None
    ):
        self.url = url
        self.status_code = status_code
        self.error_type = error_type
        self.suggestions = suggestions or []
        
        message = self._build_message()
        super().__init__(message)
    
    def _build_message(self) -> str:
        """Build a helpful network error message."""
        lines = [
            f"\n{'='*60}",
            f"🌐 Network Error: {self.url}",
        ]
        
        if self.status_code:
            lines.append(f"   Status Code: {self.status_code}")
            lines.append(f"   Meaning: {self._get_status_meaning(self.status_code)}")
        
        if self.error_type:
            lines.append(f"   Error Type: {self.error_type}")
        
        lines.append("\n💡 Suggested fixes:")
        
        suggestions = self.suggestions or self._get_status_suggestions(self.status_code)
        
        for i, suggestion in enumerate(suggestions, 1):
            lines.append(f"   {i}. {suggestion}")
        
        lines.append(f"{'='*60}\n")
        return "\n".join(lines)
    
    def _get_status_meaning(self, code: int) -> str:
        """Get human-readable meaning of status code."""
        meanings = {
            400: "Bad Request - The request was invalid",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Access denied",
            404: "Not Found - The page doesn't exist",
            500: "Internal Server Error - Server problem",
            502: "Bad Gateway - Server received invalid response",
            503: "Service Unavailable - Server temporarily down",
            504: "Gateway Timeout - Server took too long to respond"
        }
        return meanings.get(code, "Unknown status code")
    
    def _get_status_suggestions(self, code: Optional[int]) -> List[str]:
        """Get suggestions based on status code."""
        if not code:
            return [
                "Check internet connection",
                "Verify URL is correct",
                "Check if site is online",
                "Try again with retry logic"
            ]
        
        if code == 401:
            return [
                "Add authentication credentials",
                "Check if login is required",
                "Verify API key or token",
                "Handle login flow first"
            ]
        elif code == 404:
            return [
                "Verify URL is correct",
                "Check if page was moved",
                "Ensure no typos in URL",
                "Check if page requires login first"
            ]
        elif code >= 500:
            return [
                "Server error - wait and retry",
                "Contact site administrator",
                "Check service status page",
                "Implement exponential backoff"
            ]
        else:
            return ["Check request parameters", "Verify request format"]


class ErrorSuggestionEngine:
    """
    Generates helpful suggestions for various error scenarios.
    """
    
    @staticmethod
    def suggest_selector_alternatives(selector: str, available_elements: List[str]) -> List[str]:
        """
        Suggest alternative selectors based on available elements.
        
        Args:
            selector: The selector that failed
            available_elements: List of available element selectors
            
        Returns:
            List of suggested alternatives
        """
        suggestions = []
        
        # Find similar selectors using fuzzy matching
        matches = difflib.get_close_matches(selector, available_elements, n=5, cutoff=0.6)
        suggestions.extend(matches)
        
        # Suggest different selector strategies
        if selector.startswith('#'):
            # ID selector - suggest class or attribute
            element_name = selector[1:]
            suggestions.append(f"[id*='{element_name[:5]}']")  # Partial ID match
            suggestions.append(f".{element_name}")  # Try as class
        
        elif selector.startswith('.'):
            # Class selector - suggest ID or attribute
            class_name = selector[1:]
            suggestions.append(f"#{class_name}")  # Try as ID
            suggestions.append(f"[class*='{class_name[:5]}']")  # Partial class match
        
        # Suggest text-based selection
        suggestions.append(f"text='...'  # Use visible text instead")
        suggestions.append(f"xpath='//button[contains(text(), \"...\")]'")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    @staticmethod
    def analyze_page_state(pilot: Any) -> Dict[str, Any]:
        """
        Analyze current page state for debugging.
        
        Args:
            pilot: WebPilot instance
            
        Returns:
            Dictionary with page state information
        """
        state = {}
        
        try:
            if hasattr(pilot, 'current_url'):
                state['url'] = pilot.current_url
            
            if hasattr(pilot, 'title'):
                state['title'] = pilot.title
            
            if hasattr(pilot, 'get_page_load_time'):
                state['load_time'] = pilot.get_page_load_time()
            
            if hasattr(pilot, 'get_last_action'):
                state['last_action'] = pilot.get_last_action()
            
            if hasattr(pilot, 'is_page_loaded'):
                state['is_loaded'] = pilot.is_page_loaded()
            
            if hasattr(pilot, 'get_console_errors'):
                errors = pilot.get_console_errors()
                if errors:
                    state['console_errors'] = len(errors)
                    state['first_error'] = errors[0] if errors else None
            
        except Exception as e:
            logger.debug(f"Error analyzing page state: {e}")
        
        return state
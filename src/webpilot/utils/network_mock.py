#!/usr/bin/env python3
"""
Network mocking utilities for faster and more reliable tests.

Allows intercepting and mocking network requests to speed up tests
and make them more deterministic.
"""

import json
import re
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MockStrategy(Enum):
    """Strategy for matching requests to mocks."""
    EXACT = "exact"  # Exact URL match
    REGEX = "regex"  # Regular expression match
    PARTIAL = "partial"  # Partial URL match
    DOMAIN = "domain"  # Domain match only


@dataclass
class MockResponse:
    """Represents a mocked network response."""
    status: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    delay: float = 0  # Artificial delay in seconds
    error: Optional[str] = None  # Simulate network error
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to response format."""
        response = {
            "status": self.status,
            "headers": self.headers
        }
        
        if self.json_data is not None:
            response["body"] = json.dumps(self.json_data)
            response["headers"]["Content-Type"] = "application/json"
        elif self.body is not None:
            response["body"] = self.body
        
        if self.error:
            response["error"] = self.error
            
        return response


@dataclass
class MockRule:
    """Rule for mocking network requests."""
    pattern: str  # URL pattern to match
    response: MockResponse
    strategy: MockStrategy = MockStrategy.EXACT
    method: Optional[str] = None  # GET, POST, etc. (None = any)
    times: Optional[int] = None  # How many times to apply (None = unlimited)
    predicate: Optional[Callable[[Dict[str, Any]], bool]] = None  # Custom matcher
    
    def __post_init__(self):
        self.times_used = 0
        if self.strategy == MockStrategy.REGEX:
            self.regex = re.compile(self.pattern)
    
    def matches(self, request: Dict[str, Any]) -> bool:
        """Check if this rule matches the request."""
        # Check if rule has been exhausted
        if self.times is not None and self.times_used >= self.times:
            return False
        
        # Check method if specified
        if self.method and request.get("method") != self.method:
            return False
        
        # Check URL pattern
        url = request.get("url", "")
        
        if self.strategy == MockStrategy.EXACT:
            url_matches = url == self.pattern
        elif self.strategy == MockStrategy.REGEX:
            url_matches = bool(self.regex.search(url))
        elif self.strategy == MockStrategy.PARTIAL:
            url_matches = self.pattern in url
        elif self.strategy == MockStrategy.DOMAIN:
            url_matches = self.pattern in url.split('/')[2] if len(url.split('/')) > 2 else False
        else:
            url_matches = False
        
        if not url_matches:
            return False
        
        # Check custom predicate if provided
        if self.predicate and not self.predicate(request):
            return False
        
        return True
    
    def apply(self) -> MockResponse:
        """Apply this rule and return the response."""
        self.times_used += 1
        return self.response


class NetworkMocker:
    """
    Main network mocking interface.
    
    Example:
        mocker = NetworkMocker()
        
        # Mock API response
        mocker.mock_response(
            "https://api.example.com/users",
            json={"users": [{"id": 1, "name": "Test"}]},
            status=200
        )
        
        # Mock with regex
        mocker.mock_regex(
            r"https://api\.example\.com/users/\d+",
            json={"id": 1, "name": "Test User"}
        )
        
        # Mock error
        mocker.mock_error("https://slow.api.com", status=500)
        
        # Apply to pilot
        pilot.set_network_mocker(mocker)
    """
    
    def __init__(self):
        self.rules: List[MockRule] = []
        self.request_log: List[Dict[str, Any]] = []
        self.unmatched_requests: List[Dict[str, Any]] = []
        
    def mock_response(
        self,
        url: str,
        body: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        method: Optional[str] = None,
        times: Optional[int] = None,
        delay: float = 0
    ):
        """
        Mock a network response for exact URL match.
        
        Args:
            url: Exact URL to mock
            body: Response body as string
            json: Response body as JSON (will be serialized)
            status: HTTP status code
            headers: Response headers
            method: HTTP method (None = any)
            times: Number of times to apply this mock
            delay: Artificial delay before response
        """
        response = MockResponse(
            status=status,
            headers=headers or {},
            body=body,
            json_data=json,
            delay=delay
        )
        
        rule = MockRule(
            pattern=url,
            response=response,
            strategy=MockStrategy.EXACT,
            method=method,
            times=times
        )
        
        self.rules.append(rule)
        logger.debug(f"Added mock for {method or 'ANY'} {url}")
        
    def mock_regex(
        self,
        pattern: str,
        body: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        method: Optional[str] = None,
        times: Optional[int] = None
    ):
        """
        Mock responses matching a regex pattern.
        
        Args:
            pattern: Regular expression pattern
            Other args same as mock_response
        """
        response = MockResponse(
            status=status,
            headers=headers or {},
            body=body,
            json_data=json
        )
        
        rule = MockRule(
            pattern=pattern,
            response=response,
            strategy=MockStrategy.REGEX,
            method=method,
            times=times
        )
        
        self.rules.append(rule)
        logger.debug(f"Added regex mock for pattern: {pattern}")
        
    def mock_domain(
        self,
        domain: str,
        body: Optional[str] = None,
        json: Optional[Dict[str, Any]] = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Mock all requests to a domain.
        
        Args:
            domain: Domain to mock (e.g., "api.example.com")
            Other args same as mock_response
        """
        response = MockResponse(
            status=status,
            headers=headers or {},
            body=body,
            json_data=json
        )
        
        rule = MockRule(
            pattern=domain,
            response=response,
            strategy=MockStrategy.DOMAIN
        )
        
        self.rules.append(rule)
        logger.debug(f"Added domain mock for: {domain}")
        
    def mock_error(
        self,
        url: str,
        status: int = 500,
        error_message: str = "Internal Server Error",
        method: Optional[str] = None
    ):
        """
        Mock a network error.
        
        Args:
            url: URL to mock
            status: HTTP error status code
            error_message: Error message
            method: HTTP method
        """
        response = MockResponse(
            status=status,
            body=error_message,
            error=error_message
        )
        
        rule = MockRule(
            pattern=url,
            response=response,
            strategy=MockStrategy.EXACT,
            method=method
        )
        
        self.rules.append(rule)
        logger.debug(f"Added error mock for {url}: {status} {error_message}")
        
    def mock_timeout(self, url: str, delay: float = 30):
        """
        Mock a timeout by adding extreme delay.
        
        Args:
            url: URL to mock
            delay: Delay in seconds (should be longer than timeout)
        """
        response = MockResponse(delay=delay)
        
        rule = MockRule(
            pattern=url,
            response=response,
            strategy=MockStrategy.EXACT
        )
        
        self.rules.append(rule)
        logger.debug(f"Added timeout mock for {url}: {delay}s delay")
        
    def mock_custom(
        self,
        predicate: Callable[[Dict[str, Any]], bool],
        response: Union[MockResponse, Callable[[Dict[str, Any]], MockResponse]]
    ):
        """
        Mock with custom predicate function.
        
        Args:
            predicate: Function that returns True if request should be mocked
            response: MockResponse or function that returns MockResponse
        """
        if callable(response):
            # Dynamic response based on request
            rule = MockRule(
                pattern="",
                response=MockResponse(),  # Placeholder
                predicate=predicate
            )
            rule._dynamic_response = response
        else:
            rule = MockRule(
                pattern="",
                response=response,
                predicate=predicate
            )
        
        self.rules.append(rule)
        logger.debug("Added custom mock rule")
        
    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle a network request and return mock if applicable.
        
        Args:
            request: Request details (url, method, headers, body)
            
        Returns:
            Mocked response or None if no mock matches
        """
        self.request_log.append(request)
        
        # Find matching rule
        for rule in self.rules:
            if rule.matches(request):
                logger.debug(f"Mock match for {request['url']}")
                
                # Get response
                if hasattr(rule, '_dynamic_response'):
                    response = rule._dynamic_response(request)
                else:
                    response = rule.apply()
                
                # Apply delay if specified
                if response.delay > 0:
                    import time
                    time.sleep(response.delay)
                
                return response.to_response()
        
        # No match found
        self.unmatched_requests.append(request)
        logger.debug(f"No mock for {request['url']}")
        return None
        
    def clear(self):
        """Clear all mock rules."""
        self.rules.clear()
        self.request_log.clear()
        self.unmatched_requests.clear()
        
    def get_request_count(self, url_pattern: Optional[str] = None) -> int:
        """
        Get count of requests matching pattern.
        
        Args:
            url_pattern: Optional pattern to filter requests
            
        Returns:
            Number of matching requests
        """
        if not url_pattern:
            return len(self.request_log)
        
        count = 0
        for request in self.request_log:
            if url_pattern in request.get("url", ""):
                count += 1
        return count
        
    def assert_requested(self, url_pattern: str, times: Optional[int] = None):
        """
        Assert that a URL was requested.
        
        Args:
            url_pattern: URL pattern to check
            times: Expected number of times (None = at least once)
            
        Raises:
            AssertionError if not requested expected number of times
        """
        count = self.get_request_count(url_pattern)
        
        if times is None:
            if count == 0:
                raise AssertionError(f"URL pattern '{url_pattern}' was never requested")
        else:
            if count != times:
                raise AssertionError(
                    f"URL pattern '{url_pattern}' was requested {count} times, "
                    f"expected {times}"
                )
        
    def get_unmatched_requests(self) -> List[Dict[str, Any]]:
        """Get list of requests that had no mock."""
        return self.unmatched_requests.copy()


# Convenience functions for common mocking scenarios
def mock_api_endpoints(mocker: NetworkMocker, base_url: str, endpoints: Dict[str, Any]):
    """
    Mock multiple API endpoints at once.
    
    Args:
        mocker: NetworkMocker instance
        base_url: Base URL of API
        endpoints: Dict mapping paths to responses
        
    Example:
        mock_api_endpoints(mocker, "https://api.example.com", {
            "/users": {"users": []},
            "/posts": {"posts": []},
            "/auth/login": {"token": "abc123"}
        })
    """
    for path, response in endpoints.items():
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        mocker.mock_response(url, json=response)


def mock_static_assets(mocker: NetworkMocker, patterns: List[str]):
    """
    Mock static assets to speed up page loads.
    
    Args:
        mocker: NetworkMocker instance
        patterns: List of URL patterns for static assets
        
    Example:
        mock_static_assets(mocker, [
            "*.css",
            "*.js",
            "*.jpg",
            "*.png"
        ])
    """
    for pattern in patterns:
        # Convert wildcard to regex
        regex_pattern = pattern.replace("*", ".*")
        mocker.mock_regex(regex_pattern, body="", status=200)


def mock_slow_endpoints(mocker: NetworkMocker, endpoints: Dict[str, float]):
    """
    Mock slow endpoints with fast responses.
    
    Args:
        mocker: NetworkMocker instance
        endpoints: Dict mapping URLs to original response times
        
    Example:
        mock_slow_endpoints(mocker, {
            "https://slow.api.com/search": 5.0,
            "https://slow.api.com/process": 10.0
        })
    """
    for url, original_time in endpoints.items():
        # Mock with minimal delay
        mocker.mock_response(url, json={}, delay=0.1)
        logger.info(f"Mocked slow endpoint {url}: {original_time}s -> 0.1s")
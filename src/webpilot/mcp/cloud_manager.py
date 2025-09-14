"""
Cloud platform manager for WebPilot MCP.

Provides unified interface for cloud testing platforms like BrowserStack,
Sauce Labs, and LambdaTest.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import os
import logging
from urllib.parse import quote


class CloudPlatform(Enum):
    """Supported cloud testing platforms."""
    BROWSERSTACK = "browserstack"
    SAUCE_LABS = "sauce_labs"
    LAMBDA_TEST = "lambdatest"
    SELENIUM_GRID = "selenium_grid"
    LOCAL = "local"


@dataclass
class CloudCredentials:
    """Cloud platform credentials."""
    username: str
    access_key: str
    platform: CloudPlatform
    hub_url: Optional[str] = None
    
    @classmethod
    def from_env(cls, platform: CloudPlatform) -> Optional['CloudCredentials']:
        """Load credentials from environment variables."""
        env_mapping = {
            CloudPlatform.BROWSERSTACK: {
                'username': 'BROWSERSTACK_USERNAME',
                'key': 'BROWSERSTACK_ACCESS_KEY',
                'hub': 'https://hub-cloud.browserstack.com/wd/hub'
            },
            CloudPlatform.SAUCE_LABS: {
                'username': 'SAUCE_USERNAME',
                'key': 'SAUCE_ACCESS_KEY',
                'hub': 'https://ondemand.saucelabs.com/wd/hub'
            },
            CloudPlatform.LAMBDA_TEST: {
                'username': 'LT_USERNAME',
                'key': 'LT_ACCESS_KEY',
                'hub': 'https://hub.lambdatest.com/wd/hub'
            },
            CloudPlatform.SELENIUM_GRID: {
                'username': 'GRID_USERNAME',
                'key': 'GRID_ACCESS_KEY',
                'hub': os.getenv('SELENIUM_GRID_URL', 'http://localhost:4444/wd/hub')
            }
        }
        
        if platform not in env_mapping:
            return None
            
        config = env_mapping[platform]
        username = os.getenv(config['username'])
        access_key = os.getenv(config['key'])
        
        if not username or not access_key:
            return None
            
        return cls(
            username=username,
            access_key=access_key,
            platform=platform,
            hub_url=config['hub']
        )


@dataclass
class CloudCapabilities:
    """Browser capabilities for cloud platforms."""
    browser: str
    browser_version: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    resolution: Optional[str] = None
    device: Optional[str] = None
    real_mobile: bool = False
    local_testing: bool = False
    video: bool = True
    console_logs: bool = True
    network_logs: bool = False
    visual_testing: bool = False
    
    def to_browserstack(self) -> Dict[str, Any]:
        """Convert to BrowserStack capabilities."""
        caps = {
            'browserName': self.browser,
            'bstack:options': {
                'os': self.os or 'Windows',
                'osVersion': self.os_version or '11',
                'local': self.local_testing,
                'video': self.video,
                'consoleLogs': 'verbose' if self.console_logs else 'disable',
                'networkLogs': self.network_logs
            }
        }
        
        if self.browser_version:
            caps['browserVersion'] = self.browser_version
        if self.resolution:
            caps['bstack:options']['resolution'] = self.resolution
        if self.device:
            caps['bstack:options']['deviceName'] = self.device
            caps['bstack:options']['realMobile'] = self.real_mobile
            
        return caps
    
    def to_sauce_labs(self) -> Dict[str, Any]:
        """Convert to Sauce Labs capabilities."""
        caps = {
            'browserName': self.browser,
            'sauce:options': {
                'platformName': f"{self.os} {self.os_version}" if self.os else 'Windows 11',
                'recordVideo': self.video,
                'recordLogs': self.console_logs,
                'capturePerformance': self.network_logs
            }
        }
        
        if self.browser_version:
            caps['browserVersion'] = self.browser_version
        if self.resolution:
            caps['sauce:options']['screenResolution'] = self.resolution
        if self.device:
            caps['sauce:options']['deviceName'] = self.device
            
        return caps
    
    def to_lambdatest(self) -> Dict[str, Any]:
        """Convert to LambdaTest capabilities."""
        caps = {
            'browserName': self.browser,
            'lt:options': {
                'platform': f"{self.os} {self.os_version}" if self.os else 'Windows 11',
                'build': 'WebPilot MCP',
                'name': 'WebPilot Test',
                'video': self.video,
                'console': self.console_logs,
                'network': self.network_logs,
                'visual': self.visual_testing
            }
        }
        
        if self.browser_version:
            caps['version'] = self.browser_version
        if self.resolution:
            caps['lt:options']['resolution'] = self.resolution
        if self.device:
            caps['lt:options']['deviceName'] = self.device
            
        return caps


class CloudSessionManager:
    """
    Manages cloud testing sessions across platforms.
    
    Provides unified interface for starting, managing, and terminating
    cloud browser sessions.
    """
    
    def __init__(self):
        """Initialize cloud session manager."""
        self.logger = logging.getLogger(__name__)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.credentials: Dict[CloudPlatform, CloudCredentials] = {}
        
        # Auto-load credentials from environment
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from environment variables."""
        for platform in CloudPlatform:
            if platform == CloudPlatform.LOCAL:
                continue
                
            creds = CloudCredentials.from_env(platform)
            if creds:
                self.credentials[platform] = creds
                self.logger.info(f"Loaded credentials for {platform.value}")
    
    def get_available_platforms(self) -> List[CloudPlatform]:
        """Get list of platforms with configured credentials."""
        available = [CloudPlatform.LOCAL]
        available.extend(self.credentials.keys())
        return available
    
    def create_session(self, 
                      platform: CloudPlatform,
                      capabilities: CloudCapabilities,
                      session_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new cloud testing session.
        
        Args:
            platform: Cloud platform to use
            capabilities: Browser capabilities
            session_name: Optional session name
            
        Returns:
            Session information including connection details
        """
        if platform == CloudPlatform.LOCAL:
            return self._create_local_session(capabilities)
            
        if platform not in self.credentials:
            return {
                "success": False,
                "error": f"No credentials configured for {platform.value}. "
                        f"Set environment variables for authentication."
            }
        
        creds = self.credentials[platform]
        
        # Convert capabilities to platform format
        if platform == CloudPlatform.BROWSERSTACK:
            caps = capabilities.to_browserstack()
        elif platform == CloudPlatform.SAUCE_LABS:
            caps = capabilities.to_sauce_labs()
        elif platform == CloudPlatform.LAMBDA_TEST:
            caps = capabilities.to_lambdatest()
        else:
            caps = {
                'browserName': capabilities.browser,
                'browserVersion': capabilities.browser_version
            }
        
        # Build remote URL with credentials
        remote_url = self._build_remote_url(creds)
        
        session_id = session_name or f"{platform.value}_{len(self.active_sessions)}"
        
        session_info = {
            "session_id": session_id,
            "platform": platform.value,
            "remote_url": remote_url,
            "capabilities": caps,
            "dashboard_url": self._get_dashboard_url(platform, session_id),
            "status": "initializing"
        }
        
        self.active_sessions[session_id] = session_info
        
        return {
            "success": True,
            "session": session_info,
            "message": f"Cloud session prepared for {platform.value}"
        }
    
    def _create_local_session(self, capabilities: CloudCapabilities) -> Dict[str, Any]:
        """Create a local browser session."""
        return {
            "success": True,
            "session": {
                "session_id": f"local_{len(self.active_sessions)}",
                "platform": "local",
                "browser": capabilities.browser,
                "capabilities": {
                    "browserName": capabilities.browser,
                    "browserVersion": capabilities.browser_version
                }
            }
        }
    
    def _build_remote_url(self, creds: CloudCredentials) -> str:
        """Build remote WebDriver URL with credentials."""
        if creds.platform == CloudPlatform.SELENIUM_GRID:
            # Grid might not need credentials in URL
            return creds.hub_url
            
        # Most cloud platforms use https://username:key@hub.domain.com format
        hub_base = creds.hub_url.replace('https://', '').replace('http://', '')
        return f"https://{quote(creds.username)}:{quote(creds.access_key)}@{hub_base}"
    
    def _get_dashboard_url(self, platform: CloudPlatform, session_id: str) -> Optional[str]:
        """Get dashboard URL for viewing test execution."""
        base_urls = {
            CloudPlatform.BROWSERSTACK: "https://automate.browserstack.com/dashboard/v2/sessions",
            CloudPlatform.SAUCE_LABS: "https://app.saucelabs.com/tests",
            CloudPlatform.LAMBDA_TEST: "https://automation.lambdatest.com/test"
        }
        
        return base_urls.get(platform)
    
    def terminate_session(self, session_id: str) -> Dict[str, Any]:
        """Terminate a cloud testing session."""
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        session = self.active_sessions[session_id]
        session["status"] = "terminated"
        
        # In real implementation, would call platform API to end session
        del self.active_sessions[session_id]
        
        return {
            "success": True,
            "message": f"Session {session_id} terminated"
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a cloud session."""
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        return {
            "success": True,
            "session": self.active_sessions[session_id]
        }
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active cloud sessions."""
        return list(self.active_sessions.values())
    
    def get_platform_info(self, platform: CloudPlatform) -> Dict[str, Any]:
        """Get information about a cloud platform."""
        info = {
            CloudPlatform.BROWSERSTACK: {
                "name": "BrowserStack",
                "features": ["Real devices", "Local testing", "Visual testing", "Accessibility"],
                "browsers": ["Chrome", "Firefox", "Safari", "Edge"],
                "mobile": ["iOS", "Android"],
                "parallel_limit": 5,
                "pricing": "Per parallel session"
            },
            CloudPlatform.SAUCE_LABS: {
                "name": "Sauce Labs",
                "features": ["Real devices", "Performance testing", "Visual testing", "API testing"],
                "browsers": ["Chrome", "Firefox", "Safari", "Edge"],
                "mobile": ["iOS", "Android"],
                "parallel_limit": 10,
                "pricing": "Per minute"
            },
            CloudPlatform.LAMBDA_TEST: {
                "name": "LambdaTest",
                "features": ["Real devices", "Smart testing", "Visual UI testing", "Geolocation"],
                "browsers": ["Chrome", "Firefox", "Safari", "Edge", "Opera"],
                "mobile": ["iOS", "Android"],
                "parallel_limit": 6,
                "pricing": "Per parallel session"
            }
        }
        
        return info.get(platform, {
            "name": platform.value,
            "features": [],
            "browsers": [],
            "mobile": []
        })


# Global cloud manager instance
cloud_manager = CloudSessionManager()
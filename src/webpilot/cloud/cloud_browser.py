#!/usr/bin/env python3
"""
WebPilot Cloud Browser Support
Integrates with BrowserStack, Sauce Labs, and other cloud testing platforms
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.remote_connection import RemoteConnection

from ..core import WebPilotSession, ActionResult, ActionType, BrowserType
from ..backends.selenium import SeleniumWebPilot


class CloudProvider(Enum):
    """Supported cloud testing providers"""
    BROWSERSTACK = "browserstack"
    SAUCE_LABS = "saucelabs"
    LAMBDATEST = "lambdatest"
    CROSSBROWSERTESTING = "crossbrowsertesting"


@dataclass
class CloudConfig:
    """Configuration for cloud browser providers"""
    provider: CloudProvider
    username: str
    access_key: str
    project_name: Optional[str] = "WebPilot Tests"
    build_name: Optional[str] = None
    session_name: Optional[str] = None
    local_testing: bool = False
    debug: bool = False
    video_recording: bool = True
    network_logs: bool = False
    console_logs: bool = False
    visual_logs: bool = False
    

class CloudBrowserFactory:
    """Factory for creating cloud browser instances"""
    
    PROVIDER_URLS = {
        CloudProvider.BROWSERSTACK: "https://{username}:{access_key}@hub-cloud.browserstack.com/wd/hub",
        CloudProvider.SAUCE_LABS: "https://{username}:{access_key}@ondemand.saucelabs.com/wd/hub",
        CloudProvider.LAMBDATEST: "https://{username}:{access_key}@hub.lambdatest.com/wd/hub",
        CloudProvider.CROSSBROWSERTESTING: "http://{username}:{access_key}@hub.crossbrowsertesting.com:80/wd/hub"
    }
    
    @classmethod
    def create_driver(cls, config: CloudConfig, 
                     browser: str = "chrome",
                     browser_version: str = "latest",
                     os_name: str = "Windows",
                     os_version: str = "11") -> webdriver.Remote:
        """
        Create a remote WebDriver instance for cloud testing
        
        Args:
            config: Cloud provider configuration
            browser: Browser name (chrome, firefox, safari, edge)
            browser_version: Browser version or "latest"
            os_name: Operating system name
            os_version: Operating system version
            
        Returns:
            Remote WebDriver instance
        """
        # Get provider URL
        url_template = cls.PROVIDER_URLS.get(config.provider)
        if not url_template:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        hub_url = url_template.format(
            username=config.username,
            access_key=config.access_key
        )
        
        # Build capabilities based on provider
        if config.provider == CloudProvider.BROWSERSTACK:
            capabilities = cls._browserstack_capabilities(
                config, browser, browser_version, os_name, os_version
            )
        elif config.provider == CloudProvider.SAUCE_LABS:
            capabilities = cls._saucelabs_capabilities(
                config, browser, browser_version, os_name, os_version
            )
        elif config.provider == CloudProvider.LAMBDATEST:
            capabilities = cls._lambdatest_capabilities(
                config, browser, browser_version, os_name, os_version
            )
        else:
            capabilities = cls._generic_capabilities(
                config, browser, browser_version, os_name, os_version
            )
        
        # Create remote driver
        return webdriver.Remote(
            command_executor=hub_url,
            desired_capabilities=capabilities
        )
    
    @staticmethod
    def _browserstack_capabilities(config: CloudConfig, browser: str,
                                  browser_version: str, os_name: str,
                                  os_version: str) -> Dict:
        """Build BrowserStack-specific capabilities"""
        caps = {
            'browserName': browser,
            'browserVersion': browser_version,
            'bstack:options': {
                'os': os_name,
                'osVersion': os_version,
                'projectName': config.project_name,
                'buildName': config.build_name or f"Build-{time.strftime('%Y%m%d-%H%M%S')}",
                'sessionName': config.session_name or f"Test-{time.strftime('%H%M%S')}",
                'local': str(config.local_testing).lower(),
                'debug': str(config.debug).lower(),
                'video': str(config.video_recording).lower(),
                'networkLogs': str(config.network_logs).lower(),
                'consoleLogs': str(config.console_logs).lower(),
            }
        }
        return caps
    
    @staticmethod
    def _saucelabs_capabilities(config: CloudConfig, browser: str,
                               browser_version: str, os_name: str,
                               os_version: str) -> Dict:
        """Build Sauce Labs-specific capabilities"""
        caps = {
            'browserName': browser,
            'browserVersion': browser_version,
            'platformName': f"{os_name} {os_version}",
            'sauce:options': {
                'name': config.session_name or f"Test-{time.strftime('%H%M%S')}",
                'build': config.build_name or f"Build-{time.strftime('%Y%m%d-%H%M%S')}",
                'recordVideo': config.video_recording,
                'recordScreenshots': True,
                'recordLogs': config.console_logs,
                'tunnelIdentifier': 'webpilot-tunnel' if config.local_testing else None,
            }
        }
        return caps
    
    @staticmethod
    def _lambdatest_capabilities(config: CloudConfig, browser: str,
                                browser_version: str, os_name: str,
                                os_version: str) -> Dict:
        """Build LambdaTest-specific capabilities"""
        caps = {
            'browserName': browser,
            'version': browser_version,
            'platform': f"{os_name} {os_version}",
            'build': config.build_name or f"Build-{time.strftime('%Y%m%d-%H%M%S')}",
            'name': config.session_name or f"Test-{time.strftime('%H%M%S')}",
            'video': config.video_recording,
            'visual': config.visual_logs,
            'network': config.network_logs,
            'console': config.console_logs,
            'tunnel': config.local_testing,
        }
        return caps
    
    @staticmethod
    def _generic_capabilities(config: CloudConfig, browser: str,
                             browser_version: str, os_name: str,
                             os_version: str) -> Dict:
        """Build generic capabilities for other providers"""
        caps = DesiredCapabilities.CHROME.copy() if browser == "chrome" else \
               DesiredCapabilities.FIREFOX.copy() if browser == "firefox" else \
               DesiredCapabilities.SAFARI.copy() if browser == "safari" else \
               DesiredCapabilities.EDGE.copy()
        
        caps.update({
            'platform': f"{os_name} {os_version}",
            'version': browser_version,
            'name': config.session_name or f"Test-{time.strftime('%H%M%S')}",
        })
        return caps


class CloudWebPilot(SeleniumWebPilot):
    """WebPilot with cloud browser support"""
    
    def __init__(self, config: CloudConfig,
                 browser: str = "chrome",
                 browser_version: str = "latest",
                 os_name: str = "Windows", 
                 os_version: str = "11",
                 session: Optional[WebPilotSession] = None):
        """
        Initialize cloud-based WebPilot
        
        Args:
            config: Cloud provider configuration
            browser: Browser to use
            browser_version: Browser version
            os_name: Operating system
            os_version: OS version
            session: Optional session to resume
        """
        self.cloud_config = config
        self.browser_name = browser
        self.browser_version = browser_version
        self.os_name = os_name
        self.os_version = os_version
        
        # Initialize parent without starting browser
        super().__init__(
            browser=BrowserType.CHROME,  # Will be overridden
            headless=False,  # Cloud browsers handle this
            session=session
        )
        
        self.logger = logging.getLogger(f'CloudWebPilot.{config.provider.value}')
        
    def start(self, url: str) -> ActionResult:
        """Start cloud browser and navigate to URL"""
        start_time = time.time()
        
        try:
            # Create cloud driver
            self.driver = CloudBrowserFactory.create_driver(
                self.cloud_config,
                self.browser_name,
                self.browser_version,
                self.os_name,
                self.os_version
            )
            
            # Set implicit wait
            self.driver.implicitly_wait(10)
            
            # Navigate to URL
            self.driver.get(url)
            
            # Get session info
            session_id = self.driver.session_id
            
            # Update session state
            self.session.state['cloud_provider'] = self.cloud_config.provider.value
            self.session.state['cloud_session_id'] = session_id
            self.session.state['current_url'] = url
            self.session.save_state()
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={
                    'url': url,
                    'title': self.driver.title,
                    'cloud_provider': self.cloud_config.provider.value,
                    'session_id': session_id,
                    'browser': f"{self.browser_name} {self.browser_version}",
                    'os': f"{self.os_name} {self.os_version}"
                },
                duration_ms=duration
            )
            
            self.logger.info(f"Cloud browser started on {self.cloud_config.provider.value}: {url}")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to start cloud browser: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def get_session_url(self) -> Optional[str]:
        """Get URL to view the cloud session in provider's dashboard"""
        if not self.driver:
            return None
            
        session_id = self.driver.session_id
        
        if self.cloud_config.provider == CloudProvider.BROWSERSTACK:
            return f"https://automate.browserstack.com/dashboard/v2/sessions/{session_id}"
        elif self.cloud_config.provider == CloudProvider.SAUCE_LABS:
            return f"https://app.saucelabs.com/tests/{session_id}"
        elif self.cloud_config.provider == CloudProvider.LAMBDATEST:
            return f"https://automation.lambdatest.com/test/{session_id}"
        else:
            return None
    
    def mark_test_status(self, passed: bool, reason: Optional[str] = None) -> None:
        """Mark the test as passed or failed in the cloud provider"""
        if not self.driver:
            return
            
        if self.cloud_config.provider == CloudProvider.BROWSERSTACK:
            script = f'browserstack_executor: {{"action": "setSessionStatus", "arguments": {{"status": "{"passed" if passed else "failed"}", "reason": "{reason or ""}"}}}}'
            self.driver.execute_script(script)
        elif self.cloud_config.provider == CloudProvider.SAUCE_LABS:
            self.driver.execute_script(f"sauce:job-result={'passed' if passed else 'failed'}")
            if reason:
                self.driver.execute_script(f"sauce:job-info={json.dumps({'passed': passed, 'custom-data': {'reason': reason}})}")
        elif self.cloud_config.provider == CloudProvider.LAMBDATEST:
            self.driver.execute_script(f"lambda-status={'passed' if passed else 'failed'}")
    
    def enable_network_throttling(self, profile: Literal['Regular3G', 'Regular4G', 'WiFi', 'offline'] = 'Regular3G') -> ActionResult:
        """Enable network throttling (BrowserStack specific)"""
        if self.cloud_config.provider != CloudProvider.BROWSERSTACK:
            return ActionResult(
                success=False,
                action_type=ActionType.SCRIPT,
                error=f"Network throttling not supported for {self.cloud_config.provider.value}"
            )
        
        try:
            script = f'browserstack_executor: {{"action": "networkThrottle", "arguments": {{"condition": "{profile}"}}}}'
            self.driver.execute_script(script)
            
            return ActionResult(
                success=True,
                action_type=ActionType.SCRIPT,
                data={'network_profile': profile}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_type=ActionType.SCRIPT,
                error=str(e)
            )
    
    def get_network_logs(self) -> Optional[List[Dict]]:
        """Get network logs from the cloud session"""
        if not self.cloud_config.network_logs:
            return None
            
        try:
            if self.cloud_config.provider == CloudProvider.BROWSERSTACK:
                logs = self.driver.execute_script('browserstack_executor: {"action": "getNetworkLogs"}')
                return logs
            else:
                # Try generic approach
                logs = self.driver.get_log('performance')
                return logs
        except:
            return None
    
    def get_console_logs(self) -> Optional[List[Dict]]:
        """Get console logs from the cloud session"""
        if not self.cloud_config.console_logs:
            return None
            
        try:
            return self.driver.get_log('browser')
        except:
            return None


class CloudTestRunner:
    """Runner for executing tests across multiple cloud configurations"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.results = []
        self.logger = logging.getLogger('CloudTestRunner')
        
    def run_on_matrix(self, test_function, configurations: List[Dict]) -> List[Dict]:
        """
        Run tests across multiple browser/OS combinations
        
        Args:
            test_function: Function that takes a WebPilot instance
            configurations: List of configuration dicts with browser, version, os, etc.
            
        Returns:
            List of test results
        """
        results = []
        
        for config in configurations:
            self.logger.info(f"Running test on: {config}")
            
            # Create cloud pilot
            pilot = CloudWebPilot(
                self.config,
                browser=config.get('browser', 'chrome'),
                browser_version=config.get('browser_version', 'latest'),
                os_name=config.get('os', 'Windows'),
                os_version=config.get('os_version', '11')
            )
            
            # Run test
            try:
                test_result = test_function(pilot)
                
                # Mark test status
                pilot.mark_test_status(
                    passed=test_result.get('passed', False),
                    reason=test_result.get('reason', '')
                )
                
                # Add session URL
                test_result['session_url'] = pilot.get_session_url()
                
                results.append({
                    'config': config,
                    'result': test_result,
                    'session_url': pilot.get_session_url()
                })
                
            except Exception as e:
                self.logger.error(f"Test failed: {e}")
                pilot.mark_test_status(False, str(e))
                results.append({
                    'config': config,
                    'error': str(e),
                    'session_url': pilot.get_session_url()
                })
                
            finally:
                pilot.close()
        
        return results
    
    def generate_matrix(self, browsers: List[str] = None,
                       operating_systems: List[Dict] = None) -> List[Dict]:
        """Generate test matrix for common browser/OS combinations"""
        if browsers is None:
            browsers = ['chrome', 'firefox', 'safari', 'edge']
            
        if operating_systems is None:
            operating_systems = [
                {'os': 'Windows', 'os_version': '11'},
                {'os': 'Windows', 'os_version': '10'},
                {'os': 'OS X', 'os_version': 'Monterey'},
                {'os': 'OS X', 'os_version': 'Big Sur'},
            ]
        
        matrix = []
        for browser in browsers:
            for os_config in operating_systems:
                # Skip Safari on Windows
                if browser == 'safari' and os_config['os'] == 'Windows':
                    continue
                # Skip Edge on Mac
                if browser == 'edge' and os_config['os'] == 'OS X':
                    continue
                    
                matrix.append({
                    'browser': browser,
                    'browser_version': 'latest',
                    **os_config
                })
        
        return matrix


def test_cloud_browsers():
    """Test cloud browser functionality"""
    
    # Check for credentials
    bs_username = os.environ.get('BROWSERSTACK_USERNAME')
    bs_access_key = os.environ.get('BROWSERSTACK_ACCESS_KEY')
    
    if not bs_username or not bs_access_key:
        print("⚠️  Cloud browser testing requires credentials")
        print("   Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY environment variables")
        print("   Or use Sauce Labs with SAUCE_USERNAME and SAUCE_ACCESS_KEY")
        return
    
    # Create config
    config = CloudConfig(
        provider=CloudProvider.BROWSERSTACK,
        username=bs_username,
        access_key=bs_access_key,
        project_name="WebPilot Cloud Test",
        video_recording=True,
        network_logs=True
    )
    
    # Create cloud pilot
    with CloudWebPilot(config, browser="chrome", os_name="Windows", os_version="11") as pilot:
        # Run test
        print("🌩️  Starting cloud browser test...")
        result = pilot.start("https://example.com")
        
        if result.success:
            print(f"✅ Browser started: {result.data.get('browser')} on {result.data.get('os')}")
            print(f"📺 Session URL: {pilot.get_session_url()}")
            
            # Take screenshot
            screenshot = pilot.screenshot("cloud_test.png")
            print(f"📸 Screenshot: {'✅' if screenshot.success else '❌'}")
            
            # Enable network throttling
            throttle = pilot.enable_network_throttling('Regular3G')
            print(f"🐌 Network throttling: {'✅' if throttle.success else '❌'}")
            
            # Mark test as passed
            pilot.mark_test_status(True, "Test completed successfully")
            
        else:
            print(f"❌ Failed to start cloud browser: {result.error}")
            pilot.mark_test_status(False, result.error)


if __name__ == "__main__":
    test_cloud_browsers()
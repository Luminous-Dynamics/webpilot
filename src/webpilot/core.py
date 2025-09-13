#!/usr/bin/env python3
"""
Claude WebPilot - Professional Web Automation Framework.

A production-ready tool for web interaction and automation with support for
multiple browsers, session management, and comprehensive error handling.

Version: 1.1.0
"""

import json
import time
import base64
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import hashlib
import pickle

# Import our custom logging configuration
from webpilot.utils.logging_config import get_logger, setup_logging

# Setup logging with our configuration
setup_logging(level='INFO', console=True, file=True)
logger = get_logger(__name__)


# Custom Exceptions
class WebPilotError(Exception):
    """Base exception for WebPilot"""
    pass


class BrowserNotStartedError(WebPilotError):
    """Raised when browser operations attempted before start"""
    pass


class ElementNotFoundError(WebPilotError):
    """Raised when element cannot be located"""
    pass


class TimeoutError(WebPilotError):
    """Raised when operation times out"""
    pass


class SessionError(WebPilotError):
    """Raised when session operations fail"""
    pass


class NetworkError(WebPilotError):
    """Raised when network operations fail"""
    pass


class BrowserType(Enum):
    """Supported browser types"""
    FIREFOX = "firefox"
    CHROME = "chrome"
    CHROMIUM = "chromium"
    SAFARI = "safari"


class ActionType(Enum):
    """Types of actions that can be performed"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCREENSHOT = "screenshot"
    SCROLL = "scroll"
    WAIT = "wait"
    EXECUTE_JS = "execute_js"
    EXTRACT = "extract"
    SUBMIT = "submit"
    SELECT = "select"
    CLOSE = "close"
    UNKNOWN = "unknown"
    SCRIPT = "script"
    HOVER = "hover"
    DRAG = "drag"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    CLEAR = "clear"
    REFRESH = "refresh"
    BACK = "back"
    FORWARD = "forward"


@dataclass
class WebElement:
    """Represents a web element"""
    tag: str
    text: str
    attributes: Dict[str, str]
    position: Tuple[int, int]
    size: Tuple[int, int]
    is_visible: bool
    is_clickable: bool
    xpath: str = ""
    css_selector: str = ""


@dataclass
class ActionResult:
    """Result of an action"""
    success: bool
    action_type: ActionType
    data: Any = None
    error: Optional[str] = None
    timestamp: datetime = None
    duration_ms: float = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['action_type'] = self.action_type.value
        return result


class WebPilotSession:
    """
    Manages a browser session with state persistence.
    
    This class handles session management including state persistence,
    screenshot storage, logging, and action history tracking.
    
    Attributes:
        session_id: Unique identifier for the session
        session_dir: Directory for session files
        state_file: Path to session state JSON file
        screenshot_dir: Directory for screenshots
        log_file: Path to session log file
        state: Current session state dictionary
        logger: Session-specific logger instance
    """
    
    def __init__(self, session_id: Optional[str] = None) -> None:
        """
        Initialize a new WebPilot session.
        
        Args:
            session_id: Optional custom session ID. If not provided,
                       a unique ID will be generated.
        """
        self.session_id: str = session_id or self._generate_session_id()
        self.session_dir: Path = Path(f"/tmp/webpilot-sessions/{self.session_id}")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file: Path = self.session_dir / "state.json"
        self.screenshot_dir: Path = self.session_dir / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)
        self.log_file: Path = self.session_dir / "session.log"
        self._setup_logging()
        self.state: Dict[str, Any] = self._load_state()
        
    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID.
        
        Returns:
            A unique session ID string with timestamp and hash.
        """
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash: str = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"{timestamp}_{random_hash}"
        
    def _setup_logging(self):
        """Setup session-specific logging"""
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger = logging.getLogger(f'WebPilot.{self.session_id}')
        self.logger.addHandler(handler)
        
    def _load_state(self) -> Dict:
        """Load session state from disk"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'session_id': self.session_id,
            'created_at': datetime.now().isoformat(),
            'browser_pid': None,
            'current_url': None,
            'action_history': [],
            'screenshots': [],
            'extracted_data': {}
        }
        
    def save_state(self):
        """Save session state to disk"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    def add_action(self, result: ActionResult):
        """Add action to history"""
        self.state['action_history'].append(result.to_dict())
        self.save_state()
        
    def get_screenshot_path(self, name: Optional[str] = None) -> Path:
        """Get path for screenshot"""
        if not name:
            name = f"screenshot_{int(time.time())}.png"
        return self.screenshot_dir / name


class WebPilot:
    """Main WebPilot automation class"""
    
    def __init__(self, 
                 browser: BrowserType = BrowserType.FIREFOX,
                 headless: bool = False,
                 session: Optional[WebPilotSession] = None):
        self.browser = browser
        self.headless = headless
        self.session = session or WebPilotSession()
        self.logger = self.session.logger
        self.browser_process = None
        self._xdotool_available = self._check_xdotool()
        
    def _check_xdotool(self) -> bool:
        """Check if xdotool is available"""
        try:
            subprocess.run(["which", "xdotool"], 
                         capture_output=True, check=True)
            return True
        except:
            self.logger.warning("xdotool not available - some features limited")
            return False
            
    def start(self, url: str = "about:blank") -> ActionResult:
        """Start browser and navigate to URL"""
        start_time = time.time()
        
        try:
            # Prepare browser command
            if self.browser == BrowserType.FIREFOX:
                cmd = ["firefox"]
                if self.headless:
                    cmd.extend(["--headless"])
                cmd.append(url)
            elif self.browser == BrowserType.CHROME:
                cmd = ["google-chrome", "--no-sandbox"]
                if self.headless:
                    cmd.extend(["--headless"])
                cmd.append(url)
            else:
                return ActionResult(
                    success=False,
                    action_type=ActionType.NAVIGATE,
                    error=f"Unsupported browser: {self.browser}"
                )
                
            # Start browser
            self.browser_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.session.state['browser_pid'] = self.browser_process.pid
            self.session.state['current_url'] = url
            self.session.save_state()
            
            # Wait for browser to load
            time.sleep(3)
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={'url': url, 'pid': self.browser_process.pid},
                duration_ms=duration
            )
            
            self.logger.info(f"Browser started: {url} (PID: {self.browser_process.pid})")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                error=str(e)
            )
            
    def navigate(self, url: str) -> ActionResult:
        """Navigate to a URL"""
        start_time = time.time()
        
        try:
            if self._xdotool_available:
                # Use xdotool to navigate in existing window
                window_id = self._get_browser_window()
                if window_id:
                    subprocess.run(["xdotool", "windowfocus", window_id])
                    subprocess.run(["xdotool", "key", "ctrl+l"])
                    time.sleep(0.5)
                    subprocess.run(["xdotool", "key", "ctrl+a"])
                    subprocess.run(["xdotool", "type", url])
                    subprocess.run(["xdotool", "key", "Return"])
                else:
                    # Open in new window
                    subprocess.run([self.browser.value, url])
            else:
                # Fallback: open in new window/tab
                subprocess.run([self.browser.value, url])
                
            time.sleep(2)  # Wait for navigation
            
            self.session.state['current_url'] = url
            self.session.save_state()
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={'url': url},
                duration_ms=duration
            )
            
            self.logger.info(f"Navigated to: {url}")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                error=str(e)
            )
            
    def screenshot(self, name: Optional[str] = None) -> ActionResult:
        """Take a screenshot"""
        start_time = time.time()
        
        try:
            filepath = self.session.get_screenshot_path(name)
            
            # Try different screenshot methods
            success = False
            
            # Method 1: Firefox built-in screenshot
            if self.browser == BrowserType.FIREFOX:
                result = subprocess.run(
                    ["firefox", "--screenshot", str(filepath), 
                     self.session.state.get('current_url', 'about:blank')],
                    capture_output=True,
                    timeout=10
                )
                success = filepath.exists()
                
            # Method 2: xdotool + import
            if not success and self._xdotool_available:
                window_id = self._get_browser_window()
                if window_id:
                    subprocess.run(
                        ["import", "-window", window_id, str(filepath)],
                        capture_output=True
                    )
                    success = filepath.exists()
                    
            # Method 3: Full screen screenshot
            if not success:
                subprocess.run(
                    ["import", "-window", "root", str(filepath)],
                    capture_output=True
                )
                success = filepath.exists()
                
            if success:
                # Save screenshot info
                self.session.state['screenshots'].append({
                    'path': str(filepath),
                    'timestamp': datetime.now().isoformat(),
                    'url': self.session.state.get('current_url')
                })
                self.session.save_state()
                
                duration = (time.time() - start_time) * 1000
                
                result = ActionResult(
                    success=True,
                    action_type=ActionType.SCREENSHOT,
                    data={'path': str(filepath), 'size': filepath.stat().st_size},
                    duration_ms=duration
                )
                
                self.logger.info(f"Screenshot saved: {filepath}")
                self.session.add_action(result)
                return result
            else:
                raise Exception("All screenshot methods failed")
                
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SCREENSHOT,
                error=str(e)
            )
            
    def click(self, x: Optional[int] = None, y: Optional[int] = None,
              text: Optional[str] = None, selector: Optional[str] = None) -> ActionResult:
        """Click on an element"""
        start_time = time.time()
        
        if not self._xdotool_available:
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK,
                error="xdotool required for clicking"
            )
            
        try:
            window_id = self._get_browser_window()
            if window_id:
                subprocess.run(["xdotool", "windowfocus", window_id])
                
            if x is not None and y is not None:
                subprocess.run(["xdotool", "mousemove", str(x), str(y)])
                subprocess.run(["xdotool", "click", "1"])
                target = f"({x}, {y})"
            else:
                # For text/selector, we'd need more advanced detection
                # For now, just click at current position
                subprocess.run(["xdotool", "click", "1"])
                target = "current position"
                
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.CLICK,
                data={'target': target},
                duration_ms=duration
            )
            
            self.logger.info(f"Clicked: {target}")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK,
                error=str(e)
            )
            
    def type_text(self, text: str, clear_first: bool = False) -> ActionResult:
        """Type text into the focused element"""
        start_time = time.time()
        
        if not self._xdotool_available:
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                error="xdotool required for typing"
            )
            
        try:
            if clear_first:
                subprocess.run(["xdotool", "key", "ctrl+a"])
                time.sleep(0.1)
                
            subprocess.run(["xdotool", "type", text])
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.TYPE,
                data={'text': text, 'cleared': clear_first},
                duration_ms=duration
            )
            
            self.logger.info(f"Typed: {text[:50]}...")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Type failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                error=str(e)
            )
            
    def press_key(self, key: str) -> ActionResult:
        """Press a key or key combination"""
        start_time = time.time()
        
        if not self._xdotool_available:
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                error="xdotool required"
            )
            
        try:
            subprocess.run(["xdotool", "key", key])
            
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.TYPE,
                data={'key': key},
                duration_ms=duration
            )
            
            self.logger.info(f"Pressed key: {key}")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Key press failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE,
                error=str(e)
            )
            
    def scroll(self, direction: str = "down", amount: int = 3) -> ActionResult:
        """Scroll the page"""
        start_time = time.time()
        
        if not self._xdotool_available:
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL,
                error="xdotool required"
            )
            
        try:
            window_id = self._get_browser_window()
            if window_id:
                subprocess.run(["xdotool", "windowfocus", window_id])
                
            if direction == "down":
                button = "5"
            elif direction == "up":
                button = "4"
            else:
                # Use keyboard
                key_map = {
                    "top": "Home",
                    "bottom": "End",
                    "pagedown": "Page_Down",
                    "pageup": "Page_Up"
                }
                if direction in key_map:
                    subprocess.run(["xdotool", "key", key_map[direction]])
                    
                duration = (time.time() - start_time) * 1000
                
                result = ActionResult(
                    success=True,
                    action_type=ActionType.SCROLL,
                    data={'direction': direction},
                    duration_ms=duration
                )
                
                self.logger.info(f"Scrolled: {direction}")
                self.session.add_action(result)
                return result
                
            # Mouse wheel scroll
            for _ in range(amount):
                subprocess.run(["xdotool", "click", button])
                time.sleep(0.1)
                
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.SCROLL,
                data={'direction': direction, 'amount': amount},
                duration_ms=duration
            )
            
            self.logger.info(f"Scrolled: {direction} x{amount}")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Scroll failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL,
                error=str(e)
            )
            
    def wait(self, seconds: float) -> ActionResult:
        """Wait for specified seconds"""
        start_time = time.time()
        time.sleep(seconds)
        duration = (time.time() - start_time) * 1000
        
        result = ActionResult(
            success=True,
            action_type=ActionType.WAIT,
            data={'seconds': seconds},
            duration_ms=duration
        )
        
        self.logger.info(f"Waited: {seconds}s")
        self.session.add_action(result)
        return result
        
    def extract_page_content(self) -> ActionResult:
        """Extract page content (requires additional setup)"""
        start_time = time.time()
        
        try:
            # For now, download the page HTML
            url = self.session.state.get('current_url', '')
            if url:
                result = subprocess.run(
                    ["curl", "-s", url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                content = result.stdout[:1000]  # First 1000 chars
                
                duration = (time.time() - start_time) * 1000
                
                result = ActionResult(
                    success=True,
                    action_type=ActionType.EXTRACT,
                    data={'content_preview': content, 'length': len(result.stdout)},
                    duration_ms=duration
                )
                
                self.logger.info(f"Extracted content: {len(result.stdout)} bytes")
                self.session.add_action(result)
                return result
            else:
                raise Exception("No current URL")
                
        except Exception as e:
            self.logger.error(f"Extract failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.EXTRACT,
                error=str(e)
            )
            
    def close(self) -> ActionResult:
        """Close the browser"""
        start_time = time.time()
        
        try:
            if self.browser_process:
                self.browser_process.terminate()
                self.browser_process.wait(timeout=5)
            elif self.session.state.get('browser_pid'):
                subprocess.run(["kill", str(self.session.state['browser_pid'])])
                
            # Try xdotool close
            if self._xdotool_available:
                window_id = self._get_browser_window()
                if window_id:
                    subprocess.run(["xdotool", "windowclose", window_id])
                    
            duration = (time.time() - start_time) * 1000
            
            result = ActionResult(
                success=True,
                action_type=ActionType.NAVIGATE,
                data={'action': 'closed'},
                duration_ms=duration
            )
            
            self.logger.info("Browser closed")
            self.session.add_action(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Close failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.NAVIGATE,
                error=str(e)
            )
            
    def _get_browser_window(self) -> Optional[str]:
        """Get browser window ID"""
        if not self._xdotool_available:
            return None
            
        try:
            # Try to find by PID first
            if self.session.state.get('browser_pid'):
                result = subprocess.run(
                    ["xdotool", "search", "--pid", 
                     str(self.session.state['browser_pid'])],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    return result.stdout.strip().split('\n')[-1]
                    
            # Try to find by class
            for browser_class in ["firefox", "Firefox", "Chrome", "chrome"]:
                result = subprocess.run(
                    ["xdotool", "search", "--class", browser_class],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    return result.stdout.strip().split('\n')[0]
                    
        except:
            pass
            
        return None
        
    def get_session_report(self) -> Dict:
        """Get comprehensive session report"""
        return {
            'session_id': self.session.session_id,
            'created_at': self.session.state.get('created_at'),
            'current_url': self.session.state.get('current_url'),
            'total_actions': len(self.session.state.get('action_history', [])),
            'screenshots_taken': len(self.session.state.get('screenshots', [])),
            'session_dir': str(self.session.session_dir),
            'log_file': str(self.session.log_file)
        }


# Convenience functions for quick automation
def quick_browse(url: str) -> WebPilot:
    """Quick function to start browsing"""
    pilot = WebPilot()
    pilot.start(url)
    return pilot


def batch_screenshots(urls: List[str], output_dir: str = "/tmp/screenshots") -> List[str]:
    """Take screenshots of multiple URLs"""
    pilot = WebPilot()
    screenshots = []
    
    for url in urls:
        pilot.navigate(url)
        pilot.wait(2)
        result = pilot.screenshot(f"{url.replace('/', '_')}.png")
        if result.success:
            screenshots.append(result.data['path'])
            
    pilot.close()
    return screenshots
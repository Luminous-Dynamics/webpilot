#!/usr/bin/env python3
"""
Smart Wait Strategies for WebPilot
Intelligent waiting for dynamic content
"""

import time
import logging
from typing import Optional, Callable, Any
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logger = logging.getLogger('WebPilot.SmartWait')


class SmartWait:
    """Intelligent waiting strategies for dynamic content"""
    
    @staticmethod
    def wait_for_network_idle(driver, timeout: int = 30, idle_time: float = 0.5) -> bool:
        """
        Wait for network requests to complete
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to wait in seconds
            idle_time: Time with no network activity to consider idle
            
        Returns:
            True if network became idle, False if timeout
        """
        start_time = time.time()
        last_request_count = 0
        idle_start = None
        
        while time.time() - start_time < timeout:
            # Execute JavaScript to check for pending requests
            pending_requests = driver.execute_script("""
                return (function() {
                    // Check for fetch/XHR requests
                    if (window.performance && window.performance.getEntriesByType) {
                        return window.performance.getEntriesByType('resource').filter(
                            r => r.responseEnd === 0
                        ).length;
                    }
                    return 0;
                })();
            """)
            
            if pending_requests == 0:
                if idle_start is None:
                    idle_start = time.time()
                elif time.time() - idle_start >= idle_time:
                    logger.debug(f"Network idle after {time.time() - start_time:.1f}s")
                    return True
            else:
                idle_start = None
                
            time.sleep(0.1)
        
        logger.warning(f"Network idle timeout after {timeout}s")
        return False
    
    @staticmethod
    def wait_for_animation_complete(driver, selector: str, timeout: int = 10) -> bool:
        """
        Wait for CSS animations to finish on an element
        
        Args:
            driver: Selenium WebDriver instance
            selector: CSS selector for the element
            timeout: Maximum time to wait
            
        Returns:
            True if animations completed, False if timeout
        """
        script = f"""
            return (function() {{
                const element = document.querySelector('{selector}');
                if (!element) return false;
                
                const style = window.getComputedStyle(element);
                const duration = parseFloat(style.animationDuration || '0');
                const delay = parseFloat(style.animationDelay || '0');
                const transitionDuration = parseFloat(style.transitionDuration || '0');
                
                return (duration + delay + transitionDuration) === 0;
            }})();
        """
        
        wait = WebDriverWait(driver, timeout)
        try:
            wait.until(lambda d: d.execute_script(script))
            logger.debug(f"Animation complete for {selector}")
            return True
        except:
            logger.warning(f"Animation timeout for {selector}")
            return False
    
    @staticmethod
    def wait_for_element_stable(driver, selector: str, timeout: int = 10, 
                                check_interval: float = 0.5) -> bool:
        """
        Wait for an element to stop moving/resizing
        
        Args:
            driver: Selenium WebDriver instance
            selector: CSS selector for the element
            timeout: Maximum time to wait
            check_interval: Time between position checks
            
        Returns:
            True if element became stable, False if timeout
        """
        start_time = time.time()
        last_position = None
        last_size = None
        
        while time.time() - start_time < timeout:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                current_position = element.location
                current_size = element.size
                
                if last_position == current_position and last_size == current_size:
                    logger.debug(f"Element {selector} is stable")
                    return True
                
                last_position = current_position
                last_size = current_size
                
            except:
                pass
            
            time.sleep(check_interval)
        
        logger.warning(f"Element {selector} stability timeout")
        return False
    
    @staticmethod
    def wait_for_custom_condition(driver, condition: Callable[[Any], bool], 
                                  timeout: int = 30, poll_frequency: float = 0.5) -> bool:
        """
        Wait for a custom condition to be true
        
        Args:
            driver: Selenium WebDriver instance
            condition: Callable that returns True when condition is met
            timeout: Maximum time to wait
            poll_frequency: How often to check the condition
            
        Returns:
            True if condition was met, False if timeout
        """
        wait = WebDriverWait(driver, timeout, poll_frequency=poll_frequency)
        try:
            wait.until(condition)
            return True
        except:
            return False
    
    @staticmethod
    def wait_for_page_ready(driver, timeout: int = 30) -> bool:
        """
        Wait for page to be fully loaded (document ready + jQuery if present)
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to wait
            
        Returns:
            True if page is ready, False if timeout
        """
        def page_ready(driver):
            ready_state = driver.execute_script("return document.readyState")
            jquery_ready = driver.execute_script("""
                if (typeof jQuery !== 'undefined') {
                    return jQuery.active === 0;
                }
                return true;
            """)
            return ready_state == "complete" and jquery_ready
        
        wait = WebDriverWait(driver, timeout)
        try:
            wait.until(page_ready)
            logger.debug("Page is ready")
            return True
        except:
            logger.warning("Page ready timeout")
            return False
    
    @staticmethod
    def wait_for_text_present(driver, text: str, timeout: int = 10) -> bool:
        """
        Wait for specific text to appear anywhere on the page
        
        Args:
            driver: Selenium WebDriver instance
            text: Text to wait for
            timeout: Maximum time to wait
            
        Returns:
            True if text appeared, False if timeout
        """
        wait = WebDriverWait(driver, timeout)
        try:
            wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))
            logger.debug(f"Text '{text}' found on page")
            return True
        except:
            logger.warning(f"Text '{text}' not found within {timeout}s")
            return False
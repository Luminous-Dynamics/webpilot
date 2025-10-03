#!/usr/bin/env python3
"""
WebPilot v2.0 - Integrated Real Automation
Combines all working components into a unified tool.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.webpilot.core import RealBrowserAutomation  # Now uses Playwright!
from email_automation import EmailAutomation
from claude_dev_assistant import ClaudeDevAssistant


class WebPilot:
    """
    WebPilot v2.0 - Real browser automation that actually works.
    No AI hype, just practical tools for development and productivity.
    """
    
    def __init__(self):
        self.browser = None
        self.email = None
        self.assistant = None
        self.session_dir = Path("webpilot_sessions")
        self.session_dir.mkdir(exist_ok=True)
        self.current_session = None
        
    # ============================================
    # Core Browser Automation
    # ============================================
    
    def start_browser(self, headless: bool = False) -> bool:
        """Start browser for automation."""
        if not self.browser:
            self.browser = RealBrowserAutomation(headless=headless)
        return self.browser.start()
    
    def navigate(self, url: str) -> bool:
        """Navigate to URL."""
        if not self.browser:
            self.start_browser()
        return self.browser.navigate(url)
    
    def click(self, element: str) -> bool:
        """Click an element."""
        if not self.browser:
            return False
        return self.browser.click(element)
    
    def type_text(self, text: str, field: Optional[str] = None) -> bool:
        """Type text in a field."""
        if not self.browser:
            return False
        return self.browser.type_text(text, field)
    
    def screenshot(self, name: Optional[str] = None) -> str:
        """Take screenshot."""
        if not self.browser:
            return ""
        return self.browser.screenshot(name)
    
    # ============================================
    # Email Automation
    # ============================================
    
    def start_email(self, provider: str = 'gmail') -> EmailAutomation:
        """Start email automation."""
        if not self.email:
            self.email = EmailAutomation(provider)
        return self.email
    
    def check_emails(self, limit: int = 10) -> List[Dict]:
        """Quick email check."""
        if not self.email:
            print("❌ Email not initialized. Use start_email() first.")
            return []
        return self.email.check_inbox(limit)
    
    # ============================================
    # Development Assistant (for Claude)
    # ============================================
    
    def start_assistant(self) -> ClaudeDevAssistant:
        """Start Claude development assistant."""
        if not self.assistant:
            self.assistant = ClaudeDevAssistant()
        return self.assistant
    
    def capture_screen_for_claude(self, annotation: str = None) -> str:
        """Capture screen so Claude can see."""
        if not self.assistant:
            self.start_assistant()
        return self.assistant.capture_screen(annotate=annotation)
    
    def test_web_app(self, url: str, tests: List[Dict]) -> Dict:
        """Test a web application."""
        if not self.assistant:
            self.start_assistant()
        return self.assistant.test_web_app(url, tests)
    
    def verify_code(self, command: str, expected: str = None) -> Dict:
        """Verify code output."""
        if not self.assistant:
            self.start_assistant()
        return self.assistant.verify_code_output(command, expected)
    
    # ============================================
    # Session Management
    # ============================================
    
    def start_session(self, name: str = None) -> str:
        """Start a new automation session."""
        if not name:
            name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = {
            'name': name,
            'started': datetime.now().isoformat(),
            'actions': [],
            'screenshots': [],
            'results': {}
        }
        
        print(f"📝 Session started: {name}")
        return name
    
    def log_action(self, action: str, result: Any):
        """Log an action in the current session."""
        if self.current_session:
            self.current_session['actions'].append({
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'result': str(result)
            })
    
    def save_session(self) -> str:
        """Save the current session."""
        if not self.current_session:
            return ""
        
        filename = self.session_dir / f"{self.current_session['name']}.json"
        with open(filename, 'w') as f:
            json.dump(self.current_session, f, indent=2)
        
        print(f"💾 Session saved: {filename}")
        return str(filename)
    
    # ============================================
    # Utility Functions
    # ============================================
    
    def check_website_status(self, urls: List[str]) -> Dict[str, Dict]:
        """Check status of multiple websites."""
        if not self.browser:
            self.start_browser(headless=True)
        
        results = {}
        for url in urls:
            if self.browser.navigate(url):
                results[url] = {
                    'status': 'UP',
                    'title': self.browser.get_title(),
                    'screenshot': self.browser.screenshot(f"{url.replace('.', '_')}")
                }
            else:
                results[url] = {
                    'status': 'DOWN',
                    'title': None,
                    'screenshot': None
                }
        
        return results
    
    def extract_links(self) -> List[str]:
        """Extract all links from current page."""
        if not self.browser:
            return []
        
        script = """
        return Array.from(document.querySelectorAll('a[href]'))
            .map(a => a.href)
            .filter(href => href.startsWith('http'));
        """
        links = self.browser.execute_script(script)
        return links if links else []
    
    def fill_form(self, form_data: Dict[str, str]) -> bool:
        """Fill a form with provided data."""
        if not self.browser:
            return False
        
        success = True
        for field, value in form_data.items():
            if not self.browser.type_text(value, field):
                success = False
                print(f"⚠️  Failed to fill field: {field}")
        
        return success
    
    def wait_and_screenshot(self, element: str, timeout: int = 10) -> str:
        """Wait for element and take screenshot."""
        if not self.browser:
            return ""
        
        if self.browser.wait_for(element, timeout):
            return self.browser.screenshot(f"found_{element.replace(' ', '_')}")
        else:
            return self.browser.screenshot("timeout")
    
    # ============================================
    # Cleanup
    # ============================================
    
    def cleanup(self):
        """Clean up all resources."""
        if self.browser:
            self.browser.close()
        if self.email:
            self.email.logout()
        if self.assistant:
            self.assistant.cleanup()
        if self.current_session:
            self.save_session()
        
        print("✅ WebPilot cleaned up")


# ============================================
# Practical Usage Examples
# ============================================

def example_dev_workflow():
    """Example: Development workflow automation."""
    
    pilot = WebPilot()
    pilot.start_session("dev_workflow")
    
    # 1. Check if dev server is running
    print("\n1️⃣ Checking dev server...")
    result = pilot.verify_code("curl -s http://localhost:3000", "<!DOCTYPE")
    pilot.log_action("check_dev_server", result['success'])
    
    # 2. Take screenshot for Claude
    print("\n2️⃣ Capturing screen for Claude...")
    screenshot = pilot.capture_screen_for_claude("Current dev state")
    pilot.log_action("screenshot_for_claude", screenshot)
    
    # 3. Run tests on the app
    print("\n3️⃣ Testing web app...")
    tests = [
        {"action": "navigate", "url": "http://localhost:3000"},
        {"action": "screenshot", "name": "homepage"},
        {"action": "click", "element": "Login"},
        {"action": "screenshot", "name": "login_page"},
        {"action": "verify", "text": "Sign In"}
    ]
    test_results = pilot.test_web_app("http://localhost:3000", tests)
    pilot.log_action("web_app_tests", test_results['success'])
    
    # 4. Check GitHub for updates
    print("\n4️⃣ Checking GitHub...")
    pilot.navigate("https://github.com/yourusername/yourrepo")
    pilot.screenshot("github_repo")
    
    pilot.save_session()
    pilot.cleanup()


def example_monitoring():
    """Example: Website monitoring."""
    
    pilot = WebPilot()
    pilot.start_session("monitoring")
    
    sites = [
        "github.com",
        "stackoverflow.com",
        "localhost:3000",
        "myapp.com"
    ]
    
    print("\n🔍 Monitoring websites...")
    results = pilot.check_website_status(sites)
    
    for site, status in results.items():
        if status['status'] == 'UP':
            print(f"✅ {site} - {status['title'][:50]}")
        else:
            print(f"❌ {site} - DOWN")
    
    pilot.log_action("monitoring_results", results)
    pilot.save_session()
    pilot.cleanup()


def example_form_automation():
    """Example: Form filling automation."""
    
    pilot = WebPilot()
    pilot.start_browser(headless=False)  # Visible for form filling
    pilot.start_session("form_automation")
    
    # Navigate to form
    pilot.navigate("https://example-form.com")
    
    # Fill form
    form_data = {
        "First Name": "John",
        "Last Name": "Doe",
        "Email": "john.doe@example.com",
        "Phone": "555-0123",
        "Message": "This is an automated test message."
    }
    
    print("\n📝 Filling form...")
    if pilot.fill_form(form_data):
        print("✅ Form filled successfully")
        pilot.screenshot("filled_form")
    
    # Submit (commented out for safety)
    # pilot.click("Submit")
    # pilot.wait_and_screenshot("Thank you", 10)
    
    pilot.save_session()
    pilot.cleanup()


def main_menu():
    """Interactive menu for WebPilot v2.0."""
    
    print("\n" + "=" * 60)
    print("   WebPilot v2.0 - Real Automation That Works")
    print("=" * 60)
    
    print("\nChoose an option:")
    print("1. Development Workflow Assistant")
    print("2. Website Monitoring")
    print("3. Form Automation Demo")
    print("4. Email Automation (requires credentials)")
    print("5. Custom Browser Session")
    print("6. Exit")
    
    choice = input("\nYour choice (1-6): ").strip()
    
    if choice == "1":
        example_dev_workflow()
    elif choice == "2":
        example_monitoring()
    elif choice == "3":
        example_form_automation()
    elif choice == "4":
        print("\n⚠️  Email automation requires valid credentials")
        print("See email_automation.py for setup")
    elif choice == "5":
        pilot = WebPilot()
        pilot.start_browser(headless=False)
        print("\nBrowser started. WebPilot instance available as 'pilot'")
        print("Try: pilot.navigate('github.com')")
        print("     pilot.screenshot()")
        print("     pilot.click('Sign in')")
        # This would typically drop into an interactive shell
    elif choice == "6":
        print("\n👋 Goodbye!")
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    main_menu()
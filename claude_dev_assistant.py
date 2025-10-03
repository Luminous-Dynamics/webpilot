#!/usr/bin/env python3
"""
Claude Development Assistant
Tools that let Claude see your screen and verify code actually works.
This creates REAL value for our development workflow.
"""

import os
import time
import json
import base64
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    from PIL import Image, ImageGrab, ImageDraw, ImageFont
    import mss
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL/mss not available. Install with: pip install Pillow mss")

from src.webpilot.core import RealBrowserAutomation  # Now uses Playwright!


class ClaudeDevAssistant:
    """
    Tools that help Claude be a better development partner.
    """
    
    def __init__(self):
        self.screenshots_dir = Path("claude_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.test_results_dir = Path("claude_test_results")
        self.test_results_dir.mkdir(exist_ok=True)
        self.browser = None
        
    # ============================================
    # SCREEN CAPTURE - So Claude can see
    # ============================================
    
    def capture_screen(self, monitor: int = 1, annotate: str = None) -> str:
        """Capture the entire screen or specific monitor."""
        if not PIL_AVAILABLE:
            return "❌ Screen capture not available (install: pip install Pillow mss)"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshots_dir / f"screen_{timestamp}.png"
        
        try:
            with mss.mss() as sct:
                # Get the specified monitor
                monitor_info = sct.monitors[monitor]
                screenshot = sct.grab(monitor_info)
                
                # Convert to PIL Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                
                # Add annotation if requested
                if annotate:
                    draw = ImageDraw.Draw(img)
                    # Add text overlay
                    draw.rectangle([(10, 10), (500, 50)], fill='black')
                    draw.text((20, 20), annotate, fill='white')
                
                # Save
                img.save(filename)
                
                # Also save a "latest" version for easy access
                latest = self.screenshots_dir / "latest_screen.png"
                img.save(latest)
                
                return f"✅ Screen captured: {filename} ({img.width}x{img.height})"
        except Exception as e:
            return f"❌ Failed to capture screen: {e}"
    
    def capture_window(self, title_contains: str = None) -> str:
        """Capture a specific window by title."""
        # This would need platform-specific implementation
        # For now, we'll use full screen capture
        return self.capture_screen(annotate=f"Window: {title_contains}")
    
    # ============================================
    # WEB APP TESTING - For PWA/Tauri development
    # ============================================
    
    def test_web_app(self, url: str, tests: List[Dict]) -> Dict:
        """
        Run automated tests on a web app and capture results.
        
        tests = [
            {"action": "navigate", "url": "localhost:3000"},
            {"action": "click", "element": "Login"},
            {"action": "type", "text": "user@test.com", "element": "email"},
            {"action": "screenshot", "name": "after_login"},
            {"action": "verify", "text": "Dashboard"}
        ]
        """
        if not self.browser:
            self.browser = RealBrowserAutomation(headless=False)  # Visible for debugging
            self.browser.start()
        
        results = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "success": True,
            "screenshots": []
        }
        
        # Navigate to the app
        self.browser.navigate(url)
        time.sleep(2)  # Let it load
        
        # Run each test
        for i, test in enumerate(tests):
            test_result = {
                "test": test,
                "success": False,
                "message": "",
                "screenshot": None
            }
            
            try:
                if test["action"] == "navigate":
                    success = self.browser.navigate(test["url"])
                    test_result["success"] = success
                    test_result["message"] = f"Navigated to {test['url']}"
                    
                elif test["action"] == "click":
                    success = self.browser.click(test["element"])
                    test_result["success"] = success
                    test_result["message"] = f"Clicked {test['element']}"
                    
                elif test["action"] == "type":
                    success = self.browser.type_text(test["text"], test.get("element"))
                    test_result["success"] = success
                    test_result["message"] = f"Typed text"
                    
                elif test["action"] == "screenshot":
                    name = test.get("name", f"test_{i}")
                    screenshot = self.browser.screenshot(name)
                    test_result["success"] = bool(screenshot)
                    test_result["screenshot"] = screenshot
                    results["screenshots"].append(screenshot)
                    
                elif test["action"] == "verify":
                    page_text = self.browser.get_text()
                    success = test["text"] in page_text
                    test_result["success"] = success
                    test_result["message"] = f"Text {'found' if success else 'not found'}"
                    
                elif test["action"] == "wait":
                    time.sleep(test.get("seconds", 1))
                    test_result["success"] = True
                    test_result["message"] = f"Waited {test.get('seconds', 1)} seconds"
                    
            except Exception as e:
                test_result["message"] = f"Error: {str(e)}"
                results["success"] = False
            
            results["tests"].append(test_result)
            
            # Stop on failure if requested
            if not test_result["success"] and test.get("stop_on_failure", False):
                break
        
        # Save results
        results_file = self.test_results_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
    
    # ============================================
    # CODE VERIFICATION - Test what Claude writes
    # ============================================
    
    def verify_code_output(self, command: str, expected_output: str = None) -> Dict:
        """Run a command and verify its output."""
        result = {
            "command": command,
            "success": False,
            "output": "",
            "error": "",
            "screenshot": None
        }
        
        try:
            # Run the command
            process = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            result["output"] = process.stdout
            result["error"] = process.stderr
            result["success"] = process.returncode == 0
            
            # Check expected output if provided
            if expected_output and expected_output in result["output"]:
                result["message"] = "✅ Output contains expected text"
            elif expected_output:
                result["message"] = "❌ Expected text not found in output"
                result["success"] = False
            
            # Take a screenshot if it's a web-related command
            if any(word in command.lower() for word in ['npm', 'yarn', 'serve', 'start', 'dev']):
                time.sleep(3)  # Let server start
                result["screenshot"] = self.capture_screen(annotate=f"After: {command}")
            
        except subprocess.TimeoutExpired:
            result["error"] = "Command timed out after 30 seconds"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    # ============================================
    # DEVELOPMENT SERVER TESTING
    # ============================================
    
    def test_dev_server(self, start_command: str, url: str, tests: List[Dict]) -> Dict:
        """Start a dev server, run tests, then kill it."""
        result = {
            "command": start_command,
            "url": url,
            "server_started": False,
            "test_results": None,
            "server_output": ""
        }
        
        try:
            # Start the dev server in background
            process = subprocess.Popen(
                start_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            print(f"⏳ Starting dev server with: {start_command}")
            time.sleep(5)  # Give it time to start
            
            # Check if server is running
            if process.poll() is None:
                result["server_started"] = True
                print(f"✅ Server started, testing at {url}")
                
                # Run the tests
                result["test_results"] = self.test_web_app(url, tests)
                
                # Capture server output
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    result["server_output"] = stdout + stderr
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    result["server_output"] = stdout + stderr
            else:
                result["error"] = "Server failed to start"
                stdout, stderr = process.communicate()
                result["server_output"] = stdout + stderr
                
        except Exception as e:
            result["error"] = str(e)
        finally:
            # Make sure process is killed
            try:
                process.kill()
            except:
                pass
        
        return result
    
    # ============================================
    # VISUAL REGRESSION TESTING
    # ============================================
    
    def compare_screenshots(self, before: str, after: str) -> Dict:
        """Compare two screenshots and highlight differences."""
        if not PIL_AVAILABLE:
            return {"error": "PIL not available"}
        
        try:
            img1 = Image.open(before)
            img2 = Image.open(after)
            
            # Ensure same size
            if img1.size != img2.size:
                return {
                    "different_sizes": True,
                    "size1": img1.size,
                    "size2": img2.size
                }
            
            # Simple pixel difference
            from PIL import ImageChops
            diff = ImageChops.difference(img1, img2)
            
            # Calculate difference percentage
            pixels = list(diff.getdata())
            different_pixels = sum(1 for p in pixels if p != (0, 0, 0))
            total_pixels = len(pixels)
            diff_percentage = (different_pixels / total_pixels) * 100
            
            # Save diff image if there are differences
            if different_pixels > 0:
                diff_file = self.screenshots_dir / f"diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                diff.save(diff_file)
                
                return {
                    "identical": False,
                    "difference_percentage": diff_percentage,
                    "diff_image": str(diff_file)
                }
            else:
                return {
                    "identical": True,
                    "difference_percentage": 0
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def cleanup(self):
        """Clean up resources."""
        if self.browser:
            self.browser.close()


def demo_claude_assistant():
    """Demonstrate the Claude Development Assistant."""
    
    print("=" * 60)
    print("   Claude Development Assistant Demo")
    print("=" * 60)
    
    assistant = ClaudeDevAssistant()
    
    # Demo 1: Screen capture
    print("\n📸 Demo 1: Screen Capture")
    result = assistant.capture_screen(annotate="Claude can see this!")
    print(f"   {result}")
    
    # Demo 2: Code verification
    print("\n✅ Demo 2: Code Verification")
    result = assistant.verify_code_output("echo 'Hello from Claude!'", "Hello")
    print(f"   Command: {result['command']}")
    print(f"   Success: {result['success']}")
    print(f"   Output: {result['output'].strip()}")
    
    # Demo 3: Web app test (if localhost:3000 is running)
    print("\n🌐 Demo 3: Web App Testing")
    print("   (This would test your PWA/Tauri app if it was running)")
    
    test_sequence = [
        {"action": "screenshot", "name": "initial_state"},
        {"action": "verify", "text": "Welcome"},
        {"action": "wait", "seconds": 1}
    ]
    
    # Uncomment to test against a real app:
    # result = assistant.test_web_app("http://localhost:3000", test_sequence)
    # print(f"   Tests run: {len(result['tests'])}")
    # print(f"   Success: {result['success']}")
    
    print("\n" + "=" * 60)
    print("✨ Claude can now:")
    print("   • See your screen with capture_screen()")
    print("   • Test your web apps with test_web_app()")
    print("   • Verify code output with verify_code_output()")
    print("   • Compare screenshots for visual regression")
    print("=" * 60)
    
    assistant.cleanup()


if __name__ == "__main__":
    demo_claude_assistant()
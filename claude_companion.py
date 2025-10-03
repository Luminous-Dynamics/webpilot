#!/usr/bin/env python3
"""
Claude Development Companion
A real tool for real-time development collaboration between human and Claude.
This creates a feedback loop where Claude can see, test, and verify.
"""

import os
import sys
import time
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import threading
import signal

# Screen capture imports
try:
    from PIL import Image, ImageDraw, ImageFont
    import mss
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Install screen capture: pip install Pillow mss")

# Browser automation for web testing (now using Playwright!)
from src.webpilot.core import RealBrowserAutomation


class ClaudeCompanion:
    """
    Your AI pair programmer that can actually see and test your work.
    """
    
    def __init__(self, workspace: str = None):
        """Initialize the companion with a workspace."""
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create companion directories
        self.companion_dir = self.workspace / ".claude-companion"
        self.screens_dir = self.companion_dir / "screens"
        self.outputs_dir = self.companion_dir / "outputs"
        self.tests_dir = self.companion_dir / "tests"
        self.feedback_dir = self.companion_dir / "feedback"
        
        for dir in [self.screens_dir, self.outputs_dir, self.tests_dir, self.feedback_dir]:
            dir.mkdir(parents=True, exist_ok=True)
        
        # Active processes
        self.dev_servers = {}  # pid -> process info
        self.browser = None
        
        # Session state
        self.session = {
            'id': self.session_id,
            'started': datetime.now().isoformat(),
            'workspace': str(self.workspace),
            'screens': [],
            'commands': [],
            'tests': [],
            'feedback': []
        }
        
        print(f"🤖 Claude Companion initialized")
        print(f"📁 Workspace: {self.workspace}")
        print(f"🆔 Session: {self.session_id}")
    
    # ============================================
    # 1. SCREEN CAPTURE - So Claude can see
    # ============================================
    
    def capture(self, annotation: str = None, highlight: Dict = None) -> Dict:
        """
        Capture screen with optional annotation and highlighting.
        
        Args:
            annotation: Text to overlay on the screenshot
            highlight: {'x': 100, 'y': 200, 'width': 300, 'height': 150}
        
        Returns:
            {'file': 'path/to/screenshot.png', 'timestamp': '...', 'annotation': '...'}
        """
        if not PIL_AVAILABLE:
            return {'error': 'Screen capture not available. Install: pip install Pillow mss'}
        
        timestamp = datetime.now().strftime("%H%M%S")
        filename = self.screens_dir / f"screen_{timestamp}.png"
        
        try:
            with mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                
                # Add annotations if requested
                if annotation or highlight:
                    draw = ImageDraw.Draw(img)
                    
                    # Add text annotation
                    if annotation:
                        # Black background for text
                        draw.rectangle([(10, 10), (600, 50)], fill='black')
                        draw.text((20, 20), f"Claude sees: {annotation}", fill='yellow')
                    
                    # Add highlight box
                    if highlight:
                        x, y = highlight.get('x', 0), highlight.get('y', 0)
                        w, h = highlight.get('width', 100), highlight.get('height', 100)
                        draw.rectangle([(x, y), (x+w, y+h)], outline='red', width=3)
                
                # Save screenshot
                img.save(filename)
                
                # Also save as "latest" for easy access
                latest = self.screens_dir / "latest.png"
                img.save(latest)
                
                result = {
                    'file': str(filename),
                    'timestamp': datetime.now().isoformat(),
                    'annotation': annotation,
                    'size': f"{img.width}x{img.height}"
                }
                
                self.session['screens'].append(result)
                print(f"📸 Screen captured: {filename.name}")
                return result
                
        except Exception as e:
            error = {'error': str(e)}
            print(f"❌ Capture failed: {e}")
            return error
    
    def show_me(self, what: str) -> Dict:
        """Quick capture with description of what to look at."""
        return self.capture(annotation=what)
    
    # ============================================
    # 2. COMMAND EXECUTION - Test Claude's suggestions
    # ============================================
    
    def run(self, command: str, timeout: int = 30, expect: str = None) -> Dict:
        """
        Run a command and capture output.
        
        Args:
            command: Shell command to execute
            timeout: Max execution time in seconds
            expect: Optional string to look for in output
        
        Returns:
            {'command': '...', 'success': bool, 'output': '...', 'error': '...'}
        """
        result = {
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'output': '',
            'error': '',
            'exit_code': None,
            'duration': 0
        }
        
        # Save output to file
        output_file = self.outputs_dir / f"output_{len(self.session['commands'])}.txt"
        
        print(f"🏃 Running: {command}")
        start_time = time.time()
        
        try:
            # Execute command
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            result['output'] = process.stdout
            result['error'] = process.stderr
            result['exit_code'] = process.returncode
            result['success'] = (process.returncode == 0)
            
            # Check for expected output
            if expect and expect in result['output']:
                result['found_expected'] = True
                print(f"✅ Found expected: '{expect}'")
            elif expect:
                result['found_expected'] = False
                print(f"❌ Didn't find: '{expect}'")
            
            # Save output
            with open(output_file, 'w') as f:
                f.write(f"Command: {command}\n")
                f.write(f"Exit Code: {process.returncode}\n")
                f.write(f"Duration: {time.time() - start_time:.2f}s\n")
                f.write("\n--- STDOUT ---\n")
                f.write(process.stdout)
                f.write("\n--- STDERR ---\n")
                f.write(process.stderr)
            
            # Display summary
            if result['success']:
                print(f"✅ Success (exit code: {process.returncode})")
            else:
                print(f"❌ Failed (exit code: {process.returncode})")
            
            if result['output']:
                print(f"📝 Output: {result['output'][:200]}...")
            
        except subprocess.TimeoutExpired:
            result['error'] = f"Command timed out after {timeout} seconds"
            print(f"⏱️ Timeout after {timeout}s")
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")
        
        result['duration'] = time.time() - start_time
        self.session['commands'].append(result)
        
        return result
    
    def verify(self, command: str, should_contain: str = None, should_succeed: bool = True) -> bool:
        """
        Verify a command works as expected.
        
        Args:
            command: Command to run
            should_contain: Expected text in output
            should_succeed: Whether command should succeed (exit 0)
        
        Returns:
            True if all expectations met
        """
        result = self.run(command)
        
        checks = []
        
        # Check exit code
        if should_succeed:
            checks.append(('Exit code', result['success']))
        
        # Check output content
        if should_contain:
            found = should_contain in result.get('output', '')
            checks.append((f'Contains "{should_contain}"', found))
        
        # Report results
        all_passed = all(check[1] for check in checks)
        
        print("\n📋 Verification Results:")
        for check_name, passed in checks:
            symbol = "✅" if passed else "❌"
            print(f"  {symbol} {check_name}")
        
        return all_passed
    
    # ============================================
    # 3. DEV SERVER MANAGEMENT - Lifecycle control
    # ============================================
    
    def start_server(self, command: str, name: str = "dev", wait_for: str = None, port: int = None) -> Dict:
        """
        Start a development server in the background.
        
        Args:
            command: Command to start server (e.g., 'npm run dev')
            name: Friendly name for this server
            wait_for: Text to wait for in output (e.g., 'Server running')
            port: Port to check if server is up
        
        Returns:
            {'name': '...', 'pid': 123, 'running': bool}
        """
        if name in self.dev_servers:
            print(f"⚠️  Server '{name}' already running (PID: {self.dev_servers[name]['pid']})")
            return self.dev_servers[name]
        
        print(f"🚀 Starting {name} server: {command}")
        
        try:
            # Start server process
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=self.workspace,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Create new process group
            )
            
            server_info = {
                'name': name,
                'command': command,
                'pid': process.pid,
                'process': process,
                'port': port,
                'started': datetime.now().isoformat(),
                'running': False
            }
            
            # Wait for server to start
            if wait_for:
                print(f"⏳ Waiting for: '{wait_for}'")
                start_time = time.time()
                while time.time() - start_time < 30:  # 30 second timeout
                    line = process.stdout.readline()
                    if wait_for in line:
                        print(f"✅ Server ready: found '{wait_for}'")
                        server_info['running'] = True
                        break
                    if process.poll() is not None:
                        print(f"❌ Server exited early")
                        break
                    time.sleep(0.1)
            else:
                # Just wait a bit for server to start
                time.sleep(3)
                server_info['running'] = process.poll() is None
            
            # Check if port is open
            if port and server_info['running']:
                time.sleep(2)  # Give it a moment
                port_check = self.run(f"curl -s http://localhost:{port} > /dev/null && echo 'UP' || echo 'DOWN'")
                if 'UP' in port_check.get('output', ''):
                    print(f"✅ Server responding on port {port}")
                else:
                    print(f"⚠️  Port {port} not responding yet")
            
            self.dev_servers[name] = server_info
            
            if server_info['running']:
                print(f"✅ {name} server started (PID: {process.pid})")
            else:
                print(f"❌ {name} server failed to start")
            
            return server_info
            
        except Exception as e:
            error_info = {'name': name, 'error': str(e), 'running': False}
            print(f"❌ Failed to start server: {e}")
            return error_info
    
    def stop_server(self, name: str = None) -> bool:
        """Stop a dev server by name or stop all."""
        if name:
            if name not in self.dev_servers:
                print(f"⚠️  No server named '{name}'")
                return False
            
            servers_to_stop = [name]
        else:
            servers_to_stop = list(self.dev_servers.keys())
        
        for server_name in servers_to_stop:
            server = self.dev_servers[server_name]
            try:
                # Kill the process group
                os.killpg(os.getpgid(server['pid']), signal.SIGTERM)
                time.sleep(1)
                
                # Force kill if still running
                if server['process'].poll() is None:
                    os.killpg(os.getpgid(server['pid']), signal.SIGKILL)
                
                print(f"✅ Stopped {server_name} server (PID: {server['pid']})")
                del self.dev_servers[server_name]
                
            except Exception as e:
                print(f"❌ Error stopping {server_name}: {e}")
                return False
        
        return True
    
    def restart_server(self, name: str) -> Dict:
        """Restart a dev server."""
        if name not in self.dev_servers:
            print(f"⚠️  No server named '{name}' to restart")
            return {}
        
        server_info = self.dev_servers[name]
        print(f"🔄 Restarting {name} server...")
        
        self.stop_server(name)
        time.sleep(2)
        
        return self.start_server(
            command=server_info['command'],
            name=name,
            port=server_info.get('port')
        )
    
    # ============================================
    # 4. WEB TESTING - Test web apps
    # ============================================
    
    def test_web(self, url: str, tests: List[Dict]) -> Dict:
        """
        Test a web application.
        
        Args:
            url: URL to test (e.g., 'http://localhost:3000')
            tests: List of test actions
        
        Returns:
            Test results with screenshots
        """
        if not self.browser:
            self.browser = RealBrowserAutomation(headless=False)
            self.browser.start()
        
        print(f"🌐 Testing web app: {url}")
        
        test_results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'screenshots': []
        }
        
        # Navigate to app
        self.browser.navigate(url)
        time.sleep(2)
        
        # Take initial screenshot
        initial_screen = self.browser.screenshot("initial_state")
        test_results['screenshots'].append(initial_screen)
        
        # Run each test
        for i, test in enumerate(tests):
            test_result = {
                'index': i,
                'test': test,
                'success': False,
                'message': ''
            }
            
            try:
                action = test.get('action')
                
                if action == 'click':
                    success = self.browser.click(test['element'])
                    test_result['success'] = success
                    test_result['message'] = f"Clicked: {test['element']}"
                
                elif action == 'type':
                    success = self.browser.type_text(test['text'], test.get('element'))
                    test_result['success'] = success
                    test_result['message'] = f"Typed: {test['text']}"
                
                elif action == 'verify':
                    text = self.browser.get_text()
                    found = test['text'] in text
                    test_result['success'] = found
                    test_result['message'] = f"Text {'found' if found else 'not found'}: {test['text']}"
                
                elif action == 'screenshot':
                    screen = self.browser.screenshot(test.get('name', f'test_{i}'))
                    test_results['screenshots'].append(screen)
                    test_result['success'] = True
                    test_result['message'] = f"Screenshot: {screen}"
                
                elif action == 'wait':
                    time.sleep(test.get('seconds', 1))
                    test_result['success'] = True
                    test_result['message'] = f"Waited {test.get('seconds', 1)}s"
                
            except Exception as e:
                test_result['message'] = f"Error: {str(e)}"
            
            test_results['tests'].append(test_result)
            
            # Stop on failure if requested
            if not test_result['success'] and test.get('critical', False):
                print(f"❌ Critical test failed, stopping")
                break
        
        # Save test results
        results_file = self.tests_dir / f"web_test_{datetime.now().strftime('%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        self.session['tests'].append(test_results)
        
        # Print summary
        passed = sum(1 for t in test_results['tests'] if t['success'])
        total = len(test_results['tests'])
        print(f"\n📊 Test Results: {passed}/{total} passed")
        
        return test_results
    
    # ============================================
    # 5. FEEDBACK LOOP - The magic connection
    # ============================================
    
    def feedback_loop(self, 
                      code_file: str = None,
                      test_command: str = None,
                      dev_server: Dict = None,
                      web_url: str = None) -> Dict:
        """
        Create a complete feedback loop for development.
        
        This is the magic: Claude can see your code, run it, test it, and iterate.
        
        Args:
            code_file: Path to code file being worked on
            test_command: Command to test the code
            dev_server: Server config {'command': 'npm run dev', 'port': 3000}
            web_url: URL to test if it's a web app
        
        Returns:
            Complete feedback with all artifacts
        """
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'code_file': code_file,
            'artifacts': {}
        }
        
        print("\n" + "="*60)
        print("🔄 FEEDBACK LOOP INITIATED")
        print("="*60)
        
        # Step 1: Capture current state
        print("\n📸 Step 1: Capturing current state...")
        screen = self.capture(annotation=f"Working on: {code_file or 'project'}")
        feedback['artifacts']['initial_screen'] = screen
        
        # Step 2: Show the code if specified
        if code_file and Path(code_file).exists():
            print(f"\n📄 Step 2: Reading {code_file}...")
            with open(code_file, 'r') as f:
                code_content = f.read()
            feedback['artifacts']['code'] = {
                'file': code_file,
                'content': code_content[:1000] + '...' if len(code_content) > 1000 else code_content
            }
            print(f"   Code: {len(code_content)} characters")
        
        # Step 3: Start dev server if needed
        if dev_server:
            print(f"\n🚀 Step 3: Starting dev server...")
            server = self.start_server(
                command=dev_server['command'],
                name='feedback-server',
                port=dev_server.get('port')
            )
            feedback['artifacts']['server'] = server
            time.sleep(3)  # Let server warm up
        
        # Step 4: Run tests if specified
        if test_command:
            print(f"\n🧪 Step 4: Running tests...")
            test_result = self.run(test_command)
            feedback['artifacts']['test_output'] = test_result
        
        # Step 5: Test web UI if applicable
        if web_url:
            print(f"\n🌐 Step 5: Testing web interface...")
            web_tests = [
                {'action': 'screenshot', 'name': 'homepage'},
                {'action': 'verify', 'text': 'body'}  # Basic check
            ]
            web_result = self.test_web(web_url, web_tests)
            feedback['artifacts']['web_test'] = web_result
        
        # Step 6: Capture final state
        print("\n📸 Step 6: Capturing final state...")
        final_screen = self.capture(annotation="After changes")
        feedback['artifacts']['final_screen'] = final_screen
        
        # Step 7: Generate summary
        print("\n📊 Step 7: Generating summary...")
        summary = self._generate_summary(feedback)
        feedback['summary'] = summary
        
        # Save feedback
        feedback_file = self.feedback_dir / f"feedback_{datetime.now().strftime('%H%M%S')}.json"
        with open(feedback_file, 'w') as f:
            json.dump(feedback, f, indent=2)
        
        self.session['feedback'].append(feedback)
        
        print("\n" + "="*60)
        print("✅ FEEDBACK LOOP COMPLETE")
        print(summary)
        print("="*60)
        
        return feedback
    
    def _generate_summary(self, feedback: Dict) -> str:
        """Generate a human-readable summary of the feedback."""
        lines = []
        
        # Check what we have
        if 'initial_screen' in feedback['artifacts']:
            lines.append(f"📸 Captured screen: {feedback['artifacts']['initial_screen'].get('file', 'Unknown')}")
        
        if 'server' in feedback['artifacts']:
            server = feedback['artifacts']['server']
            if server.get('running'):
                lines.append(f"✅ Server running: PID {server.get('pid')}")
            else:
                lines.append("❌ Server failed to start")
        
        if 'test_output' in feedback['artifacts']:
            test = feedback['artifacts']['test_output']
            if test.get('success'):
                lines.append(f"✅ Tests passed: {test.get('command')}")
            else:
                lines.append(f"❌ Tests failed: exit code {test.get('exit_code')}")
        
        if 'web_test' in feedback['artifacts']:
            web = feedback['artifacts']['web_test']
            tests = web.get('tests', [])
            passed = sum(1 for t in tests if t.get('success'))
            lines.append(f"🌐 Web tests: {passed}/{len(tests)} passed")
        
        return '\n'.join(lines)
    
    # ============================================
    # SESSION MANAGEMENT
    # ============================================
    
    def save_session(self) -> str:
        """Save the current session state."""
        session_file = self.companion_dir / f"session_{self.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(self.session, f, indent=2)
        print(f"💾 Session saved: {session_file}")
        return str(session_file)
    
    def cleanup(self):
        """Clean up resources."""
        print("\n🧹 Cleaning up...")
        
        # Stop all dev servers
        if self.dev_servers:
            print("   Stopping dev servers...")
            self.stop_server()  # Stops all
        
        # Close browser
        if self.browser:
            print("   Closing browser...")
            self.browser.close()
        
        # Save session
        self.save_session()
        
        print("✅ Cleanup complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


# ============================================
# QUICK HELPERS
# ============================================

def quick_feedback(workspace: str = ".") -> ClaudeCompanion:
    """Quick way to start a feedback session."""
    return ClaudeCompanion(workspace)


def demo():
    """Demonstrate the Claude Development Companion."""
    print("="*60)
    print("   🤖 Claude Development Companion Demo")
    print("="*60)
    
    with ClaudeCompanion() as companion:
        
        # Demo 1: Screen capture
        print("\n📸 Demo 1: Screen Capture")
        companion.show_me("Current development environment")
        
        # Demo 2: Command execution
        print("\n🏃 Demo 2: Command Execution")
        companion.verify("echo 'Hello Claude!'", should_contain="Hello Claude")
        
        # Demo 3: Dev server (simulated)
        print("\n🚀 Demo 3: Dev Server Management")
        print("   (Would start your actual dev server here)")
        # companion.start_server("npm run dev", "frontend", port=3000)
        
        # Demo 4: Feedback loop
        print("\n🔄 Demo 4: Feedback Loop")
        feedback = companion.feedback_loop(
            code_file=__file__,  # This file itself
            test_command="python --version"
        )
        
        print("\n" + "="*60)
        print("✨ Demo complete! Claude can now:")
        print("   • See your screen")
        print("   • Run your commands")
        print("   • Test your apps")
        print("   • Provide feedback")
        print("="*60)


if __name__ == "__main__":
    demo()
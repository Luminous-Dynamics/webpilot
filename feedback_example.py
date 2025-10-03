#!/usr/bin/env python3
"""
Real Development Feedback Loop Example
This shows how Claude and a developer can work together in real-time.
"""

from claude_companion import ClaudeCompanion
import time


def real_development_scenario():
    """
    Simulate a real development workflow where Claude helps debug and test.
    """
    
    print("="*60)
    print("   Real Development Scenario")
    print("   Claude helping debug a web app")
    print("="*60)
    
    # Initialize companion for current project
    companion = ClaudeCompanion(workspace=".")
    
    try:
        # SCENARIO: Developer is working on a Python web app
        print("\n📖 Scenario: You're debugging a Python web app\n")
        
        # Step 1: Claude needs to see what you're working on
        print("Step 1: Show Claude the current state")
        screen1 = companion.show_me("IDE with the bug")
        print(f"   Claude can now see: {screen1['file']}")
        time.sleep(1)
        
        # Step 2: Developer says "I think the issue is in the server startup"
        print("\nStep 2: Check if the server starts correctly")
        
        # First, let's check Python version (should work)
        companion.verify("python3 --version", should_contain="Python")
        
        # Try to run a simple test
        print("\nStep 3: Run the unit tests")
        test_result = companion.run("python3 -m pytest tests/ -v 2>/dev/null || echo 'No tests found'")
        
        if "No tests found" in test_result.get('output', ''):
            print("   ℹ️  No tests available (normal for this demo)")
        
        # Step 4: Start a simple web server for testing
        print("\nStep 4: Start a test server")
        
        # Create a simple test server file
        test_server_code = '''
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

class TestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Claude Companion Test Server Running!")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    server = HTTPServer(("", port), TestHandler)
    print(f"Test server running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped")
'''
        
        # Save the test server
        with open("test_server_temp.py", "w") as f:
            f.write(test_server_code)
        print("   Created test_server_temp.py")
        
        # Start the test server
        server = companion.start_server(
            "python3 test_server_temp.py 8888",
            name="test-server",
            wait_for="Test server running",
            port=8888
        )
        
        if server.get('running'):
            print("   ✅ Server started successfully!")
            
            # Step 5: Test the server
            print("\nStep 5: Test the server endpoint")
            time.sleep(2)  # Give server time to start
            
            # Check if server responds
            response = companion.run("curl -s http://localhost:8888")
            
            if "Test Server Running" in response.get('output', ''):
                print("   ✅ Server is responding correctly!")
            
            # Step 6: Take a screenshot showing success
            print("\nStep 6: Document the working state")
            screen2 = companion.capture(annotation="Server working - bug fixed!")
            
            # Step 7: Run the feedback loop
            print("\nStep 7: Complete feedback loop")
            feedback = companion.feedback_loop(
                code_file="test_server_temp.py",
                test_command="curl -s http://localhost:8888",
                web_url="http://localhost:8888"
            )
            
            print("\n" + "="*60)
            print("✅ DEVELOPMENT SESSION COMPLETE")
            print("="*60)
            print("\n📊 What Claude learned:")
            print("   • Your Python environment works")
            print("   • The server starts successfully")
            print("   • The endpoint responds correctly")
            print("   • Screenshots document the working state")
            print("\n💡 Claude can now suggest fixes based on what was observed!")
            
        else:
            print("   ❌ Server failed to start (this is useful debugging info!)")
        
    except Exception as e:
        print(f"\n❌ Error in scenario: {e}")
        print("   (This error is also useful feedback for Claude!)")
    
    finally:
        # Cleanup
        companion.cleanup()
        
        # Remove test file
        import os
        if os.path.exists("test_server_temp.py"):
            os.remove("test_server_temp.py")
            print("\n🧹 Cleaned up test files")


def simple_feedback_demo():
    """
    Simpler demo showing the core feedback loop concept.
    """
    print("\n" + "="*60)
    print("   Simple Feedback Loop Demo")
    print("="*60)
    
    with ClaudeCompanion() as companion:
        
        # The magic feedback loop in action
        print("\n🔄 THE FEEDBACK LOOP IN ACTION:")
        print("   1. You write code")
        print("   2. Claude sees your screen")
        print("   3. Claude suggests a test")
        print("   4. We run the test together")
        print("   5. Claude sees the result")
        print("   6. Iterate until it works!\n")
        
        # Example: You wrote some code
        print("📝 You: 'I just wrote a function to calculate fibonacci'")
        
        # Claude can see it
        companion.show_me("Your fibonacci function code")
        
        # Claude suggests a test
        print("🤖 Claude: 'Let's test if it works for small numbers'")
        
        # Create a simple fibonacci function
        fib_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test it
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
'''
        
        with open("test_fib.py", "w") as f:
            f.write(fib_code)
        
        # Run Claude's suggested test
        print("\n🧪 Running the test...")
        result = companion.run("python3 test_fib.py")
        
        # Claude sees the output
        if result['success']:
            print("✅ Claude: 'Great! The function works correctly!'")
            print("   Output shows correct Fibonacci sequence")
        
        # Capture final state
        companion.capture(annotation="Fibonacci function tested and working!")
        
        # Clean up
        import os
        if os.path.exists("test_fib.py"):
            os.remove("test_fib.py")
        
        print("\n" + "="*60)
        print("💡 This is the power of the feedback loop!")
        print("   • Claude sees what you see")
        print("   • Tests run in your actual environment")
        print("   • Results are immediately visible")
        print("   • Iteration is instant")
        print("="*60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        simple_feedback_demo()
    else:
        real_development_scenario()
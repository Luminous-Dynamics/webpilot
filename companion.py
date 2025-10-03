#!/usr/bin/env python3
"""
Claude Companion - Interactive Mode
Simple interactive tool for real-time development with Claude.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from claude_companion import ClaudeCompanion


def interactive_menu():
    """Interactive menu for the Claude Companion."""
    
    print("\n" + "="*60)
    print("   🤖 Claude Development Companion")
    print("   Real-time feedback loop for development")
    print("="*60)
    
    # Initialize companion
    workspace = input("\n📁 Workspace path (Enter for current dir): ").strip() or "."
    companion = ClaudeCompanion(workspace)
    
    try:
        while True:
            print("\n" + "-"*40)
            print("What would you like me to help with?")
            print("-"*40)
            print("1. 📸 Show me your screen")
            print("2. 🏃 Run a command") 
            print("3. 🧪 Verify code works")
            print("4. 🚀 Start dev server")
            print("5. 🔄 Stop dev server")
            print("6. 🌐 Test web app")
            print("7. 🔁 Full feedback loop")
            print("8. 💾 Save session")
            print("9. 🚪 Exit")
            print("-"*40)
            
            choice = input("\nChoice (1-9): ").strip()
            
            if choice == "1":
                # Screen capture
                what = input("What should I look at? ").strip() or "Current state"
                result = companion.show_me(what)
                print(f"✅ Screenshot saved: {result.get('file', 'Error')}")
                
            elif choice == "2":
                # Run command
                command = input("Command to run: ").strip()
                if command:
                    timeout = int(input("Timeout (seconds, default 30): ").strip() or "30")
                    result = companion.run(command, timeout=timeout)
                    
                    # Show output preview
                    output = result.get('output', '')
                    if output:
                        lines = output.split('\n')
                        print(f"\n📝 Output ({len(lines)} lines):")
                        for line in lines[:10]:  # First 10 lines
                            print(f"   {line}")
                        if len(lines) > 10:
                            print(f"   ... and {len(lines)-10} more lines")
                
            elif choice == "3":
                # Verify command
                command = input("Command to verify: ").strip()
                if command:
                    expect = input("Should contain (optional): ").strip() or None
                    success = companion.verify(command, should_contain=expect)
                    if success:
                        print("✅ Verification passed!")
                    else:
                        print("❌ Verification failed")
                
            elif choice == "4":
                # Start dev server
                command = input("Server command (e.g., npm run dev): ").strip()
                if command:
                    name = input("Server name (default: dev): ").strip() or "dev"
                    port = input("Port number (optional): ").strip()
                    port = int(port) if port else None
                    
                    result = companion.start_server(command, name=name, port=port)
                    if result.get('running'):
                        print(f"✅ Server '{name}' started (PID: {result['pid']})")
                    else:
                        print(f"❌ Failed to start server")
                
            elif choice == "5":
                # Stop dev server
                if companion.dev_servers:
                    print("\nRunning servers:")
                    for name, info in companion.dev_servers.items():
                        print(f"  • {name} (PID: {info['pid']})")
                    
                    name = input("Server name to stop (Enter for all): ").strip() or None
                    if companion.stop_server(name):
                        print("✅ Server stopped")
                else:
                    print("No servers running")
                
            elif choice == "6":
                # Test web app
                url = input("URL to test (e.g., http://localhost:3000): ").strip()
                if url:
                    print("\nQuick test or custom?")
                    print("1. Quick test (screenshot + basic check)")
                    print("2. Custom test sequence")
                    
                    test_type = input("Choice (1-2): ").strip()
                    
                    if test_type == "1":
                        tests = [
                            {'action': 'screenshot', 'name': 'initial'},
                            {'action': 'verify', 'text': 'body'}
                        ]
                    else:
                        tests = []
                        print("\nEnter test steps (empty to finish):")
                        while True:
                            action = input("Action (click/type/verify/screenshot/wait): ").strip()
                            if not action:
                                break
                            
                            test = {'action': action}
                            
                            if action == 'click':
                                test['element'] = input("Element to click: ").strip()
                            elif action == 'type':
                                test['text'] = input("Text to type: ").strip()
                                test['element'] = input("Element (optional): ").strip() or None
                            elif action == 'verify':
                                test['text'] = input("Text to find: ").strip()
                            elif action == 'screenshot':
                                test['name'] = input("Screenshot name: ").strip()
                            elif action == 'wait':
                                test['seconds'] = int(input("Seconds: ").strip() or "1")
                            
                            tests.append(test)
                    
                    if tests:
                        result = companion.test_web(url, tests)
                        passed = sum(1 for t in result['tests'] if t['success'])
                        total = len(result['tests'])
                        print(f"\n✅ Tests: {passed}/{total} passed")
                
            elif choice == "7":
                # Full feedback loop
                print("\n🔄 Setting up feedback loop...")
                
                code_file = input("Code file (optional): ").strip() or None
                test_command = input("Test command (optional): ").strip() or None
                
                # Dev server setup
                start_server = input("Start a dev server? (y/n): ").strip().lower() == 'y'
                dev_server = None
                if start_server:
                    dev_server = {
                        'command': input("Server command: ").strip(),
                        'port': int(input("Port (optional): ").strip() or "0") or None
                    }
                
                web_url = input("Web URL to test (optional): ").strip() or None
                
                print("\n🔄 Running feedback loop...")
                feedback = companion.feedback_loop(
                    code_file=code_file,
                    test_command=test_command,
                    dev_server=dev_server,
                    web_url=web_url
                )
                
                print("\n✅ Feedback loop complete!")
                print(f"   Artifacts collected: {len(feedback.get('artifacts', {}))}")
                
            elif choice == "8":
                # Save session
                session_file = companion.save_session()
                print(f"✅ Session saved: {session_file}")
                
            elif choice == "9":
                # Exit
                print("\n👋 Goodbye! Cleaning up...")
                break
            
            else:
                print("❌ Invalid choice")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        companion.cleanup()
        print("\n✅ Claude Companion session ended")


def quick_test():
    """Quick test to verify everything works."""
    print("🧪 Running quick test...")
    
    with ClaudeCompanion() as companion:
        # Test screen capture
        screen = companion.capture(annotation="Quick test")
        if 'file' in screen:
            print(f"✅ Screen capture works: {screen['file']}")
        
        # Test command execution
        result = companion.run("echo 'Claude Companion Test'")
        if result['success']:
            print(f"✅ Command execution works")
        
        # Test verification
        if companion.verify("echo 'test'", should_contain="test"):
            print(f"✅ Verification works")
        
        print("\n✅ All systems operational!")
        print("📁 Session data in: .claude-companion/")
        
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Development Companion')
    parser.add_argument('--test', action='store_true', help='Run quick test')
    parser.add_argument('--workspace', type=str, default='.', help='Workspace directory')
    parser.add_argument('--feedback', action='store_true', help='Run immediate feedback loop')
    
    args = parser.parse_args()
    
    if args.test:
        quick_test()
    elif args.feedback:
        # Quick feedback mode
        with ClaudeCompanion(args.workspace) as companion:
            feedback = companion.feedback_loop(
                test_command="ls -la"  # Simple test
            )
            print(f"\n✅ Feedback collected in: .claude-companion/feedback/")
    else:
        # Interactive mode
        interactive_menu()


if __name__ == "__main__":
    main()
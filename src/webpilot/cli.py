#!/usr/bin/env python3
"""
WebPilot CLI - Command-line interface for web automation
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from webpilot import WebPilot, WebPilotSession, BrowserType, ActionResult


class WebPilotCLI:
    """Command-line interface for WebPilot"""
    
    def __init__(self):
        self.pilot = None
        self.session = None
        
    def parse_args(self) -> argparse.Namespace:
        """Parse command-line arguments"""
        parser = argparse.ArgumentParser(
            description="WebPilot - Professional Web Automation Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  webpilot browse https://github.com
  webpilot screenshot --url https://example.com --output example.png
  webpilot interact --session my-session
  webpilot batch --urls-file sites.txt --action screenshot
  webpilot report --session-id 20250112_123456_abc123
            """
        )
        
        parser.add_argument('--version', action='version', version='WebPilot 1.0.0')
        parser.add_argument('--browser', 
                          choices=['firefox', 'chrome', 'chromium'],
                          default='firefox',
                          help='Browser to use')
        parser.add_argument('--headless', 
                          action='store_true',
                          help='Run browser in headless mode')
        parser.add_argument('--session', 
                          help='Session ID to use or resume')
        parser.add_argument('--verbose', '-v',
                          action='store_true',
                          help='Verbose output')
        
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # Browse command
        browse_parser = subparsers.add_parser('browse', help='Open browser and navigate')
        browse_parser.add_argument('url', help='URL to navigate to')
        browse_parser.add_argument('--screenshot', action='store_true',
                                  help='Take screenshot after loading')
        
        # Screenshot command
        screenshot_parser = subparsers.add_parser('screenshot', help='Take screenshot')
        screenshot_parser.add_argument('--url', help='URL to screenshot')
        screenshot_parser.add_argument('--output', '-o', help='Output filename')
        
        # Click command
        click_parser = subparsers.add_parser('click', help='Click on element')
        click_parser.add_argument('--x', type=int, help='X coordinate')
        click_parser.add_argument('--y', type=int, help='Y coordinate')
        click_parser.add_argument('--text', help='Text to click on')
        
        # Type command
        type_parser = subparsers.add_parser('type', help='Type text')
        type_parser.add_argument('text', help='Text to type')
        type_parser.add_argument('--clear', action='store_true',
                                help='Clear field first')
        
        # Scroll command
        scroll_parser = subparsers.add_parser('scroll', help='Scroll page')
        scroll_parser.add_argument('direction', 
                                  choices=['up', 'down', 'top', 'bottom'],
                                  help='Scroll direction')
        scroll_parser.add_argument('--amount', type=int, default=3,
                                  help='Scroll amount')
        
        # Navigate command
        nav_parser = subparsers.add_parser('navigate', help='Navigate to URL')
        nav_parser.add_argument('url', help='URL to navigate to')
        
        # Extract command
        extract_parser = subparsers.add_parser('extract', help='Extract page content')
        extract_parser.add_argument('--output', '-o', help='Output file')
        
        # Interactive mode
        interact_parser = subparsers.add_parser('interact', 
                                               help='Interactive mode')
        interact_parser.add_argument('--commands-file', 
                                    help='File with commands to execute')
        
        # Batch mode
        batch_parser = subparsers.add_parser('batch', help='Batch operations')
        batch_parser.add_argument('--urls-file', required=True,
                                 help='File with URLs (one per line)')
        batch_parser.add_argument('--action', required=True,
                                 choices=['screenshot', 'extract'],
                                 help='Action to perform on each URL')
        batch_parser.add_argument('--output-dir', default='./output',
                                 help='Output directory')
        
        # Report command
        report_parser = subparsers.add_parser('report', help='Get session report')
        report_parser.add_argument('--session-id', help='Session ID')
        report_parser.add_argument('--format', choices=['json', 'text'],
                                  default='text', help='Output format')
        
        # Close command
        close_parser = subparsers.add_parser('close', help='Close browser')
        
        return parser.parse_args()
        
    def setup_pilot(self, args: argparse.Namespace) -> WebPilot:
        """Setup WebPilot instance"""
        browser_type = BrowserType[args.browser.upper()]
        
        if args.session:
            session = WebPilotSession(args.session)
        else:
            session = WebPilotSession()
            
        self.session = session
        self.pilot = WebPilot(
            browser=browser_type,
            headless=args.headless,
            session=session
        )
        
        if args.verbose:
            print(f"Session ID: {session.session_id}")
            print(f"Session directory: {session.session_dir}")
            
        return self.pilot
        
    def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the specified command"""
        
        if not args.command:
            print("No command specified. Use --help for usage.")
            return 1
            
        # Commands that don't need pilot setup
        if args.command == 'report':
            return self.cmd_report(args)
            
        # Setup pilot for other commands
        pilot = self.setup_pilot(args)
        
        # Command dispatch
        commands = {
            'browse': self.cmd_browse,
            'screenshot': self.cmd_screenshot,
            'click': self.cmd_click,
            'type': self.cmd_type,
            'scroll': self.cmd_scroll,
            'navigate': self.cmd_navigate,
            'extract': self.cmd_extract,
            'interact': self.cmd_interact,
            'batch': self.cmd_batch,
            'close': self.cmd_close,
        }
        
        if args.command in commands:
            return commands[args.command](args, pilot)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    def cmd_browse(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Browse command"""
        result = pilot.start(args.url)
        self.print_result(result, args.verbose)
        
        if args.screenshot and result.success:
            screenshot_result = pilot.screenshot()
            self.print_result(screenshot_result, args.verbose)
            
        return 0 if result.success else 1
        
    def cmd_screenshot(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Screenshot command"""
        if args.url:
            nav_result = pilot.navigate(args.url)
            if not nav_result.success:
                self.print_result(nav_result, args.verbose)
                return 1
            pilot.wait(2)  # Wait for page load
            
        result = pilot.screenshot(args.output)
        self.print_result(result, args.verbose)
        
        if result.success:
            print(f"Screenshot saved: {result.data['path']}")
            
        return 0 if result.success else 1
        
    def cmd_click(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Click command"""
        result = pilot.click(x=args.x, y=args.y, text=args.text)
        self.print_result(result, args.verbose)
        return 0 if result.success else 1
        
    def cmd_type(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Type command"""
        result = pilot.type_text(args.text, clear_first=args.clear)
        self.print_result(result, args.verbose)
        return 0 if result.success else 1
        
    def cmd_scroll(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Scroll command"""
        result = pilot.scroll(args.direction, args.amount)
        self.print_result(result, args.verbose)
        return 0 if result.success else 1
        
    def cmd_navigate(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Navigate command"""
        result = pilot.navigate(args.url)
        self.print_result(result, args.verbose)
        return 0 if result.success else 1
        
    def cmd_extract(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Extract command"""
        result = pilot.extract_page_content()
        self.print_result(result, args.verbose)
        
        if result.success and args.output:
            with open(args.output, 'w') as f:
                f.write(result.data.get('content_preview', ''))
            print(f"Content saved to: {args.output}")
            
        return 0 if result.success else 1
        
    def cmd_interact(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Interactive mode"""
        print("WebPilot Interactive Mode")
        print("Type 'help' for commands, 'quit' to exit")
        print(f"Session: {pilot.session.session_id}")
        print()
        
        # Start browser if not already running
        if not pilot.session.state.get('browser_pid'):
            pilot.start("about:blank")
            
        commands_help = """
Available commands:
  navigate <url>     - Navigate to URL
  screenshot [name]  - Take screenshot
  click <x> <y>      - Click at coordinates
  type <text>        - Type text
  key <key>          - Press key (e.g., Return, Tab, ctrl+a)
  scroll <direction> - Scroll (up/down/top/bottom)
  extract            - Extract page content
  wait <seconds>     - Wait
  report             - Show session report
  help               - Show this help
  quit               - Exit
        """
        
        while True:
            try:
                command = input("> ").strip()
                
                if command == 'quit':
                    break
                elif command == 'help':
                    print(commands_help)
                elif command.startswith('navigate '):
                    url = command[9:]
                    result = pilot.navigate(url)
                    self.print_result(result, args.verbose)
                elif command == 'screenshot' or command.startswith('screenshot '):
                    name = command[11:] if len(command) > 11 else None
                    result = pilot.screenshot(name)
                    self.print_result(result, args.verbose)
                elif command.startswith('click '):
                    parts = command.split()
                    if len(parts) >= 3:
                        result = pilot.click(int(parts[1]), int(parts[2]))
                        self.print_result(result, args.verbose)
                elif command.startswith('type '):
                    text = command[5:]
                    result = pilot.type_text(text)
                    self.print_result(result, args.verbose)
                elif command.startswith('key '):
                    key = command[4:]
                    result = pilot.press_key(key)
                    self.print_result(result, args.verbose)
                elif command.startswith('scroll '):
                    direction = command[7:]
                    result = pilot.scroll(direction)
                    self.print_result(result, args.verbose)
                elif command == 'extract':
                    result = pilot.extract_page_content()
                    self.print_result(result, args.verbose)
                elif command.startswith('wait '):
                    seconds = float(command[5:])
                    result = pilot.wait(seconds)
                    self.print_result(result, args.verbose)
                elif command == 'report':
                    report = pilot.get_session_report()
                    print(json.dumps(report, indent=2))
                else:
                    print(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except Exception as e:
                print(f"Error: {e}")
                
        return 0
        
    def cmd_batch(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Batch operations"""
        urls_file = Path(args.urls_file)
        if not urls_file.exists():
            print(f"URLs file not found: {urls_file}")
            return 1
            
        urls = urls_file.read_text().strip().split('\n')
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        print(f"Processing {len(urls)} URLs...")
        
        success_count = 0
        for i, url in enumerate(urls, 1):
            if not url.strip():
                continue
                
            print(f"[{i}/{len(urls)}] {url}")
            
            # Navigate to URL
            nav_result = pilot.navigate(url)
            if not nav_result.success:
                print(f"  Failed to navigate: {nav_result.error}")
                continue
                
            pilot.wait(2)  # Wait for page load
            
            # Perform action
            if args.action == 'screenshot':
                filename = f"{url.replace('://', '_').replace('/', '_')}.png"
                result = pilot.screenshot(filename)
            elif args.action == 'extract':
                result = pilot.extract_page_content()
                if result.success:
                    filename = f"{url.replace('://', '_').replace('/', '_')}.txt"
                    output_file = output_dir / filename
                    output_file.write_text(result.data.get('content_preview', ''))
                    print(f"  Saved to: {output_file}")
                    
            if result.success:
                success_count += 1
                
        print(f"\nCompleted: {success_count}/{len(urls)} successful")
        return 0
        
    def cmd_close(self, args: argparse.Namespace, pilot: WebPilot) -> int:
        """Close browser"""
        result = pilot.close()
        self.print_result(result, args.verbose)
        return 0 if result.success else 1
        
    def cmd_report(self, args: argparse.Namespace) -> int:
        """Get session report"""
        if args.session_id:
            session = WebPilotSession(args.session_id)
        else:
            # Find latest session
            sessions_dir = Path("/tmp/webpilot-sessions")
            if not sessions_dir.exists():
                print("No sessions found")
                return 1
                
            sessions = sorted(sessions_dir.iterdir(), key=lambda p: p.stat().st_mtime)
            if not sessions:
                print("No sessions found")
                return 1
                
            session = WebPilotSession(sessions[-1].name)
            
        pilot = WebPilot(session=session)
        report = pilot.get_session_report()
        
        if args.format == 'json':
            print(json.dumps(report, indent=2))
        else:
            print(f"Session ID: {report['session_id']}")
            print(f"Created: {report['created_at']}")
            print(f"Current URL: {report['current_url']}")
            print(f"Total actions: {report['total_actions']}")
            print(f"Screenshots: {report['screenshots_taken']}")
            print(f"Session directory: {report['session_dir']}")
            print(f"Log file: {report['log_file']}")
            
        return 0
        
    def print_result(self, result: ActionResult, verbose: bool = False):
        """Print action result"""
        if result.success:
            print(f"✅ {result.action_type.value}: Success")
        else:
            print(f"❌ {result.action_type.value}: {result.error}")
            
        if verbose and result.data:
            print(f"  Data: {json.dumps(result.data, indent=2)}")
        if verbose:
            print(f"  Duration: {result.duration_ms:.1f}ms")
            
    def run(self) -> int:
        """Main entry point"""
        args = self.parse_args()
        return self.execute_command(args)


def main():
    """Main function"""
    cli = WebPilotCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
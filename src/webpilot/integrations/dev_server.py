#!/usr/bin/env python3
"""
Dev Server Integration - Auto-detect and connect to development servers
Supports: Vite, Next.js, Create React App, Vue CLI, Webpack Dev Server, Parcel, and more
"""

import socket
import time
import requests
import re
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import json


class DevServer:
    """Detect and interact with development servers"""
    
    # Common dev server ports and their frameworks
    COMMON_PORTS = {
        3000: ['Next.js', 'Create React App', 'Remix'],
        3001: ['Alternative React'],
        4200: ['Angular'],
        5173: ['Vite'],
        5174: ['Vite (alternative)'],
        8080: ['Webpack Dev Server', 'Vue CLI'],
        8081: ['Webpack (alternative)'],
        1234: ['Parcel'],
        24678: ['Parcel (alternative)'],
        9000: ['Gatsby'],
        4000: ['Ember'],
    }
    
    def __init__(self, host: str = 'localhost'):
        """Initialize dev server detector"""
        self.host = host
        self.detected_servers: List[Dict] = []
        
    def scan_ports(self, ports: Optional[List[int]] = None) -> List[Dict]:
        """
        Scan for running dev servers on common ports.
        
        Args:
            ports: List of ports to scan (None = scan all common ports)
            
        Returns:
            List of detected servers with details
        """
        if ports is None:
            ports = list(self.COMMON_PORTS.keys())
        
        detected = []
        
        for port in ports:
            if self._is_port_open(port):
                server_info = self._identify_server(port)
                if server_info:
                    detected.append(server_info)
                    print(f"✅ Found {server_info['framework']} on port {port}")
        
        self.detected_servers = detected
        return detected
    
    def _is_port_open(self, port: int, timeout: float = 0.5) -> bool:
        """Check if a port is open"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((self.host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _identify_server(self, port: int) -> Optional[Dict]:
        """Identify the framework running on a port"""
        url = f"http://{self.host}:{port}"
        
        try:
            response = requests.get(url, timeout=2)
            
            # Analyze response to identify framework
            framework = self._detect_framework(response, port)
            
            return {
                'port': port,
                'url': url,
                'framework': framework,
                'status': response.status_code,
                'ready': response.status_code == 200
            }
        except requests.exceptions.RequestException:
            # Port is open but not responding to HTTP
            return {
                'port': port,
                'url': url,
                'framework': self.COMMON_PORTS.get(port, ['Unknown'])[0],
                'status': None,
                'ready': False
            }
    
    def _detect_framework(self, response: requests.Response, port: int) -> str:
        """Detect framework from response"""
        content = response.text.lower()
        headers = {k.lower(): v for k, v in response.headers.items()}
        
        # Vite detection
        if 'vite' in content or 'vite' in headers.get('server', ''):
            return 'Vite'
        
        # Next.js detection
        if 'next.js' in content or '__next' in content:
            return 'Next.js'
        
        # Create React App detection
        if 'react' in content and 'webpack' in content:
            return 'Create React App'
        
        # Vue detection
        if 'vue' in content or port == 8080:
            return 'Vue CLI'
        
        # Angular detection
        if 'angular' in content or port == 4200:
            return 'Angular'
        
        # Parcel detection
        if 'parcel' in content or port == 1234:
            return 'Parcel'
        
        # Gatsby detection
        if 'gatsby' in content or port == 9000:
            return 'Gatsby'
        
        # Fallback to port-based detection
        return self.COMMON_PORTS.get(port, ['Unknown'])[0]
    
    def detect(self) -> Optional[Dict]:
        """
        Auto-detect the primary dev server.
        
        Returns:
            First detected server or None
        """
        servers = self.scan_ports()
        return servers[0] if servers else None
    
    def wait_for_ready(self, url: str, timeout: int = 30, interval: float = 0.5) -> bool:
        """
        Wait for dev server to be ready.
        
        Args:
            url: Server URL
            timeout: Max wait time in seconds
            interval: Check interval
            
        Returns:
            True if server became ready, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ Server ready at {url}")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(interval)
        
        print(f"❌ Server not ready after {timeout}s")
        return False
    
    def wait_for_hmr(self, page, timeout: int = 5) -> bool:
        """
        Wait for Hot Module Replacement (HMR) to complete.
        Uses Playwright page to detect HMR events.
        
        Args:
            page: Playwright page object
            timeout: Max wait time
            
        Returns:
            True when HMR complete
        """
        # Listen for HMR events (framework-specific)
        hmr_complete = False
        
        def handle_console(msg):
            nonlocal hmr_complete
            text = msg.text.lower()
            
            # Vite HMR
            if '[vite]' in text and 'updated' in text:
                hmr_complete = True
            
            # Webpack HMR
            if '[hmr]' in text or '[wds]' in text:
                hmr_complete = True
            
            # Next.js Fast Refresh
            if 'fast refresh' in text or 'compiled' in text:
                hmr_complete = True
        
        page.on('console', handle_console)
        
        # Wait for HMR event or timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            if hmr_complete:
                print("✅ HMR complete")
                return True
            time.sleep(0.1)
        
        print("⚠️  HMR timeout (continuing anyway)")
        return False
    
    def read_build_errors(self, page) -> List[Dict]:
        """
        Read build errors from dev server error overlay.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of error objects
        """
        errors = []
        
        try:
            # Vite error overlay
            vite_overlay = page.query_selector('vite-error-overlay')
            if vite_overlay:
                error_text = vite_overlay.inner_text()
                errors.append({
                    'framework': 'Vite',
                    'type': 'build_error',
                    'message': error_text
                })
            
            # Webpack/React error overlay
            react_overlay = page.query_selector('.react-error-overlay, #webpack-dev-server-client-overlay')
            if react_overlay:
                error_text = react_overlay.inner_text()
                errors.append({
                    'framework': 'Webpack/React',
                    'type': 'build_error',
                    'message': error_text
                })
            
            # Next.js error overlay
            nextjs_overlay = page.query_selector('nextjs-portal')
            if nextjs_overlay:
                error_text = nextjs_overlay.inner_text()
                errors.append({
                    'framework': 'Next.js',
                    'type': 'build_error',
                    'message': error_text
                })
        
        except Exception as e:
            print(f"⚠️  Error reading build errors: {e}")
        
        return errors
    
    def get_package_json(self, project_dir: str = '.') -> Optional[Dict]:
        """Read package.json to identify framework"""
        try:
            package_json_path = Path(project_dir) / 'package.json'
            if package_json_path.exists():
                with open(package_json_path) as f:
                    return json.load(f)
        except:
            pass
        return None
    
    def identify_framework_from_package(self, project_dir: str = '.') -> Optional[str]:
        """Identify framework from package.json dependencies"""
        pkg = self.get_package_json(project_dir)
        if not pkg:
            return None
        
        deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
        
        # Check for framework packages
        if 'next' in deps:
            return 'Next.js'
        elif 'vite' in deps:
            return 'Vite'
        elif 'react-scripts' in deps:
            return 'Create React App'
        elif '@vue/cli-service' in deps or 'vue' in deps:
            return 'Vue'
        elif '@angular/cli' in deps:
            return 'Angular'
        elif 'gatsby' in deps:
            return 'Gatsby'
        elif 'parcel' in deps or 'parcel-bundler' in deps:
            return 'Parcel'
        
        return None
    
    def get_dev_script(self, project_dir: str = '.') -> Optional[str]:
        """Get the dev script command from package.json"""
        pkg = self.get_package_json(project_dir)
        if pkg and 'scripts' in pkg:
            return pkg['scripts'].get('dev') or pkg['scripts'].get('start')
        return None


# Quick usage function
def detect_dev_server() -> Optional[Dict]:
    """Quick function to detect running dev server"""
    detector = DevServer()
    return detector.detect()


# Example usage
if __name__ == "__main__":
    print("🔍 Scanning for development servers...\n")
    
    detector = DevServer()
    
    # Scan for running servers
    servers = detector.scan_ports()
    
    if servers:
        print(f"\n✨ Found {len(servers)} development server(s):")
        for server in servers:
            print(f"\n  📦 {server['framework']}")
            print(f"     URL: {server['url']}")
            print(f"     Status: {'✅ Ready' if server['ready'] else '⚠️  Not ready'}")
    else:
        print("\n❌ No development servers found")
        print("\nℹ️  Make sure your dev server is running:")
        print("   npm run dev")
        print("   npm start")
        print("   yarn dev")
    
    # Try to identify framework from package.json
    print("\n🔍 Checking package.json...")
    framework = detector.identify_framework_from_package()
    if framework:
        print(f"✅ Detected {framework} in package.json")
        dev_script = detector.get_dev_script()
        if dev_script:
            print(f"   Dev command: {dev_script}")

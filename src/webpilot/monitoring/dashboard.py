#!/usr/bin/env python3
"""
WebPilot Monitoring Dashboard - Real-time test monitoring
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

logger = logging.getLogger('WebPilot.Monitor')


@dataclass
class TestMetric:
    """Individual test metric"""
    timestamp: datetime
    test_name: str
    status: str  # 'running', 'passed', 'failed', 'skipped'
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    screenshot: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class WebPilotMonitor:
    """Real-time monitoring dashboard for WebPilot tests"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.metrics: List[TestMetric] = []
        self.current_tests: Dict[str, TestMetric] = {}
        self.start_time = datetime.now()
        self.server_thread = None
        self.server = None
        self.logger = logging.getLogger('WebPilotMonitor')
        
    def add_test_start(self, test_name: str):
        """Record test start"""
        metric = TestMetric(
            timestamp=datetime.now(),
            test_name=test_name,
            status='running'
        )
        self.current_tests[test_name] = metric
        self.metrics.append(metric)
        self._update_dashboard()
        
    def add_test_result(self, test_name: str, status: str, 
                        duration_ms: float = None, error: str = None,
                        screenshot: str = None, metrics: Dict = None):
        """Record test completion"""
        if test_name in self.current_tests:
            metric = self.current_tests[test_name]
            metric.status = status
            metric.duration_ms = duration_ms
            metric.error = error
            metric.screenshot = screenshot
            metric.metrics = metrics
            del self.current_tests[test_name]
        else:
            metric = TestMetric(
                timestamp=datetime.now(),
                test_name=test_name,
                status=status,
                duration_ms=duration_ms,
                error=error,
                screenshot=screenshot,
                metrics=metrics
            )
            self.metrics.append(metric)
        
        self._update_dashboard()
        
    def get_statistics(self) -> Dict:
        """Get current test statistics"""
        total = len(self.metrics)
        passed = sum(1 for m in self.metrics if m.status == 'passed')
        failed = sum(1 for m in self.metrics if m.status == 'failed')
        running = len(self.current_tests)
        skipped = sum(1 for m in self.metrics if m.status == 'skipped')
        
        avg_duration = 0
        if completed := [m for m in self.metrics if m.duration_ms]:
            avg_duration = sum(m.duration_ms for m in completed) / len(completed)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'running': running,
            'skipped': skipped,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'avg_duration_ms': avg_duration,
            'runtime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
    def _update_dashboard(self):
        """Update dashboard HTML with latest data"""
        dashboard_html = self._generate_dashboard_html()
        dashboard_path = Path(f"/tmp/webpilot-monitor-{self.port}/index.html")
        dashboard_path.parent.mkdir(exist_ok=True)
        dashboard_path.write_text(dashboard_html)
        
        # Also save JSON data for API access
        json_path = dashboard_path.parent / 'data.json'
        json_data = {
            'statistics': self.get_statistics(),
            'metrics': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'test_name': m.test_name,
                    'status': m.status,
                    'duration_ms': m.duration_ms,
                    'error': m.error
                }
                for m in self.metrics[-100:]  # Last 100 tests
            ],
            'current_tests': [
                {
                    'test_name': name,
                    'status': 'running',
                    'started': m.timestamp.isoformat()
                }
                for name, m in self.current_tests.items()
            ]
        }
        json_path.write_text(json.dumps(json_data, indent=2))
        
    def _generate_dashboard_html(self) -> str:
        """Generate dashboard HTML"""
        stats = self.get_statistics()
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="5">
    <title>WebPilot Monitor Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 2rem;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }}
        
        .stat-value {{
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            font-size: 1rem;
            opacity: 0.9;
        }}
        
        .passed {{ color: #4ade80; }}
        .failed {{ color: #f87171; }}
        .running {{ color: #60a5fa; }}
        .skipped {{ color: #fbbf24; }}
        
        .tests-section {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        
        h2 {{
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }}
        
        .test-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        
        .test-item {{
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid;
        }}
        
        .test-item.passed {{ border-color: #4ade80; }}
        .test-item.failed {{ border-color: #f87171; }}
        .test-item.running {{ 
            border-color: #60a5fa; 
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        
        .test-name {{
            font-weight: 600;
            flex: 1;
        }}
        
        .test-duration {{
            margin-left: 1rem;
            opacity: 0.8;
        }}
        
        .test-status {{
            margin-left: 1rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
        }}
        
        .status-passed {{
            background: #4ade80;
            color: #14532d;
        }}
        
        .status-failed {{
            background: #f87171;
            color: #7f1d1d;
        }}
        
        .status-running {{
            background: #60a5fa;
            color: #1e3a8a;
        }}
        
        .progress-bar {{
            height: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 3rem;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4ade80 0%, #60a5fa 100%);
            width: {stats['pass_rate']:.1f}%;
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 3rem;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>🚁 WebPilot Monitor Dashboard</h1>
        
        <div class="progress-bar">
            <div class="progress-fill">
                {stats['pass_rate']:.1f}% Pass Rate
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total']}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-value passed">{stats['passed']}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value failed">{stats['failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value running">{stats['running']}</div>
                <div class="stat-label">Running</div>
            </div>
            <div class="stat-card">
                <div class="stat-value skipped">{stats['skipped']}</div>
                <div class="stat-label">Skipped</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['avg_duration_ms']:.0f}ms</div>
                <div class="stat-label">Avg Duration</div>
            </div>
        </div>
        
        {self._generate_current_tests_html()}
        {self._generate_recent_tests_html()}
        
        <div class="footer">
            <p>Runtime: {stats['runtime_seconds']:.0f} seconds | Auto-refresh: 5s</p>
            <p>WebPilot Monitor v1.0.0</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_current_tests_html(self) -> str:
        """Generate HTML for currently running tests"""
        if not self.current_tests:
            return ""
        
        items = ""
        for name, metric in self.current_tests.items():
            runtime = (datetime.now() - metric.timestamp).total_seconds()
            items += f"""
            <div class="test-item running">
                <span class="test-name">{name}</span>
                <span class="test-duration">{runtime:.1f}s</span>
                <span class="test-status status-running">Running</span>
            </div>
            """
        
        return f"""
        <div class="tests-section">
            <h2>🔄 Currently Running</h2>
            <div class="test-list">
                {items}
            </div>
        </div>
        """
    
    def _generate_recent_tests_html(self) -> str:
        """Generate HTML for recent test results"""
        recent = [m for m in self.metrics if m.status != 'running'][-10:]
        if not recent:
            return ""
        
        items = ""
        for metric in reversed(recent):
            status_class = f"status-{metric.status}"
            duration = f"{metric.duration_ms:.0f}ms" if metric.duration_ms else "-"
            items += f"""
            <div class="test-item {metric.status}">
                <span class="test-name">{metric.test_name}</span>
                <span class="test-duration">{duration}</span>
                <span class="test-status {status_class}">{metric.status.title()}</span>
            </div>
            """
        
        return f"""
        <div class="tests-section">
            <h2>📊 Recent Tests</h2>
            <div class="test-list">
                {items}
            </div>
        </div>
        """
    
    def start_dashboard(self, auto_open: bool = True):
        """Start the monitoring dashboard server"""
        dashboard_dir = Path(f"/tmp/webpilot-monitor-{self.port}")
        dashboard_dir.mkdir(exist_ok=True)
        
        # Initial dashboard generation
        self._update_dashboard()
        
        # Start HTTP server in background thread
        class DashboardHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(dashboard_dir), **kwargs)
            
            def log_message(self, format, *args):
                # Suppress request logging
                pass
        
        self.server = HTTPServer(('localhost', self.port), DashboardHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        url = f"http://localhost:{self.port}"
        self.logger.info(f"Dashboard started at: {url}")
        
        if auto_open:
            webbrowser.open(url)
        
        return url
    
    def stop_dashboard(self):
        """Stop the monitoring dashboard server"""
        if self.server:
            self.server.shutdown()
            self.server_thread.join(timeout=5)
            self.logger.info("Dashboard stopped")


class MetricsCollector:
    """Collect and aggregate performance metrics"""
    
    def __init__(self):
        self.metrics = []
        self.start_time = time.time()
        
    def add_metric(self, name: str, value: float, unit: str = 'ms'):
        """Add a performance metric"""
        self.metrics.append({
            'name': name,
            'value': value,
            'unit': unit,
            'timestamp': time.time() - self.start_time
        })
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        if not self.metrics:
            return {}
        
        by_name = {}
        for metric in self.metrics:
            name = metric['name']
            if name not in by_name:
                by_name[name] = []
            by_name[name].append(metric['value'])
        
        summary = {}
        for name, values in by_name.items():
            summary[name] = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'last': values[-1]
            }
        
        return summary
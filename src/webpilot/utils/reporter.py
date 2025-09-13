#!/usr/bin/env python3
"""
Enhanced Reporting for WebPilot
Generate beautiful HTML and JSON reports
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import base64

@dataclass
class TestResult:
    """Individual test result"""
    name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration_ms: float
    error: Optional[str] = None
    screenshot: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TestReport:
    """Rich test reporting with HTML and JSON output"""
    
    def __init__(self, title: str = "WebPilot Test Report"):
        self.title = title
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        self.metadata = {}
    
    def add_result(self, result: TestResult):
        """Add a test result to the report"""
        self.results.append(result)
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the report"""
        self.metadata[key] = value
    
    def generate_json_report(self) -> Dict:
        """Generate machine-readable JSON report"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == 'passed')
        failed = sum(1 for r in self.results if r.status == 'failed')
        skipped = sum(1 for r in self.results if r.status == 'skipped')
        
        duration = sum(r.duration_ms for r in self.results)
        
        return {
            'title': self.title,
            'timestamp': self.start_time.isoformat(),
            'duration_ms': duration,
            'summary': {
                'total': total_tests,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'pass_rate': (passed / total_tests * 100) if total_tests > 0 else 0
            },
            'metadata': self.metadata,
            'results': [
                {
                    'name': r.name,
                    'status': r.status,
                    'duration_ms': r.duration_ms,
                    'error': r.error,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
    
    def generate_html_report(self) -> str:
        """Generate beautiful HTML report with screenshots"""
        stats = self.generate_json_report()
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }}
        
        h1 {{
            color: #1a202c;
            margin-bottom: 1rem;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}
        
        .stat {{
            background: #f7fafc;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #4a5568;
        }}
        
        .stat-label {{
            font-size: 0.875rem;
            color: #718096;
            margin-top: 0.25rem;
        }}
        
        .passed {{ color: #48bb78; }}
        .failed {{ color: #f56565; }}
        .skipped {{ color: #ed8936; }}
        
        .results {{
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }}
        
        .result {{
            border-left: 4px solid;
            padding: 1rem;
            margin-bottom: 1rem;
            background: #f7fafc;
            border-radius: 0.25rem;
            transition: transform 0.2s;
        }}
        
        .result:hover {{
            transform: translateX(5px);
        }}
        
        .result.passed {{ border-color: #48bb78; }}
        .result.failed {{ border-color: #f56565; }}
        .result.skipped {{ border-color: #ed8936; }}
        
        .result-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
        
        .result-name {{
            font-weight: 600;
            color: #2d3748;
        }}
        
        .result-duration {{
            font-size: 0.875rem;
            color: #718096;
        }}
        
        .result-error {{
            background: #fff5f5;
            border: 1px solid #feb2b2;
            border-radius: 0.25rem;
            padding: 0.75rem;
            margin-top: 0.5rem;
            color: #742a2a;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
        }}
        
        .screenshot {{
            margin-top: 1rem;
            border-radius: 0.5rem;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .screenshot img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        
        .metadata {{
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            margin-top: 2rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }}
        
        .metadata h2 {{
            color: #1a202c;
            margin-bottom: 1rem;
        }}
        
        .metadata-item {{
            display: flex;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .metadata-key {{
            font-weight: 600;
            color: #4a5568;
            width: 200px;
        }}
        
        .metadata-value {{
            color: #718096;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚁 {self.title}</h1>
            <p>Generated: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{stats['summary']['total']}</div>
                    <div class="stat-label">Total Tests</div>
                </div>
                <div class="stat">
                    <div class="stat-value passed">{stats['summary']['passed']}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat">
                    <div class="stat-value failed">{stats['summary']['failed']}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat">
                    <div class="stat-value skipped">{stats['summary']['skipped']}</div>
                    <div class="stat-label">Skipped</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{stats['summary']['pass_rate']:.1f}%</div>
                    <div class="stat-label">Pass Rate</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{stats['duration_ms']/1000:.1f}s</div>
                    <div class="stat-label">Duration</div>
                </div>
            </div>
        </div>
        
        <div class="results">
            <h2>Test Results</h2>
            {''.join(self._generate_result_html(r) for r in self.results)}
        </div>
        
        {self._generate_metadata_html() if self.metadata else ''}
    </div>
</body>
</html>
"""
        return html
    
    def _generate_result_html(self, result: TestResult) -> str:
        """Generate HTML for a single test result"""
        status_icon = {
            'passed': '✅',
            'failed': '❌',
            'skipped': '⏭️'
        }.get(result.status, '❓')
        
        html = f"""
            <div class="result {result.status}">
                <div class="result-header">
                    <span class="result-name">{status_icon} {result.name}</span>
                    <span class="result-duration">{result.duration_ms:.1f}ms</span>
                </div>
        """
        
        if result.error:
            html += f"""
                <div class="result-error">{result.error}</div>
            """
        
        if result.screenshot:
            html += f"""
                <div class="screenshot">
                    <img src="{result.screenshot}" alt="Screenshot for {result.name}">
                </div>
            """
        
        html += "</div>"
        return html
    
    def _generate_metadata_html(self) -> str:
        """Generate HTML for metadata section"""
        if not self.metadata:
            return ""
        
        items = ''.join(
            f"""
            <div class="metadata-item">
                <div class="metadata-key">{key}</div>
                <div class="metadata-value">{value}</div>
            </div>
            """
            for key, value in self.metadata.items()
        )
        
        return f"""
        <div class="metadata">
            <h2>Metadata</h2>
            {items}
        </div>
        """
    
    def save_report(self, path: Path, format: str = 'both'):
        """Save report to file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format in ['json', 'both']:
            json_path = path.with_suffix('.json')
            with open(json_path, 'w') as f:
                json.dump(self.generate_json_report(), f, indent=2)
        
        if format in ['html', 'both']:
            html_path = path.with_suffix('.html')
            with open(html_path, 'w') as f:
                f.write(self.generate_html_report())


class PerformanceReport:
    """Performance metrics reporting"""
    
    def __init__(self):
        self.metrics = []
    
    def add_metric(self, url: str, metrics: Dict[str, Any]):
        """Add performance metrics for a URL"""
        self.metrics.append({
            'url': url,
            'timestamp': datetime.now().isoformat(),
            **metrics
        })
    
    def generate_summary(self) -> Dict:
        """Generate performance summary"""
        if not self.metrics:
            return {}
        
        avg_load_time = sum(m.get('load_time_ms', 0) for m in self.metrics) / len(self.metrics)
        avg_fcp = sum(m.get('first_contentful_paint_ms', 0) for m in self.metrics) / len(self.metrics)
        
        return {
            'total_pages': len(self.metrics),
            'average_load_time_ms': avg_load_time,
            'average_fcp_ms': avg_fcp,
            'slowest_page': max(self.metrics, key=lambda m: m.get('load_time_ms', 0)),
            'fastest_page': min(self.metrics, key=lambda m: m.get('load_time_ms', 0))
        }
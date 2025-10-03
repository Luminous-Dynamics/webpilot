#!/usr/bin/env python3
"""
Lighthouse Integration - Performance and Accessibility Auditing
Uses Playwright + Lighthouse to generate comprehensive audit reports
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class LighthouseAudit:
    """Run Lighthouse audits via Playwright"""
    
    # Lighthouse categories
    CATEGORIES = [
        'performance',
        'accessibility',
        'best-practices',
        'seo',
        'pwa'
    ]
    
    # Score thresholds
    SCORE_EXCELLENT = 90
    SCORE_GOOD = 50
    SCORE_POOR = 0
    
    def __init__(self):
        """Initialize Lighthouse auditor"""
        self.reports_dir = Path("lighthouse_reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.baseline_scores: Dict[str, Dict] = {}
    
    def run(self, url: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run Lighthouse audit on URL.
        
        Args:
            url: URL to audit
            categories: Categories to audit (None = all)
            
        Returns:
            Audit results with scores
        """
        if categories is None:
            categories = self.CATEGORIES
        
        print(f"🔍 Running Lighthouse audit on {url}...")
        
        try:
            # Run Lighthouse via CLI
            result = self._run_lighthouse_cli(url, categories)
            
            if result:
                print(f"\n📊 Lighthouse Scores:")
                self._print_scores(result)
                
                # Save report
                self._save_report(url, result)
                
                return result
            else:
                print("❌ Lighthouse audit failed")
                return {}
        
        except Exception as e:
            print(f"❌ Error running Lighthouse: {e}")
            return {}
    
    def _run_lighthouse_cli(self, url: str, categories: List[str]) -> Optional[Dict]:
        """Run Lighthouse via CLI and parse JSON output"""
        try:
            # Create temp file for output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                tmp_path = tmp.name
            
            # Build Lighthouse command
            cmd = [
                'lighthouse',
                url,
                '--output=json',
                f'--output-path={tmp_path}',
                '--quiet',
                '--chrome-flags=--headless'
            ]
            
            # Add category flags
            for category in categories:
                cmd.append(f'--only-categories={category}')
            
            # Run Lighthouse
            subprocess.run(cmd, capture_output=True, timeout=60)
            
            # Parse JSON output
            with open(tmp_path) as f:
                data = json.load(f)
            
            # Clean up
            Path(tmp_path).unlink()
            
            # Extract scores
            return self._parse_lighthouse_output(data)
        
        except FileNotFoundError:
            print("❌ Lighthouse CLI not found. Install with: npm install -g lighthouse")
            return None
        except subprocess.TimeoutExpired:
            print("❌ Lighthouse audit timed out")
            return None
        except Exception as e:
            print(f"❌ Error running Lighthouse CLI: {e}")
            return None
    
    def _parse_lighthouse_output(self, data: Dict) -> Dict[str, Any]:
        """Parse Lighthouse JSON output into structured results"""
        categories = data.get('categories', {})
        audits = data.get('audits', {})
        
        results = {
            'url': data.get('finalUrl'),
            'fetch_time': data.get('fetchTime'),
            'scores': {},
            'metrics': {},
            'opportunities': [],
            'diagnostics': []
        }
        
        # Extract category scores
        for category_id, category_data in categories.items():
            results['scores'][category_id] = {
                'score': int(category_data.get('score', 0) * 100),
                'title': category_data.get('title')
            }
        
        # Extract key metrics
        metrics_to_extract = [
            'first-contentful-paint',
            'largest-contentful-paint',
            'total-blocking-time',
            'cumulative-layout-shift',
            'speed-index',
            'interactive'
        ]
        
        for metric_id in metrics_to_extract:
            if metric_id in audits:
                audit = audits[metric_id]
                results['metrics'][metric_id] = {
                    'title': audit.get('title'),
                    'score': audit.get('score'),
                    'displayValue': audit.get('displayValue'),
                    'numericValue': audit.get('numericValue')
                }
        
        # Extract opportunities (performance improvements)
        for audit_id, audit in audits.items():
            if audit.get('details', {}).get('type') == 'opportunity':
                if audit.get('score', 1) < 1:  # Has opportunity
                    results['opportunities'].append({
                        'id': audit_id,
                        'title': audit.get('title'),
                        'description': audit.get('description'),
                        'score': audit.get('score'),
                        'savings': audit.get('details', {}).get('overallSavingsMs', 0)
                    })
        
        return results
    
    def _print_scores(self, results: Dict):
        """Pretty print Lighthouse scores"""
        for category, data in results.get('scores', {}).items():
            score = data['score']
            emoji = self._score_emoji(score)
            print(f"  {emoji} {data['title']:20s}: {score:3d}/100")
    
    def _score_emoji(self, score: int) -> str:
        """Get emoji for score"""
        if score >= self.SCORE_EXCELLENT:
            return "🟢"
        elif score >= self.SCORE_GOOD:
            return "🟡"
        else:
            return "🔴"
    
    def _save_report(self, url: str, results: Dict):
        """Save audit report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_slug = url.replace('http://', '').replace('https://', '').replace('/', '_')
        filename = f"lighthouse_{url_slug}_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Report saved: {filepath}")
    
    def set_baseline(self, name: str, scores: Dict):
        """Set baseline scores for comparison"""
        self.baseline_scores[name] = scores
        print(f"✅ Baseline set for '{name}'")
    
    def compare_with_baseline(self, name: str, current_scores: Dict) -> Dict[str, int]:
        """
        Compare current scores with baseline.
        
        Returns:
            Dictionary of score differences (positive = improvement)
        """
        if name not in self.baseline_scores:
            print(f"⚠️  No baseline found for '{name}'")
            return {}
        
        baseline = self.baseline_scores[name]
        differences = {}
        
        print(f"\n📊 Comparing with baseline '{name}':")
        
        for category in current_scores.get('scores', {}):
            if category in baseline.get('scores', {}):
                current = current_scores['scores'][category]['score']
                base = baseline['scores'][category]['score']
                diff = current - base
                differences[category] = diff
                
                emoji = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                sign = "+" if diff > 0 else ""
                print(f"  {emoji} {category:20s}: {sign}{diff:3d} points")
        
        return differences
    
    def run_and_compare(self, url: str, baseline_name: str) -> bool:
        """
        Run audit and compare with baseline.
        
        Returns:
            True if no regressions, False if any scores decreased
        """
        results = self.run(url)
        if not results:
            return False
        
        differences = self.compare_with_baseline(baseline_name, results)
        
        # Check for regressions
        regressions = [cat for cat, diff in differences.items() if diff < -5]
        
        if regressions:
            print(f"\n❌ Performance regressions detected in: {', '.join(regressions)}")
            return False
        else:
            print(f"\n✅ No significant regressions")
            return True
    
    def audit_all_categories(self, url: str) -> Dict:
        """Run comprehensive audit on all categories"""
        return self.run(url, self.CATEGORIES)
    
    def audit_performance_only(self, url: str) -> Dict:
        """Quick performance-only audit"""
        return self.run(url, ['performance'])
    
    def audit_accessibility_only(self, url: str) -> Dict:
        """Accessibility-only audit"""
        return self.run(url, ['accessibility'])
    
    def get_performance_metrics(self, url: str) -> Dict:
        """Get detailed performance metrics"""
        results = self.audit_performance_only(url)
        return results.get('metrics', {})
    
    def get_opportunities(self, url: str) -> List[Dict]:
        """Get performance improvement opportunities"""
        results = self.audit_performance_only(url)
        return results.get('opportunities', [])


# Quick usage functions
def audit_url(url: str) -> Dict:
    """Quick function to audit a URL"""
    lighthouse = LighthouseAudit()
    return lighthouse.run(url)


def check_performance(url: str) -> int:
    """Quick performance check - returns score"""
    lighthouse = LighthouseAudit()
    results = lighthouse.audit_performance_only(url)
    return results.get('scores', {}).get('performance', {}).get('score', 0)


# Example usage
if __name__ == "__main__":
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    
    print(f"🚀 Lighthouse Audit Demo")
    print(f"   URL: {url}\n")
    
    lighthouse = LighthouseAudit()
    
    # Run full audit
    results = lighthouse.run(url)
    
    # Show opportunities
    opportunities = results.get('opportunities', [])
    if opportunities:
        print(f"\n💡 Performance Opportunities:")
        for opp in opportunities[:5]:  # Top 5
            savings = opp.get('savings', 0) / 1000  # Convert to seconds
            print(f"  • {opp['title']}: Save ~{savings:.1f}s")
    
    # Set as baseline
    lighthouse.set_baseline('production', results)
    
    print("\n✨ Audit complete!")

#!/usr/bin/env python3
"""
WebPilot DevOps - Enhanced features for Web Development Operations
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import subprocess
from datetime import datetime

from ..core import WebPilot, ActionResult, ActionType
from ..backends.selenium import SeleniumWebPilot
from ..backends.async_pilot import AsyncWebPilot
from .vision import WebPilotVision


@dataclass
class PerformanceMetrics:
    """Performance metrics for a page"""
    url: str
    load_time_ms: float
    dom_ready_ms: float
    first_paint_ms: float
    first_contentful_paint_ms: float
    largest_contentful_paint_ms: float
    time_to_interactive_ms: float
    total_size_bytes: int
    num_requests: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'url': self.url,
            'load_time_ms': self.load_time_ms,
            'dom_ready_ms': self.dom_ready_ms,
            'first_paint_ms': self.first_paint_ms,
            'fcp_ms': self.first_contentful_paint_ms,
            'lcp_ms': self.largest_contentful_paint_ms,
            'tti_ms': self.time_to_interactive_ms,
            'total_size': self.total_size_bytes,
            'requests': self.num_requests,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AccessibilityReport:
    """Accessibility audit results"""
    url: str
    score: float
    issues: List[Dict]
    warnings: List[Dict]
    passes: List[Dict]
    
    @property
    def passed(self) -> bool:
        return self.score >= 90 and len(self.issues) == 0


class WebPilotDevOps:
    """Enhanced WebPilot for DevOps operations"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.selenium = None
        self.vision = WebPilotVision()
        self.test_results = []
        self.performance_history = []
        
    async def smoke_test(self, urls: List[str], 
                         expected_status: int = 200) -> Dict:
        """Run smoke tests on multiple URLs"""
        print(f"🔥 Running smoke tests on {len(urls)} URLs...")
        
        async with AsyncWebPilot() as pilot:
            results = await pilot.batch_fetch(urls)
            
            passed = 0
            failed = []
            
            for url, result in zip(urls, results):
                if result.success:
                    status = result.data.get('status', 0)
                    if status == expected_status:
                        passed += 1
                    else:
                        failed.append({
                            'url': url,
                            'expected': expected_status,
                            'actual': status
                        })
                else:
                    failed.append({
                        'url': url,
                        'error': result.error
                    })
            
            return {
                'total': len(urls),
                'passed': passed,
                'failed': len(failed),
                'failures': failed,
                'success_rate': (passed / len(urls)) * 100
            }
    
    def visual_regression_test(self, url: str, 
                               baseline_path: str,
                               threshold: float = 0.95) -> Dict:
        """Compare current page against baseline screenshot"""
        print(f"📸 Visual regression test for {url}")
        
        with SeleniumWebPilot(headless=self.headless) as pilot:
            # Take current screenshot
            pilot.start(url)
            time.sleep(3)  # Wait for page to stabilize
            result = pilot.screenshot("current.png")
            
            if not result.success:
                return {'success': False, 'error': 'Failed to capture screenshot'}
            
            current_path = result.data.get('path')
            
            # Compare with baseline
            if Path(baseline_path).exists():
                similarity = self._compare_images(baseline_path, current_path)
                
                passed = similarity >= threshold
                
                return {
                    'success': True,
                    'passed': passed,
                    'similarity': similarity,
                    'threshold': threshold,
                    'baseline': baseline_path,
                    'current': current_path
                }
            else:
                # No baseline, create it
                import shutil
                shutil.copy(current_path, baseline_path)
                return {
                    'success': True,
                    'baseline_created': True,
                    'path': baseline_path
                }
    
    def _compare_images(self, img1_path: str, img2_path: str) -> float:
        """Compare two images and return similarity score"""
        try:
            import cv2
            import numpy as np
            
            img1 = cv2.imread(img1_path)
            img2 = cv2.imread(img2_path)
            
            # Resize if different sizes
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            
            # Calculate similarity
            diff = cv2.absdiff(img1, img2)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Calculate percentage of similar pixels
            threshold = 30
            _, thresh = cv2.threshold(diff_gray, threshold, 255, cv2.THRESH_BINARY)
            similar_pixels = np.count_nonzero(thresh == 0)
            total_pixels = thresh.shape[0] * thresh.shape[1]
            
            similarity = similar_pixels / total_pixels
            return similarity
            
        except Exception as e:
            print(f"Image comparison error: {e}")
            return 0.0
    
    def performance_audit(self, url: str) -> PerformanceMetrics:
        """Run performance audit on a page"""
        print(f"⚡ Performance audit for {url}")
        
        with SeleniumWebPilot(headless=self.headless) as pilot:
            pilot.start(url)
            
            # Get performance metrics via JavaScript
            perf_script = """
            return {
                loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                domReady: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
                firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
                fcp: performance.getEntriesByType('paint').find(e => e.name === 'first-contentful-paint')?.startTime || 0,
                resources: performance.getEntriesByType('resource').length,
                totalSize: performance.getEntriesByType('resource').reduce((sum, r) => sum + (r.transferSize || 0), 0)
            };
            """
            
            result = pilot.execute_javascript(perf_script)
            
            if result.success:
                data = result.data.get('result', {})
                # Handle case where result is a string instead of dict
                if isinstance(data, str):
                    data = {}
                
                metrics = PerformanceMetrics(
                    url=url,
                    load_time_ms=data.get('loadTime', 0),
                    dom_ready_ms=data.get('domReady', 0),
                    first_paint_ms=data.get('firstPaint', 0),
                    first_contentful_paint_ms=data.get('fcp', 0),
                    largest_contentful_paint_ms=0,  # Would need more complex measurement
                    time_to_interactive_ms=data.get('domReady', 0),
                    total_size_bytes=data.get('totalSize', 0),
                    num_requests=data.get('resources', 0)
                )
                
                self.performance_history.append(metrics)
                return metrics
            
            return None
    
    def accessibility_check(self, url: str) -> AccessibilityReport:
        """Run accessibility checks on a page"""
        print(f"♿ Accessibility check for {url}")
        
        with SeleniumWebPilot(headless=self.headless) as pilot:
            pilot.start(url)
            
            # Basic accessibility checks
            checks_script = """
            const results = {
                issues: [],
                warnings: [],
                passes: []
            };
            
            // Check for alt text on images
            document.querySelectorAll('img').forEach(img => {
                if (!img.alt) {
                    results.issues.push({
                        type: 'missing-alt',
                        element: img.outerHTML.substring(0, 100)
                    });
                }
            });
            
            // Check for form labels
            document.querySelectorAll('input, select, textarea').forEach(input => {
                if (!input.labels?.length && !input.getAttribute('aria-label')) {
                    results.warnings.push({
                        type: 'missing-label',
                        element: input.outerHTML.substring(0, 100)
                    });
                }
            });
            
            // Check for heading hierarchy
            const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'));
            let lastLevel = 0;
            headings.forEach(h => {
                const level = parseInt(h.tagName[1]);
                if (level - lastLevel > 1) {
                    results.warnings.push({
                        type: 'heading-skip',
                        from: `h${lastLevel}`,
                        to: h.tagName
                    });
                }
                lastLevel = level;
            });
            
            // Check for contrast (simplified)
            if (document.body) {
                const bgColor = window.getComputedStyle(document.body).backgroundColor;
                const textColor = window.getComputedStyle(document.body).color;
                results.passes.push({
                    type: 'has-colors',
                    bg: bgColor,
                    text: textColor
                });
            }
            
            // Calculate score
            const score = Math.max(0, 100 - (results.issues.length * 10) - (results.warnings.length * 5));
            
            return {
                score: score,
                issues: results.issues,
                warnings: results.warnings,
                passes: results.passes
            };
            """
            
            result = pilot.execute_javascript(checks_script)
            
            if result.success:
                data = result.data.get('result', {})
                # Handle case where result is a string instead of dict
                if isinstance(data, str):
                    data = {}
                
                return AccessibilityReport(
                    url=url,
                    score=data.get('score', 0),
                    issues=data.get('issues', []),
                    warnings=data.get('warnings', []),
                    passes=data.get('passes', [])
                )
            
            return AccessibilityReport(url=url, score=0, issues=[], warnings=[], passes=[])
    
    async def monitor_deployment(self, url: str, 
                                expected_version: str,
                                max_wait: int = 300,
                                check_interval: int = 10) -> Dict:
        """Monitor deployment until new version is live"""
        print(f"🚀 Monitoring deployment at {url}")
        print(f"   Expecting version: {expected_version}")
        
        start_time = time.time()
        checks = 0
        
        async with AsyncWebPilot() as pilot:
            while time.time() - start_time < max_wait:
                checks += 1
                
                # Fetch page
                result = await pilot.fetch_content(url)
                
                if result.success:
                    content = result.data.get('content_preview', '')
                    
                    # Check if version string is present
                    if expected_version in content:
                        elapsed = time.time() - start_time
                        
                        return {
                            'success': True,
                            'version_found': expected_version,
                            'time_elapsed': elapsed,
                            'checks_performed': checks,
                            'status': 'deployed'
                        }
                
                # Wait before next check
                print(f"   Check {checks}: Version not found, waiting {check_interval}s...")
                await asyncio.sleep(check_interval)
        
        return {
            'success': False,
            'timeout': True,
            'time_elapsed': max_wait,
            'checks_performed': checks,
            'status': 'timeout'
        }
    
    def seo_audit(self, url: str) -> Dict:
        """Run SEO audit on a page"""
        print(f"🔍 SEO audit for {url}")
        
        with SeleniumWebPilot(headless=self.headless) as pilot:
            pilot.start(url)
            
            seo_script = """
            const audit = {
                title: document.title,
                titleLength: document.title.length,
                metaDescription: document.querySelector('meta[name="description"]')?.content || null,
                metaKeywords: document.querySelector('meta[name="keywords"]')?.content || null,
                h1Count: document.querySelectorAll('h1').length,
                h1Text: Array.from(document.querySelectorAll('h1')).map(h => h.textContent),
                canonicalUrl: document.querySelector('link[rel="canonical"]')?.href || null,
                ogTitle: document.querySelector('meta[property="og:title"]')?.content || null,
                ogDescription: document.querySelector('meta[property="og:description"]')?.content || null,
                ogImage: document.querySelector('meta[property="og:image"]')?.content || null,
                structuredData: Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s => s.textContent),
                imagesMissingAlt: document.querySelectorAll('img:not([alt])').length,
                totalImages: document.querySelectorAll('img').length,
                internalLinks: document.querySelectorAll('a[href^="/"], a[href^="' + window.location.origin + '"]').length,
                externalLinks: document.querySelectorAll('a[href^="http"]:not([href^="' + window.location.origin + '"])').length
            };
            
            // SEO scoring
            let score = 100;
            const issues = [];
            
            if (!audit.title || audit.titleLength < 10) {
                score -= 20;
                issues.push('Missing or too short title');
            }
            if (audit.titleLength > 60) {
                score -= 5;
                issues.push('Title too long (>60 chars)');
            }
            if (!audit.metaDescription) {
                score -= 15;
                issues.push('Missing meta description');
            }
            if (audit.h1Count === 0) {
                score -= 15;
                issues.push('No H1 tag found');
            }
            if (audit.h1Count > 1) {
                score -= 5;
                issues.push('Multiple H1 tags');
            }
            if (!audit.canonicalUrl) {
                score -= 5;
                issues.push('Missing canonical URL');
            }
            if (!audit.ogTitle || !audit.ogDescription || !audit.ogImage) {
                score -= 10;
                issues.push('Incomplete Open Graph tags');
            }
            if (audit.imagesMissingAlt > 0) {
                score -= Math.min(10, audit.imagesMissingAlt * 2);
                issues.push(`${audit.imagesMissingAlt} images missing alt text`);
            }
            
            audit.score = Math.max(0, score);
            audit.issues = issues;
            
            return audit;
            """
            
            result = pilot.execute_javascript(seo_script)
            
            if result.success:
                data = result.data.get('result', {})
                # Handle case where result is a string instead of dict
                if isinstance(data, str):
                    return {'error': 'Failed to parse SEO audit results'}
                return data
            
            return {'error': 'Failed to run SEO audit'}
    
    async def load_test(self, url: str, 
                        concurrent_users: int = 10,
                        duration_seconds: int = 30) -> Dict:
        """Simple load test"""
        print(f"🔨 Load testing {url}")
        print(f"   Users: {concurrent_users}, Duration: {duration_seconds}s")
        
        results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'errors': []
        }
        
        async def user_session():
            async with AsyncWebPilot() as pilot:
                end_time = time.time() + duration_seconds
                
                while time.time() < end_time:
                    start = time.time()
                    result = await pilot.fetch_content(url)
                    elapsed = (time.time() - start) * 1000
                    
                    results['total_requests'] += 1
                    results['response_times'].append(elapsed)
                    
                    if result.success:
                        results['successful_requests'] += 1
                    else:
                        results['failed_requests'] += 1
                        results['errors'].append(result.error)
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
        
        # Run concurrent user sessions
        tasks = [user_session() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)
        
        # Calculate statistics
        if results['response_times']:
            results['avg_response_time'] = sum(results['response_times']) / len(results['response_times'])
            results['min_response_time'] = min(results['response_times'])
            results['max_response_time'] = max(results['response_times'])
            results['requests_per_second'] = results['total_requests'] / duration_seconds
        
        return results
    
    def generate_lighthouse_report(self, url: str) -> Dict:
        """Generate a Lighthouse-style report"""
        print(f"🏗️ Generating comprehensive report for {url}")
        
        report = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'scores': {}
        }
        
        # Performance
        perf = self.performance_audit(url)
        if perf:
            perf_score = 100
            if perf.load_time_ms > 3000:
                perf_score -= 20
            if perf.first_contentful_paint_ms > 1800:
                perf_score -= 20
            if perf.time_to_interactive_ms > 3800:
                perf_score -= 20
            
            report['scores']['performance'] = max(0, perf_score)
            report['performance'] = perf.to_dict()
        
        # Accessibility
        a11y = self.accessibility_check(url)
        report['scores']['accessibility'] = a11y.score
        report['accessibility'] = {
            'score': a11y.score,
            'issues': a11y.issues,
            'warnings': a11y.warnings
        }
        
        # SEO
        seo = self.seo_audit(url)
        report['scores']['seo'] = seo.get('score', 0)
        report['seo'] = seo
        
        # Overall score
        scores = list(report['scores'].values())
        report['overall_score'] = sum(scores) / len(scores) if scores else 0
        
        return report


def test_devops_features():
    """Test DevOps features"""
    import asyncio
    
    devops = WebPilotDevOps(headless=True)
    
    print("\n🚀 WebPilot DevOps Features Demo")
    print("=" * 60)
    
    # 1. Smoke test
    print("\n1. Smoke Testing...")
    urls = [
        "https://example.com",
        "https://github.com",
        "https://httpstat.us/404"  # This will fail
    ]
    
    result = asyncio.run(devops.smoke_test(urls))
    print(f"   ✅ Passed: {result['passed']}/{result['total']}")
    print(f"   Success Rate: {result['success_rate']:.1f}%")
    
    # 2. Performance audit
    print("\n2. Performance Audit...")
    perf = devops.performance_audit("https://example.com")
    if perf:
        print(f"   Load Time: {perf.load_time_ms:.0f}ms")
        print(f"   DOM Ready: {perf.dom_ready_ms:.0f}ms")
        print(f"   Total Size: {perf.total_size_bytes:,} bytes")
    
    # 3. Accessibility check
    print("\n3. Accessibility Check...")
    a11y = devops.accessibility_check("https://example.com")
    print(f"   Score: {a11y.score}/100")
    print(f"   Issues: {len(a11y.issues)}")
    print(f"   Warnings: {len(a11y.warnings)}")
    
    # 4. SEO audit
    print("\n4. SEO Audit...")
    seo = devops.seo_audit("https://example.com")
    print(f"   SEO Score: {seo.get('score', 0)}/100")
    if seo.get('issues'):
        for issue in seo['issues'][:3]:
            print(f"   ⚠️  {issue}")
    
    # 5. Comprehensive report
    print("\n5. Generating Comprehensive Report...")
    report = devops.generate_lighthouse_report("https://example.com")
    print(f"   Overall Score: {report['overall_score']:.1f}/100")
    print(f"   • Performance: {report['scores'].get('performance', 0)}/100")
    print(f"   • Accessibility: {report['scores'].get('accessibility', 0)}/100")
    print(f"   • SEO: {report['scores'].get('seo', 0)}/100")
    
    # Save report
    report_path = Path("/tmp/webpilot-devops-report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📊 Full report saved to: {report_path}")
    
    print("\n✨ DevOps features test complete!")


if __name__ == "__main__":
    test_devops_features()
#!/usr/bin/env python3
"""
Terra Atlas Testing Suite - Real Project Validation
Tests the live Terra Atlas platform at atlas.luminousdynamics.io
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.webpilot import WebPilot, WebPilotDevOps, AsyncWebPilot
from src.webpilot.backends.selenium import SeleniumWebPilot


class TerraAtlasTestSuite:
    """Comprehensive test suite for Terra Atlas platform"""
    
    def __init__(self):
        self.base_url = "https://atlas.luminousdynamics.io"
        self.devops = WebPilotDevOps(headless=True)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'site': 'Terra Atlas',
            'url': self.base_url,
            'tests': {}
        }
        
        # Key pages to test
        self.key_pages = [
            "/",  # Homepage with 3D globe
            "/explore",  # Project explorer
            "/projects",  # Project listing
            "/about",  # About page
            "/invest",  # Investment flow
        ]
        
        # Create results directory
        self.results_dir = Path("terra-atlas-tests")
        self.results_dir.mkdir(exist_ok=True)
        
    async def test_homepage_load(self):
        """Test homepage loads and 3D globe renders"""
        print("\n🌍 Testing Terra Atlas Homepage...")
        
        async with AsyncWebPilot() as pilot:
            result = await pilot.fetch_content(self.base_url)
            
            if result.success:
                content_len = result.data.get('length', 0)
                status = result.data.get('status', 0)
                
                # Check for key elements
                content = result.data.get('content_preview', '')
                has_globe = 'globe' in content.lower() or 'canvas' in content.lower()
                has_projects = 'projects' in content.lower()
                
                self.results['tests']['homepage'] = {
                    'success': True,
                    'status_code': status,
                    'content_size': content_len,
                    'has_3d_globe': has_globe,
                    'has_projects': has_projects,
                    'load_time_ms': result.duration_ms
                }
                
                print(f"   ✅ Homepage loaded successfully")
                print(f"   Status: {status}")
                print(f"   Size: {content_len:,} bytes")
                print(f"   Load time: {result.duration_ms:.1f}ms")
                print(f"   3D Globe: {'✅' if has_globe else '❌'}")
                print(f"   Projects: {'✅' if has_projects else '❌'}")
            else:
                self.results['tests']['homepage'] = {
                    'success': False,
                    'error': result.error
                }
                print(f"   ❌ Homepage failed: {result.error}")
    
    async def test_page_availability(self):
        """Test all key pages are accessible"""
        print("\n📄 Testing Page Availability...")
        
        urls = [self.base_url + page for page in self.key_pages]
        
        async with AsyncWebPilot() as pilot:
            results = await pilot.batch_fetch(urls)
            
            page_results = {}
            for page, result in zip(self.key_pages, results):
                if result.success:
                    status = result.data.get('status', 0)
                    success = status == 200
                    page_results[page] = {
                        'success': success,
                        'status': status,
                        'load_time_ms': result.duration_ms
                    }
                    
                    icon = '✅' if success else '❌'
                    print(f"   {icon} {page}: {status} ({result.duration_ms:.0f}ms)")
                else:
                    page_results[page] = {
                        'success': False,
                        'error': result.error
                    }
                    print(f"   ❌ {page}: {result.error}")
            
            self.results['tests']['page_availability'] = page_results
    
    def test_performance(self):
        """Test performance metrics"""
        print("\n⚡ Testing Performance Metrics...")
        
        perf = self.devops.performance_audit(self.base_url)
        
        if perf:
            # Evaluate performance
            scores = {
                'load_time': 100 if perf.load_time_ms < 3000 else 
                            70 if perf.load_time_ms < 5000 else 40,
                'fcp': 100 if perf.first_contentful_paint_ms < 1800 else
                       70 if perf.first_contentful_paint_ms < 3000 else 40,
                'dom_ready': 100 if perf.dom_ready_ms < 1500 else
                            70 if perf.dom_ready_ms < 3000 else 40
            }
            
            overall_score = sum(scores.values()) / len(scores)
            
            self.results['tests']['performance'] = {
                'success': True,
                'metrics': perf.to_dict(),
                'scores': scores,
                'overall_score': overall_score
            }
            
            print(f"   Overall Score: {overall_score:.0f}/100")
            print(f"   • Load Time: {perf.load_time_ms:.0f}ms (Score: {scores['load_time']})")
            print(f"   • First Contentful Paint: {perf.first_contentful_paint_ms:.0f}ms (Score: {scores['fcp']})")
            print(f"   • DOM Ready: {perf.dom_ready_ms:.0f}ms (Score: {scores['dom_ready']})")
            print(f"   • Total Size: {perf.total_size_bytes:,} bytes")
            print(f"   • Requests: {perf.num_requests}")
        else:
            self.results['tests']['performance'] = {
                'success': False,
                'error': 'Performance audit failed'
            }
            print("   ❌ Performance audit failed")
    
    def test_accessibility(self):
        """Test accessibility compliance"""
        print("\n♿ Testing Accessibility...")
        
        a11y = self.devops.accessibility_check(self.base_url)
        
        self.results['tests']['accessibility'] = {
            'success': a11y.passed,
            'score': a11y.score,
            'issues': a11y.issues,
            'warnings': a11y.warnings
        }
        
        print(f"   Score: {a11y.score}/100 {'✅' if a11y.passed else '❌'}")
        
        if a11y.issues:
            print(f"   Issues found: {len(a11y.issues)}")
            for issue in a11y.issues[:3]:  # Show first 3
                print(f"     • {issue.get('type', 'Unknown issue')}")
        
        if a11y.warnings:
            print(f"   Warnings: {len(a11y.warnings)}")
    
    def test_seo(self):
        """Test SEO optimization"""
        print("\n🔍 Testing SEO...")
        
        seo = self.devops.seo_audit(self.base_url)
        
        if seo:
            self.results['tests']['seo'] = seo
            
            score = seo.get('score', 0)
            print(f"   SEO Score: {score}/100 {'✅' if score >= 80 else '⚠️' if score >= 60 else '❌'}")
            
            if seo.get('title'):
                print(f"   • Title: '{seo['title'][:50]}...' ({seo.get('titleLength', 0)} chars)")
            
            if seo.get('metaDescription'):
                print(f"   • Meta Description: ✅ Present")
            else:
                print(f"   • Meta Description: ❌ Missing")
            
            if seo.get('ogTitle') and seo.get('ogDescription') and seo.get('ogImage'):
                print(f"   • Open Graph: ✅ Complete")
            else:
                print(f"   • Open Graph: ⚠️ Incomplete")
            
            if seo.get('issues'):
                print(f"   Issues:")
                for issue in seo['issues'][:3]:
                    print(f"     • {issue}")
    
    def test_visual_baseline(self):
        """Create visual baseline screenshots"""
        print("\n📸 Creating Visual Baselines...")
        
        baselines_dir = self.results_dir / "baselines"
        baselines_dir.mkdir(exist_ok=True)
        
        with SeleniumWebPilot(headless=True) as pilot:
            for page in self.key_pages[:3]:  # Test first 3 pages
                url = self.base_url + page
                page_name = page.replace('/', 'home') if page == '/' else page.replace('/', '')
                
                print(f"   Capturing {page_name}...")
                pilot.start(url)
                
                # Wait for page to load
                import time
                time.sleep(3)
                
                # Take screenshot
                screenshot_path = baselines_dir / f"{page_name}_baseline.png"
                result = pilot.screenshot(str(screenshot_path))
                
                if result.success:
                    print(f"     ✅ Saved: {screenshot_path.name}")
                else:
                    print(f"     ❌ Failed: {result.error}")
    
    async def test_api_endpoints(self):
        """Test API endpoints if available"""
        print("\n🔌 Testing API Endpoints...")
        
        api_endpoints = [
            "/api/projects",
            "/api/stats",
            "/api/health"
        ]
        
        async with AsyncWebPilot() as pilot:
            for endpoint in api_endpoints:
                url = self.base_url + endpoint
                result = await pilot.fetch_content(url)
                
                if result.success:
                    status = result.data.get('status', 0)
                    if status == 200:
                        print(f"   ✅ {endpoint}: {status}")
                    elif status == 404:
                        print(f"   ⚠️ {endpoint}: Not found (might not be implemented)")
                    else:
                        print(f"   ❌ {endpoint}: {status}")
                else:
                    print(f"   ❌ {endpoint}: {result.error}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report...")
        
        # Calculate overall health
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for test in self.results['tests'].values() 
                          if test.get('success', False))
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Save JSON report
        report_path = self.results_dir / f"terra_atlas_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"   ✅ Report saved: {report_path}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📈 TERRA ATLAS TEST SUMMARY")
        print("=" * 60)
        print(f"Site: {self.base_url}")
        print(f"Time: {self.results['timestamp']}")
        print(f"Tests Run: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {total_tests - passed_tests} ❌")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        # Performance summary
        if 'performance' in self.results['tests'] and self.results['tests']['performance'].get('success'):
            perf = self.results['tests']['performance']
            print(f"\nPerformance Score: {perf.get('overall_score', 0):.0f}/100")
        
        # Accessibility summary
        if 'accessibility' in self.results['tests']:
            a11y = self.results['tests']['accessibility']
            print(f"Accessibility Score: {a11y.get('score', 0)}/100")
        
        # SEO summary
        if 'seo' in self.results['tests']:
            seo = self.results['tests']['seo']
            print(f"SEO Score: {seo.get('score', 0)}/100")
        
        print("=" * 60)
        
        return report_path
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("\n🚀 TERRA ATLAS COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"Testing: {self.base_url}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Run async tests
        await self.test_homepage_load()
        await self.test_page_availability()
        await self.test_api_endpoints()
        
        # Run sync tests
        self.test_performance()
        self.test_accessibility()
        self.test_seo()
        self.test_visual_baseline()
        
        # Generate report
        report_path = self.generate_report()
        
        return report_path


async def main():
    """Run Terra Atlas tests"""
    suite = TerraAtlasTestSuite()
    report_path = await suite.run_all_tests()
    
    print(f"\n✨ Testing complete! Report: {report_path}")
    print("\nNext steps:")
    print("1. Review the report for any issues")
    print("2. Set up regular monitoring with these tests")
    print("3. Create CI/CD integration for automated testing")
    print("4. Establish performance budgets based on baselines")


if __name__ == "__main__":
    asyncio.run(main())
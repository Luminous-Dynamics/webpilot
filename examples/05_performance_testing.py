#!/usr/bin/env python3
"""
WebPilot Performance Testing Example

This example demonstrates:
- Page load time measurement
- Network performance analysis
- Resource usage monitoring
- Performance regression detection
- Lighthouse integration
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webpilot import WebPilot
from webpilot.performance import (
    PerformanceMonitor,
    LighthouseRunner,
    NetworkThrottler,
    ResourceMonitor,
    PerformanceReport
)


def measure_page_load_times():
    """Measure page load times for various pages."""
    print("⏱️  Measuring Page Load Times")
    print("=" * 50)
    
    urls = [
        "https://example.com",
        "https://httpbin.org",
        "https://www.google.com"
    ]
    
    with WebPilot() as pilot:
        monitor = PerformanceMonitor(pilot)
        
        results = []
        for url in urls:
            print(f"\n📊 Testing: {url}")
            
            # Start performance monitoring
            monitor.start()
            
            # Navigate to page
            start_time = time.time()
            pilot.start(url)
            load_time = time.time() - start_time
            
            # Get performance metrics
            metrics = monitor.get_metrics()
            
            # Get navigation timing
            timing = pilot.execute_script("return performance.timing")
            
            # Calculate key metrics
            dom_ready = (timing["domContentLoadedEventEnd"] - 
                        timing["navigationStart"]) / 1000
            page_complete = (timing["loadEventEnd"] - 
                           timing["navigationStart"]) / 1000
            
            result = {
                "url": url,
                "load_time": load_time,
                "dom_ready": dom_ready,
                "page_complete": page_complete,
                "first_byte": metrics.get("time_to_first_byte", 0),
                "first_paint": metrics.get("first_paint", 0),
                "first_contentful_paint": metrics.get("first_contentful_paint", 0),
                "largest_contentful_paint": metrics.get("largest_contentful_paint", 0)
            }
            
            results.append(result)
            
            # Display results
            print(f"   Load Time: {load_time:.2f}s")
            print(f"   DOM Ready: {dom_ready:.2f}s")
            print(f"   Page Complete: {page_complete:.2f}s")
            print(f"   First Byte: {result['first_byte']:.2f}s")
            print(f"   First Paint: {result['first_paint']:.2f}s")
            
            # Stop monitoring
            monitor.stop()
        
        return results


def analyze_network_performance():
    """Analyze network performance and resource loading."""
    print("\n🌐 Analyzing Network Performance")
    print("=" * 50)
    
    with WebPilot() as pilot:
        monitor = PerformanceMonitor(pilot)
        
        # Enable network monitoring
        monitor.enable_network_monitoring()
        
        # Navigate to test page
        url = "https://www.example.com"
        print(f"\n📊 Analyzing: {url}")
        
        pilot.start(url)
        
        # Get network entries
        network_entries = pilot.execute_script("""
            return performance.getEntriesByType('resource').map(entry => ({
                name: entry.name,
                type: entry.initiatorType,
                duration: entry.duration,
                size: entry.transferSize || 0,
                protocol: entry.nextHopProtocol
            }));
        """)
        
        # Analyze by resource type
        resource_stats = {}
        for entry in network_entries:
            resource_type = entry.get("type", "unknown")
            if resource_type not in resource_stats:
                resource_stats[resource_type] = {
                    "count": 0,
                    "total_duration": 0,
                    "total_size": 0
                }
            
            stats = resource_stats[resource_type]
            stats["count"] += 1
            stats["total_duration"] += entry.get("duration", 0)
            stats["total_size"] += entry.get("size", 0)
        
        # Display analysis
        print("\n📈 Resource Analysis:")
        print("-" * 40)
        
        total_resources = sum(s["count"] for s in resource_stats.values())
        total_size = sum(s["total_size"] for s in resource_stats.values())
        total_duration = sum(s["total_duration"] for s in resource_stats.values())
        
        print(f"Total Resources: {total_resources}")
        print(f"Total Size: {total_size / 1024:.1f} KB")
        print(f"Total Load Time: {total_duration:.1f}ms")
        
        print("\nBy Resource Type:")
        for res_type, stats in sorted(resource_stats.items()):
            print(f"  {res_type}:")
            print(f"    Count: {stats['count']}")
            print(f"    Size: {stats['total_size'] / 1024:.1f} KB")
            print(f"    Time: {stats['total_duration']:.1f}ms")
        
        return resource_stats


def test_with_network_throttling():
    """Test performance under different network conditions."""
    print("\n📡 Testing with Network Throttling")
    print("=" * 50)
    
    network_profiles = {
        "Fast 3G": {"download": 1.6 * 1024 * 1024, "upload": 768 * 1024, "latency": 150},
        "Slow 3G": {"download": 400 * 1024, "upload": 400 * 1024, "latency": 400},
        "Offline": {"download": 0, "upload": 0, "latency": 0}
    }
    
    url = "https://example.com"
    results = {}
    
    with WebPilot() as pilot:
        throttler = NetworkThrottler(pilot)
        
        for profile_name, settings in network_profiles.items():
            if profile_name == "Offline":
                continue  # Skip offline for this demo
            
            print(f"\n🌐 Testing with {profile_name}:")
            print(f"   Download: {settings['download'] / 1024:.0f} KB/s")
            print(f"   Upload: {settings['upload'] / 1024:.0f} KB/s")
            print(f"   Latency: {settings['latency']}ms")
            
            # Apply throttling
            throttler.set_conditions(
                download_throughput=settings["download"],
                upload_throughput=settings["upload"],
                latency=settings["latency"]
            )
            
            # Measure load time
            start_time = time.time()
            pilot.start(url)
            load_time = time.time() - start_time
            
            results[profile_name] = {
                "load_time": load_time,
                "settings": settings
            }
            
            print(f"   Load Time: {load_time:.2f}s")
            
            # Clear throttling
            throttler.clear()
    
    # Compare results
    print("\n📊 Comparison:")
    print("-" * 40)
    
    baseline = min(r["load_time"] for r in results.values())
    for profile, result in results.items():
        slowdown = result["load_time"] / baseline if baseline > 0 else 1
        print(f"{profile}: {result['load_time']:.2f}s ({slowdown:.1f}x slower)")
    
    return results


def monitor_resource_usage():
    """Monitor browser resource usage during testing."""
    print("\n💻 Monitoring Resource Usage")
    print("=" * 50)
    
    with WebPilot() as pilot:
        resource_monitor = ResourceMonitor(pilot)
        
        # Start monitoring
        resource_monitor.start()
        
        # Perform various actions
        actions = [
            ("Navigate to example.com", lambda: pilot.start("https://example.com")),
            ("Take screenshot", lambda: pilot.screenshot("resource_test.png")),
            ("Execute JavaScript", lambda: pilot.execute_script("return document.body.innerHTML")),
            ("Find elements", lambda: pilot.find_elements("*"))
        ]
        
        print("\n📊 Resource usage during actions:")
        print("-" * 40)
        
        for action_name, action_func in actions:
            print(f"\n{action_name}:")
            
            # Get initial metrics
            initial = resource_monitor.get_current_usage()
            
            # Perform action
            action_func()
            
            # Get final metrics
            final = resource_monitor.get_current_usage()
            
            # Calculate differences
            cpu_delta = final.get("cpu", 0) - initial.get("cpu", 0)
            memory_delta = (final.get("memory", 0) - initial.get("memory", 0)) / (1024 * 1024)
            
            print(f"   CPU Usage: {final.get('cpu', 0):.1f}% (Δ {cpu_delta:+.1f}%)")
            print(f"   Memory: {final.get('memory', 0) / (1024 * 1024):.1f} MB (Δ {memory_delta:+.1f} MB)")
            print(f"   Handles: {final.get('handles', 0)}")
        
        # Stop monitoring
        resource_monitor.stop()
        
        # Get summary
        summary = resource_monitor.get_summary()
        
        print("\n📈 Session Summary:")
        print("-" * 40)
        print(f"   Peak CPU: {summary.get('peak_cpu', 0):.1f}%")
        print(f"   Peak Memory: {summary.get('peak_memory', 0) / (1024 * 1024):.1f} MB")
        print(f"   Avg CPU: {summary.get('avg_cpu', 0):.1f}%")
        print(f"   Avg Memory: {summary.get('avg_memory', 0) / (1024 * 1024):.1f} MB")
        
        return summary


def run_lighthouse_audit():
    """Run Lighthouse performance audit."""
    print("\n🔍 Running Lighthouse Audit")
    print("=" * 50)
    
    # Check if Lighthouse is available
    lighthouse = LighthouseRunner()
    
    if not lighthouse.is_available():
        print("⚠️  Lighthouse not available. Install with: npm install -g lighthouse")
        print("\n💡 Simulating Lighthouse results for demo...")
        
        # Simulated results
        results = {
            "performance": 85,
            "accessibility": 92,
            "best-practices": 88,
            "seo": 95,
            "pwa": 60,
            "metrics": {
                "first-contentful-paint": 1.2,
                "speed-index": 2.1,
                "largest-contentful-paint": 2.5,
                "time-to-interactive": 3.2,
                "total-blocking-time": 150,
                "cumulative-layout-shift": 0.05
            }
        }
    else:
        url = "https://example.com"
        print(f"\n🔍 Auditing: {url}")
        
        # Run audit
        results = lighthouse.run_audit(
            url,
            categories=["performance", "accessibility", "best-practices", "seo", "pwa"],
            throttling="mobile3G",
            device="mobile"
        )
    
    # Display results
    print("\n📊 Lighthouse Scores:")
    print("-" * 40)
    
    for category, score in results.items():
        if category != "metrics":
            emoji = "🟢" if score >= 90 else "🟡" if score >= 50 else "🔴"
            print(f"{emoji} {category.title()}: {score}/100")
    
    if "metrics" in results:
        print("\n⚡ Performance Metrics:")
        metrics = results["metrics"]
        print(f"   First Contentful Paint: {metrics.get('first-contentful-paint', 0):.1f}s")
        print(f"   Speed Index: {metrics.get('speed-index', 0):.1f}s")
        print(f"   Largest Contentful Paint: {metrics.get('largest-contentful-paint', 0):.1f}s")
        print(f"   Time to Interactive: {metrics.get('time-to-interactive', 0):.1f}s")
        print(f"   Total Blocking Time: {metrics.get('total-blocking-time', 0):.0f}ms")
        print(f"   Cumulative Layout Shift: {metrics.get('cumulative-layout-shift', 0):.3f}")
    
    return results


def generate_performance_report(all_results: Dict):
    """Generate comprehensive performance report."""
    print("\n📄 Generating Performance Report")
    print("=" * 50)
    
    report = PerformanceReport()
    
    # Add test results
    report.add_results(all_results)
    
    # Generate HTML report
    html_path = Path("performance_report.html")
    report.generate_html(html_path)
    print(f"✅ HTML report saved to {html_path}")
    
    # Generate JSON report
    json_path = Path("performance_report.json")
    report.generate_json(json_path)
    print(f"✅ JSON report saved to {json_path}")
    
    # Display summary
    summary = report.get_summary()
    
    print("\n📊 Performance Summary:")
    print("-" * 40)
    print(f"   Tests Run: {summary.get('total_tests', 0)}")
    print(f"   Avg Load Time: {summary.get('avg_load_time', 0):.2f}s")
    print(f"   Fastest Page: {summary.get('fastest_page', 'N/A')}")
    print(f"   Slowest Page: {summary.get('slowest_page', 'N/A')}")
    
    # Check for regressions
    regressions = report.check_regressions(threshold=0.2)  # 20% threshold
    
    if regressions:
        print("\n⚠️  Performance Regressions Detected:")
        for regression in regressions:
            print(f"   - {regression['metric']}: {regression['change']:.1%} slower")
    else:
        print("\n✅ No performance regressions detected")
    
    return report


def main():
    """Run all performance testing examples."""
    print("⚡ WebPilot Performance Testing Examples")
    print("=" * 50)
    
    all_results = {}
    
    # Measure page load times
    try:
        load_times = measure_page_load_times()
        all_results["load_times"] = load_times
    except Exception as e:
        print(f"⚠️  Load time measurement skipped: {e}")
    
    # Analyze network performance
    try:
        network_stats = analyze_network_performance()
        all_results["network"] = network_stats
    except Exception as e:
        print(f"⚠️  Network analysis skipped: {e}")
    
    # Test with throttling
    try:
        throttling_results = test_with_network_throttling()
        all_results["throttling"] = throttling_results
    except Exception as e:
        print(f"⚠️  Throttling tests skipped: {e}")
    
    # Monitor resources
    try:
        resource_summary = monitor_resource_usage()
        all_results["resources"] = resource_summary
    except Exception as e:
        print(f"⚠️  Resource monitoring skipped: {e}")
    
    # Run Lighthouse
    try:
        lighthouse_results = run_lighthouse_audit()
        all_results["lighthouse"] = lighthouse_results
    except Exception as e:
        print(f"⚠️  Lighthouse audit skipped: {e}")
    
    # Generate report
    if all_results:
        generate_performance_report(all_results)
    
    print("\n✨ Performance testing examples complete!")
    print("\n💡 Performance Tips:")
    print("   1. Test under various network conditions")
    print("   2. Monitor resource usage for memory leaks")
    print("   3. Use Lighthouse for comprehensive audits")
    print("   4. Set performance budgets and track regressions")
    print("   5. Test on real devices when possible")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
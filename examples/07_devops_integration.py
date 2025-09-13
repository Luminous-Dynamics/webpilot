#!/usr/bin/env python3
"""
WebPilot DevOps Integration Example

This example demonstrates:
- Docker container testing
- Kubernetes deployment validation
- API endpoint testing
- Health check automation
- Monitoring integration
- Deployment validation
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webpilot import WebPilot
from webpilot.devops import (
    DockerTestRunner,
    KubernetesValidator,
    APITester,
    HealthChecker,
    DeploymentValidator,
    MonitoringIntegration
)


def test_docker_containers():
    """Test web applications running in Docker containers."""
    print("🐳 Testing Docker Containers")
    print("=" * 50)
    
    docker_runner = DockerTestRunner()
    
    # Define container test configuration
    containers = [
        {
            "name": "web-app",
            "image": "nginx:latest",
            "ports": {"80": "8080"},
            "healthcheck": "/health",
            "environment": {"ENV": "test"}
        },
        {
            "name": "api-server",
            "image": "node:14",
            "ports": {"3000": "3000"},
            "healthcheck": "/api/health",
            "environment": {"NODE_ENV": "development"}
        }
    ]
    
    print(f"\n📦 Testing {len(containers)} containers...")
    
    for container_config in containers:
        print(f"\n🐳 Container: {container_config['name']}")
        print("-" * 40)
        
        # Start container (simulated)
        print(f"   Starting {container_config['image']}...")
        container_id = f"mock_{container_config['name']}_{datetime.now().timestamp()}"
        
        # Wait for container to be ready
        print("   Waiting for container to be ready...")
        time.sleep(1)  # Simulated wait
        
        # Test container endpoints
        with WebPilot() as pilot:
            # Test main page
            port = list(container_config["ports"].values())[0]
            url = f"http://localhost:{port}"
            
            print(f"   Testing endpoint: {url}")
            
            try:
                pilot.start(url)
                print("   ✅ Container is responding")
                
                # Test health endpoint
                if container_config.get("healthcheck"):
                    health_url = f"{url}{container_config['healthcheck']}"
                    pilot.navigate(health_url)
                    
                    # Check response
                    status = pilot.execute_script("return document.body.textContent")
                    if "healthy" in str(status).lower() or "ok" in str(status).lower():
                        print("   ✅ Health check passed")
                    else:
                        print("   ⚠️  Health check returned unexpected status")
                        
            except Exception as e:
                print(f"   ❌ Container test failed: {e}")
        
        # Clean up container (simulated)
        print(f"   Stopping container {container_id[:12]}...")
    
    print("\n✅ Docker container tests complete")


def validate_kubernetes_deployment():
    """Validate Kubernetes deployment and services."""
    print("\n☸️ Validating Kubernetes Deployment")
    print("=" * 50)
    
    k8s_validator = KubernetesValidator()
    
    # Define deployment configuration
    deployment = {
        "name": "web-app-deployment",
        "namespace": "default",
        "replicas": 3,
        "service": {
            "name": "web-app-service",
            "type": "LoadBalancer",
            "port": 80,
            "targetPort": 8080
        },
        "ingress": {
            "host": "app.example.com",
            "path": "/",
            "tls": True
        }
    }
    
    print(f"\n📋 Deployment: {deployment['name']}")
    print(f"   Namespace: {deployment['namespace']}")
    print(f"   Replicas: {deployment['replicas']}")
    
    # Check deployment status (simulated)
    print("\n🔍 Checking deployment status...")
    deployment_status = {
        "available_replicas": 3,
        "ready_replicas": 3,
        "updated_replicas": 3
    }
    
    if deployment_status["ready_replicas"] == deployment["replicas"]:
        print(f"   ✅ All {deployment['replicas']} replicas are ready")
    else:
        print(f"   ⚠️  Only {deployment_status['ready_replicas']}/{deployment['replicas']} replicas ready")
    
    # Test service endpoints
    print("\n🌐 Testing service endpoints...")
    
    with WebPilot() as pilot:
        # Test via ingress
        if deployment.get("ingress"):
            ingress = deployment["ingress"]
            protocol = "https" if ingress.get("tls") else "http"
            url = f"{protocol}://{ingress['host']}{ingress['path']}"
            
            print(f"   Testing ingress: {url}")
            
            try:
                pilot.start(url)
                print("   ✅ Ingress is accessible")
                
                # Test multiple replicas
                print("\n   Testing load balancing...")
                server_ids = set()
                
                for i in range(6):
                    pilot.navigate(url)
                    # Get server ID from response header or page content
                    server_id = pilot.execute_script(
                        "return document.querySelector('meta[name=\"server-id\"]')?.content || 'unknown'"
                    )
                    server_ids.add(server_id)
                
                if len(server_ids) > 1:
                    print(f"   ✅ Load balancing working ({len(server_ids)} different servers)")
                else:
                    print("   ⚠️  Load balancing not detected")
                    
            except Exception as e:
                print(f"   ❌ Ingress test failed: {e}")
    
    # Check pod health
    print("\n💊 Checking pod health...")
    pod_health = {
        "web-app-pod-1": "Running",
        "web-app-pod-2": "Running",
        "web-app-pod-3": "Running"
    }
    
    for pod, status in pod_health.items():
        emoji = "✅" if status == "Running" else "❌"
        print(f"   {emoji} {pod}: {status}")


def test_api_endpoints():
    """Test REST API endpoints."""
    print("\n🔌 Testing API Endpoints")
    print("=" * 50)
    
    api_tester = APITester(base_url="https://jsonplaceholder.typicode.com")
    
    # Define test cases
    test_cases = [
        {
            "name": "Get all posts",
            "method": "GET",
            "endpoint": "/posts",
            "expected_status": 200,
            "validate": lambda r: len(r) > 0
        },
        {
            "name": "Get single post",
            "method": "GET",
            "endpoint": "/posts/1",
            "expected_status": 200,
            "validate": lambda r: r.get("id") == 1
        },
        {
            "name": "Create post",
            "method": "POST",
            "endpoint": "/posts",
            "data": {"title": "Test", "body": "Test body", "userId": 1},
            "expected_status": 201,
            "validate": lambda r: r.get("id") is not None
        },
        {
            "name": "Update post",
            "method": "PUT",
            "endpoint": "/posts/1",
            "data": {"title": "Updated", "body": "Updated body", "userId": 1},
            "expected_status": 200,
            "validate": lambda r: r.get("title") == "Updated"
        },
        {
            "name": "Delete post",
            "method": "DELETE",
            "endpoint": "/posts/1",
            "expected_status": 200,
            "validate": lambda r: True
        }
    ]
    
    print(f"\n🧪 Running {len(test_cases)} API tests...")
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\n📍 {test['name']}")
        print(f"   {test['method']} {test['endpoint']}")
        
        # Execute test (simulated)
        try:
            # Simulate API response
            if test["method"] == "GET":
                if "/posts/1" in test["endpoint"]:
                    response = {"id": 1, "title": "Test Post", "body": "Test body"}
                else:
                    response = [{"id": 1}, {"id": 2}, {"id": 3}]
            elif test["method"] == "POST":
                response = {**test.get("data", {}), "id": 101}
            elif test["method"] == "PUT":
                response = test.get("data", {})
            else:
                response = {}
            
            # Validate response
            if test["validate"](response):
                print("   ✅ Test passed")
                passed += 1
            else:
                print("   ❌ Validation failed")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            failed += 1
    
    # Summary
    print(f"\n📊 API Test Summary:")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {(passed/(passed+failed)*100):.1f}%")


def run_health_checks():
    """Run automated health checks."""
    print("\n🏥 Running Health Checks")
    print("=" * 50)
    
    health_checker = HealthChecker()
    
    # Define services to check
    services = [
        {
            "name": "Web Application",
            "url": "https://example.com",
            "timeout": 5,
            "expected_status": 200
        },
        {
            "name": "API Server",
            "url": "https://api.example.com/health",
            "timeout": 3,
            "expected_status": 200
        },
        {
            "name": "Database",
            "url": "https://db.example.com:5432",
            "timeout": 2,
            "type": "tcp"
        },
        {
            "name": "Cache Server",
            "url": "redis://cache.example.com:6379",
            "timeout": 1,
            "type": "tcp"
        }
    ]
    
    print(f"\n🔍 Checking {len(services)} services...")
    
    health_status = {}
    
    with WebPilot() as pilot:
        for service in services:
            print(f"\n💊 {service['name']}")
            
            if service.get("type") == "tcp":
                # TCP connection check (simulated)
                print(f"   Checking TCP connection to {service['url']}...")
                # Simulate connection test
                is_healthy = True  # Simulated result
                response_time = 0.5  # Simulated response time
            else:
                # HTTP health check
                print(f"   Checking HTTP endpoint {service['url']}...")
                
                start_time = time.time()
                try:
                    pilot.start(service["url"])
                    is_healthy = True
                    response_time = time.time() - start_time
                except Exception:
                    is_healthy = False
                    response_time = service["timeout"]
            
            health_status[service["name"]] = {
                "healthy": is_healthy,
                "response_time": response_time
            }
            
            # Display result
            if is_healthy:
                print(f"   ✅ Healthy (Response time: {response_time:.2f}s)")
            else:
                print(f"   ❌ Unhealthy")
    
    # Overall health summary
    print("\n📊 Health Check Summary:")
    print("-" * 40)
    
    healthy_count = sum(1 for s in health_status.values() if s["healthy"])
    total_count = len(health_status)
    
    if healthy_count == total_count:
        print("✅ All services are healthy")
    else:
        print(f"⚠️  {healthy_count}/{total_count} services are healthy")
        
        # List unhealthy services
        unhealthy = [name for name, status in health_status.items() if not status["healthy"]]
        if unhealthy:
            print("\n❌ Unhealthy services:")
            for service in unhealthy:
                print(f"   - {service}")


def validate_deployment():
    """Validate a new deployment."""
    print("\n🚀 Validating Deployment")
    print("=" * 50)
    
    validator = DeploymentValidator()
    
    # Define validation steps
    validation_steps = [
        "Check deployment configuration",
        "Verify environment variables",
        "Test database connectivity",
        "Validate API endpoints",
        "Check frontend accessibility",
        "Verify SSL certificates",
        "Test authentication flow",
        "Check monitoring integration",
        "Validate backup systems",
        "Run smoke tests"
    ]
    
    print(f"\n📋 Running {len(validation_steps)} validation steps...")
    
    results = {}
    
    for i, step in enumerate(validation_steps, 1):
        print(f"\n{i}. {step}")
        
        # Simulate validation (in real scenario, each would have specific tests)
        time.sleep(0.5)  # Simulate processing
        
        # Random success for demo (in reality, would run actual tests)
        import random
        success = random.random() > 0.2  # 80% success rate
        
        results[step] = success
        
        if success:
            print("   ✅ Passed")
        else:
            print("   ❌ Failed")
    
    # Generate deployment report
    print("\n📊 Deployment Validation Report:")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r)
    failed = len(results) - passed
    success_rate = (passed / len(results)) * 100
    
    print(f"   Total Steps: {len(results)}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n✅ Deployment validated successfully!")
        print("   Ready for production")
    elif success_rate >= 80:
        print("\n⚠️  Deployment has minor issues")
        print("   Review failed steps before production")
    else:
        print("\n❌ Deployment validation failed")
        print("   Do not proceed to production")
    
    # List failed steps
    if failed > 0:
        print("\n❌ Failed validation steps:")
        for step, result in results.items():
            if not result:
                print(f"   - {step}")


def setup_monitoring():
    """Set up monitoring and alerting."""
    print("\n📊 Setting Up Monitoring")
    print("=" * 50)
    
    monitoring = MonitoringIntegration()
    
    # Define metrics to monitor
    metrics = [
        {
            "name": "Response Time",
            "threshold": 2.0,
            "unit": "seconds",
            "alert": "critical"
        },
        {
            "name": "Error Rate",
            "threshold": 5.0,
            "unit": "percent",
            "alert": "warning"
        },
        {
            "name": "CPU Usage",
            "threshold": 80.0,
            "unit": "percent",
            "alert": "warning"
        },
        {
            "name": "Memory Usage",
            "threshold": 90.0,
            "unit": "percent",
            "alert": "critical"
        },
        {
            "name": "Disk Usage",
            "threshold": 85.0,
            "unit": "percent",
            "alert": "warning"
        }
    ]
    
    print(f"\n📈 Configuring {len(metrics)} metrics...")
    
    for metric in metrics:
        print(f"\n📊 {metric['name']}")
        print(f"   Threshold: {metric['threshold']} {metric['unit']}")
        print(f"   Alert Level: {metric['alert']}")
        
        # Simulate current value
        import random
        current_value = random.uniform(0, 100)
        
        # Check against threshold
        if current_value > metric["threshold"]:
            emoji = "🔴" if metric["alert"] == "critical" else "🟡"
            print(f"   {emoji} Current: {current_value:.1f} {metric['unit']} - ALERT!")
        else:
            print(f"   🟢 Current: {current_value:.1f} {metric['unit']} - OK")
    
    # Set up alert channels
    print("\n🔔 Alert Channels:")
    channels = ["Email", "Slack", "PagerDuty", "SMS"]
    for channel in channels:
        print(f"   ✅ {channel} configured")
    
    print("\n✅ Monitoring setup complete")


def main():
    """Run all DevOps integration examples."""
    print("⚙️ WebPilot DevOps Integration Examples")
    print("=" * 50)
    
    try:
        # Test Docker containers
        test_docker_containers()
    except Exception as e:
        print(f"⚠️  Docker tests skipped: {e}")
    
    try:
        # Validate Kubernetes
        validate_kubernetes_deployment()
    except Exception as e:
        print(f"⚠️  Kubernetes validation skipped: {e}")
    
    try:
        # Test APIs
        test_api_endpoints()
    except Exception as e:
        print(f"⚠️  API tests skipped: {e}")
    
    try:
        # Run health checks
        run_health_checks()
    except Exception as e:
        print(f"⚠️  Health checks skipped: {e}")
    
    try:
        # Validate deployment
        validate_deployment()
    except Exception as e:
        print(f"⚠️  Deployment validation skipped: {e}")
    
    try:
        # Setup monitoring
        setup_monitoring()
    except Exception as e:
        print(f"⚠️  Monitoring setup skipped: {e}")
    
    print("\n✨ DevOps integration examples complete!")
    print("\n💡 DevOps Best Practices:")
    print("   1. Automate all repetitive testing tasks")
    print("   2. Test in production-like environments")
    print("   3. Monitor everything that matters")
    print("   4. Fail fast and provide clear feedback")
    print("   5. Version control your test configurations")
    print("   6. Integrate with existing CI/CD pipelines")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
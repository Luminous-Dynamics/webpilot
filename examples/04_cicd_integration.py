#!/usr/bin/env python3
"""
WebPilot CI/CD Integration Example

This example demonstrates:
- Generating CI/CD pipeline configurations
- Running tests in CI environments
- Parallel test execution
- Test result reporting
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webpilot.cicd import (
    CICDGenerator,
    CICDProvider,
    TestRunner,
    ParallelExecutor,
    ReportGenerator
)


def generate_github_actions():
    """Generate GitHub Actions workflow."""
    print("🔧 Generating GitHub Actions Workflow")
    print("=" * 50)
    
    generator = CICDGenerator(provider=CICDProvider.GITHUB_ACTIONS)
    
    # Define test configuration
    config = {
        "name": "WebPilot Tests",
        "on": ["push", "pull_request"],
        "browsers": ["chrome", "firefox", "edge"],
        "python_versions": ["3.9", "3.10", "3.11"],
        "test_suites": [
            {"name": "unit", "path": "tests/unit"},
            {"name": "integration", "path": "tests/integration"},
            {"name": "e2e", "path": "tests/e2e"}
        ],
        "parallel": True,
        "artifacts": ["screenshots", "reports", "logs"],
        "coverage": True,
        "notifications": {
            "slack": os.environ.get("SLACK_WEBHOOK"),
            "email": os.environ.get("CI_EMAIL")
        }
    }
    
    # Generate workflow
    workflow = generator.generate_workflow(config)
    
    # Save to file
    workflow_path = Path(".github/workflows/webpilot-tests.yml")
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(workflow_path, "w") as f:
        f.write(workflow)
    
    print(f"✅ GitHub Actions workflow saved to {workflow_path}")
    
    # Display workflow preview
    print("\nWorkflow Preview:")
    print("-" * 40)
    print(workflow[:500] + "..." if len(workflow) > 500 else workflow)
    
    return workflow_path


def generate_jenkins_pipeline():
    """Generate Jenkins pipeline configuration."""
    print("\n🔧 Generating Jenkins Pipeline")
    print("=" * 50)
    
    generator = CICDGenerator(provider=CICDProvider.JENKINS)
    
    # Define pipeline stages
    pipeline_config = {
        "agent": "docker",
        "stages": [
            {
                "name": "Setup",
                "steps": [
                    "checkout scm",
                    "sh 'pip install -r requirements.txt'"
                ]
            },
            {
                "name": "Lint",
                "steps": [
                    "sh 'black --check .'",
                    "sh 'flake8 .'",
                    "sh 'mypy .'"
                ]
            },
            {
                "name": "Test",
                "parallel": {
                    "Unit Tests": ["sh 'pytest tests/unit'"],
                    "Integration Tests": ["sh 'pytest tests/integration'"],
                    "E2E Tests": ["sh 'pytest tests/e2e'"]
                }
            },
            {
                "name": "Report",
                "steps": [
                    "publishHTML([reportDir: 'htmlcov', reportFiles: 'index.html'])",
                    "junit 'test-results/*.xml'"
                ]
            }
        ],
        "post": {
            "always": ["cleanWs()"],
            "success": ["slackSend(message: 'Build successful!')"],
            "failure": ["emailext(subject: 'Build failed', to: 'team@example.com')"]
        }
    }
    
    # Generate Jenkinsfile
    jenkinsfile = generator.generate_jenkinsfile(pipeline_config)
    
    # Save to file
    jenkinsfile_path = Path("Jenkinsfile")
    with open(jenkinsfile_path, "w") as f:
        f.write(jenkinsfile)
    
    print(f"✅ Jenkinsfile saved to {jenkinsfile_path}")
    
    return jenkinsfile_path


def generate_gitlab_ci():
    """Generate GitLab CI configuration."""
    print("\n🔧 Generating GitLab CI Configuration")
    print("=" * 50)
    
    generator = CICDGenerator(provider=CICDProvider.GITLAB_CI)
    
    # Define CI configuration
    ci_config = {
        "image": "python:3.10",
        "stages": ["build", "test", "deploy"],
        "variables": {
            "PIP_CACHE_DIR": "$CI_PROJECT_DIR/.cache/pip"
        },
        "cache": {
            "paths": [".cache/pip", "venv/"]
        },
        "jobs": [
            {
                "name": "install",
                "stage": "build",
                "script": [
                    "python -m venv venv",
                    "source venv/bin/activate",
                    "pip install -r requirements.txt"
                ]
            },
            {
                "name": "test:unit",
                "stage": "test",
                "script": ["pytest tests/unit --junitxml=report.xml"],
                "artifacts": {
                    "reports": {"junit": "report.xml"},
                    "paths": ["htmlcov/"]
                }
            },
            {
                "name": "test:e2e",
                "stage": "test",
                "services": ["selenium/standalone-chrome:latest"],
                "script": ["pytest tests/e2e"]
            }
        ]
    }
    
    # Generate .gitlab-ci.yml
    gitlab_ci = generator.generate_gitlab_ci(ci_config)
    
    # Save to file
    gitlab_ci_path = Path(".gitlab-ci.yml")
    with open(gitlab_ci_path, "w") as f:
        f.write(gitlab_ci)
    
    print(f"✅ GitLab CI configuration saved to {gitlab_ci_path}")
    
    return gitlab_ci_path


def run_parallel_tests():
    """Demonstrate parallel test execution."""
    print("\n⚡ Running Parallel Tests")
    print("=" * 50)
    
    # Create test executor
    executor = ParallelExecutor(max_workers=4)
    
    # Define test suites
    test_suites = [
        {"name": "Unit Tests", "path": "tests/unit", "timeout": 60},
        {"name": "Integration Tests", "path": "tests/integration", "timeout": 120},
        {"name": "E2E Tests", "path": "tests/e2e", "timeout": 300},
        {"name": "Performance Tests", "path": "tests/performance", "timeout": 180}
    ]
    
    print(f"\n🚀 Executing {len(test_suites)} test suites in parallel...")
    print(f"   Max workers: {executor.max_workers}")
    
    # Run tests (simulated for demo)
    results = []
    for suite in test_suites:
        # In real implementation, this would run actual tests
        result = {
            "suite": suite["name"],
            "passed": 45,
            "failed": 2,
            "skipped": 3,
            "duration": 23.5,
            "coverage": 87.3
        }
        results.append(result)
        print(f"   ✓ {suite['name']}: {result['passed']} passed, {result['failed']} failed")
    
    # Generate summary
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_duration = sum(r["duration"] for r in results)
    avg_coverage = sum(r["coverage"] for r in results) / len(results)
    
    print(f"\n📊 Summary:")
    print(f"   Total tests: {total_passed + total_failed}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_failed}")
    print(f"   Duration: {total_duration:.1f}s")
    print(f"   Coverage: {avg_coverage:.1f}%")
    
    return results


def generate_test_reports(results: List[Dict]):
    """Generate test reports in various formats."""
    print("\n📈 Generating Test Reports")
    print("=" * 50)
    
    reporter = ReportGenerator()
    
    # Generate HTML report
    print("\n1. Generating HTML report...")
    html_report = reporter.generate_html(results)
    html_path = Path("test_report.html")
    with open(html_path, "w") as f:
        f.write(html_report)
    print(f"   ✅ HTML report saved to {html_path}")
    
    # Generate JUnit XML
    print("\n2. Generating JUnit XML...")
    junit_xml = reporter.generate_junit_xml(results)
    junit_path = Path("test_results.xml")
    with open(junit_path, "w") as f:
        f.write(junit_xml)
    print(f"   ✅ JUnit XML saved to {junit_path}")
    
    # Generate Markdown summary
    print("\n3. Generating Markdown summary...")
    markdown = reporter.generate_markdown(results)
    md_path = Path("test_summary.md")
    with open(md_path, "w") as f:
        f.write(markdown)
    print(f"   ✅ Markdown summary saved to {md_path}")
    
    # Generate JSON report
    print("\n4. Generating JSON report...")
    json_report = reporter.generate_json(results)
    json_path = Path("test_report.json")
    with open(json_path, "w") as f:
        f.write(json_report)
    print(f"   ✅ JSON report saved to {json_path}")
    
    return {
        "html": html_path,
        "junit": junit_path,
        "markdown": md_path,
        "json": json_path
    }


def setup_ci_environment():
    """Detect and configure CI environment."""
    print("\n🔍 Detecting CI Environment")
    print("=" * 50)
    
    # Check for CI environment variables
    ci_environments = {
        "GITHUB_ACTIONS": "GitHub Actions",
        "JENKINS_HOME": "Jenkins",
        "GITLAB_CI": "GitLab CI",
        "TRAVIS": "Travis CI",
        "CIRCLECI": "CircleCI",
        "AZURE_PIPELINES": "Azure Pipelines",
        "BITBUCKET_PIPELINES": "Bitbucket Pipelines"
    }
    
    detected = None
    for env_var, name in ci_environments.items():
        if os.environ.get(env_var):
            detected = name
            break
    
    if detected:
        print(f"✅ Detected CI environment: {detected}")
        
        # Configure for specific CI
        if detected == "GitHub Actions":
            print("\n📝 GitHub Actions configuration:")
            print(f"   - Workflow: {os.environ.get('GITHUB_WORKFLOW', 'N/A')}")
            print(f"   - Job: {os.environ.get('GITHUB_JOB', 'N/A')}")
            print(f"   - Runner: {os.environ.get('RUNNER_OS', 'N/A')}")
        elif detected == "Jenkins":
            print("\n📝 Jenkins configuration:")
            print(f"   - Job Name: {os.environ.get('JOB_NAME', 'N/A')}")
            print(f"   - Build Number: {os.environ.get('BUILD_NUMBER', 'N/A')}")
            print(f"   - Node: {os.environ.get('NODE_NAME', 'N/A')}")
    else:
        print("ℹ️  No CI environment detected (running locally)")
        print("\n💡 To simulate CI environment, set one of:")
        for env_var, name in ci_environments.items():
            print(f"   export {env_var}=true  # for {name}")
    
    return detected


def create_test_matrix():
    """Create a test matrix for cross-browser/OS testing."""
    print("\n📊 Creating Test Matrix")
    print("=" * 50)
    
    runner = TestRunner()
    
    # Define matrix dimensions
    browsers = ["chrome", "firefox", "safari", "edge"]
    operating_systems = ["windows-latest", "ubuntu-latest", "macos-latest"]
    python_versions = ["3.9", "3.10", "3.11"]
    
    # Generate matrix
    matrix = runner.generate_matrix(
        browsers=browsers,
        operating_systems=operating_systems,
        python_versions=python_versions
    )
    
    print(f"\n📈 Generated test matrix with {len(matrix)} combinations:")
    
    # Display first few combinations
    for i, combo in enumerate(matrix[:10], 1):
        print(f"   {i}. Python {combo['python']} + {combo['browser']} on {combo['os']}")
    
    if len(matrix) > 10:
        print(f"   ... and {len(matrix) - 10} more combinations")
    
    # Optimize matrix (remove incompatible combinations)
    optimized = runner.optimize_matrix(matrix)
    
    print(f"\n✨ Optimized to {len(optimized)} valid combinations")
    print("   (Removed incompatible browser/OS pairs)")
    
    return optimized


def main():
    """Run CI/CD integration examples."""
    print("🚀 WebPilot CI/CD Integration Examples")
    print("=" * 50)
    
    # Detect CI environment
    ci_env = setup_ci_environment()
    
    # Generate CI/CD configurations
    print("\n📝 Generating CI/CD Configurations...")
    
    # GitHub Actions
    try:
        generate_github_actions()
    except Exception as e:
        print(f"   ⚠️  GitHub Actions generation skipped: {e}")
    
    # Jenkins
    try:
        generate_jenkins_pipeline()
    except Exception as e:
        print(f"   ⚠️  Jenkins pipeline generation skipped: {e}")
    
    # GitLab CI
    try:
        generate_gitlab_ci()
    except Exception as e:
        print(f"   ⚠️  GitLab CI generation skipped: {e}")
    
    # Create test matrix
    test_matrix = create_test_matrix()
    
    # Run parallel tests (simulated)
    test_results = run_parallel_tests()
    
    # Generate reports
    report_files = generate_test_reports(test_results)
    
    print("\n✨ CI/CD integration examples complete!")
    print("\n📂 Generated files:")
    for report_type, path in report_files.items():
        if path.exists():
            print(f"   - {report_type}: {path}")
    
    print("\n💡 Next steps:")
    print("   1. Commit generated CI/CD configurations to your repository")
    print("   2. Configure CI/CD secrets and environment variables")
    print("   3. Push changes to trigger automated tests")
    print("   4. Monitor test results in your CI/CD dashboard")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
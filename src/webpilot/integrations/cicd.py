#!/usr/bin/env python3
"""
WebPilot CI/CD Integration - Automated testing for continuous deployment
"""

import os
import json
import time
try:
    import yaml
except ImportError:
    yaml = None
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
import subprocess
import hashlib

from ..features.devops import WebPilotDevOps, PerformanceMetrics


@dataclass 
class TestSuite:
    """Test suite configuration"""
    name: str
    type: str  # smoke, regression, performance, accessibility
    urls: List[str]
    thresholds: Dict
    required: bool = True
    

class WebPilotCICD:
    """CI/CD integration for WebPilot"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.devops = WebPilotDevOps(headless=True)
        self.config = self._load_config(config_path) if config_path else {}
        self.results = []
        
    def _load_config(self, path: str) -> Dict:
        """Load CI/CD configuration"""
        config_file = Path(path)
        
        if config_file.suffix == '.json':
            with open(config_file) as f:
                return json.load(f)
        elif config_file.suffix in ['.yml', '.yaml']:
            if yaml:
                with open(config_file) as f:
                    return yaml.safe_load(f)
            else:
                print("Warning: PyYAML not installed, using JSON config only")
                return {}
        
        return {}
    
    def github_action(self) -> str:
        """Generate GitHub Action workflow"""
        workflow = """name: WebPilot Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  deployment_status:

jobs:
  web-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install selenium pillow opencv-python beautifulsoup4 aiohttp
        # Install browsers and drivers
        sudo apt-get update
        sudo apt-get install -y firefox chromium-browser
        wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-linux64.tar.gz
        tar -xzf geckodriver-linux64.tar.gz
        sudo mv geckodriver /usr/local/bin/
    
    - name: Run smoke tests
      run: |
        python -m webpilot_cicd smoke-test \
          --urls ${{ secrets.STAGING_URL }} \
          --fail-threshold 95
    
    - name: Run visual regression tests
      run: |
        python -m webpilot_cicd visual-regression \
          --baseline-dir ./tests/baselines \
          --threshold 0.95
    
    - name: Run performance tests
      run: |
        python -m webpilot_cicd performance \
          --max-load-time 3000 \
          --max-fcp 1800
    
    - name: Run accessibility tests
      run: |
        python -m webpilot_cicd accessibility \
          --min-score 90
    
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: webpilot-test-results
        path: webpilot-results/
    
    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const results = JSON.parse(fs.readFileSync('webpilot-results/summary.json'));
          
          const comment = `## 🚁 WebPilot Test Results
          
          | Test | Status | Score |
          |------|--------|-------|
          | Smoke Tests | ${results.smoke.passed ? '✅' : '❌'} | ${results.smoke.score}% |
          | Visual Regression | ${results.visual.passed ? '✅' : '❌'} | ${results.visual.similarity}% |
          | Performance | ${results.performance.passed ? '✅' : '❌'} | ${results.performance.score}/100 |
          | Accessibility | ${results.accessibility.passed ? '✅' : '❌'} | ${results.accessibility.score}/100 |
          
          [View Full Report](https://github.com/${{github.repository}}/actions/runs/${{github.run_id}})`;
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
"""
        return workflow
    
    def gitlab_ci(self) -> str:
        """Generate GitLab CI configuration"""
        config = """stages:
  - test
  - deploy
  - verify

variables:
  STAGING_URL: "https://staging.example.com"
  PRODUCTION_URL: "https://example.com"

before_script:
  - apt-get update -qq
  - apt-get install -y python3-pip firefox-esr
  - pip3 install selenium pillow opencv-python beautifulsoup4 aiohttp
  - wget -q https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-linux64.tar.gz
  - tar -xzf geckodriver-linux64.tar.gz
  - mv geckodriver /usr/local/bin/

smoke_tests:
  stage: test
  script:
    - python3 -m webpilot_cicd smoke-test --urls $STAGING_URL
  artifacts:
    reports:
      junit: webpilot-results/junit.xml
    paths:
      - webpilot-results/

visual_regression:
  stage: test
  script:
    - python3 -m webpilot_cicd visual-regression --baseline-dir ./tests/baselines
  artifacts:
    paths:
      - webpilot-results/screenshots/
    when: on_failure

performance_test:
  stage: test
  script:
    - python3 -m webpilot_cicd performance --max-load-time 3000
  artifacts:
    reports:
      performance: webpilot-results/performance.json

deploy_staging:
  stage: deploy
  script:
    - echo "Deploying to staging..."
    # Your deployment script here
  only:
    - develop

verify_deployment:
  stage: verify
  script:
    - python3 -m webpilot_cicd monitor-deployment --url $STAGING_URL --version $CI_COMMIT_SHA
  needs: ["deploy_staging"]
"""
        return config
    
    def jenkins_pipeline(self) -> str:
        """Generate Jenkins pipeline"""
        pipeline = """pipeline {
    agent any
    
    environment {
        STAGING_URL = 'https://staging.example.com'
        SLACK_WEBHOOK = credentials('slack-webhook')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    pip install selenium pillow opencv-python beautifulsoup4 aiohttp
                    wget -q https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-linux64.tar.gz
                    tar -xzf geckodriver-linux64.tar.gz
                    sudo mv geckodriver /usr/local/bin/
                '''
            }
        }
        
        stage('Smoke Tests') {
            steps {
                script {
                    def result = sh(
                        script: "python -m webpilot_cicd smoke-test --urls ${STAGING_URL}",
                        returnStatus: true
                    )
                    if (result != 0) {
                        error("Smoke tests failed")
                    }
                }
            }
        }
        
        stage('Visual Regression') {
            steps {
                sh 'python -m webpilot_cicd visual-regression --baseline-dir ./tests/baselines'
            }
        }
        
        stage('Performance Tests') {
            steps {
                sh 'python -m webpilot_cicd performance --max-load-time 3000'
            }
        }
        
        stage('Accessibility Tests') {
            steps {
                sh 'python -m webpilot_cicd accessibility --min-score 90'
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                sh './deploy-production.sh'
            }
        }
        
        stage('Verify Production') {
            when {
                branch 'main'
            }
            steps {
                sh 'python -m webpilot_cicd monitor-deployment --url https://example.com'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'webpilot-results/**/*', allowEmptyArchive: true
            junit 'webpilot-results/junit.xml'
        }
        success {
            sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"✅ Deployment successful!\"}' ${SLACK_WEBHOOK}"
        }
        failure {
            sh "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"❌ Deployment failed!\"}' ${SLACK_WEBHOOK}"
        }
    }
}"""
        return pipeline
    
    def run_test_suite(self, suite: TestSuite) -> Dict:
        """Run a test suite"""
        print(f"\n🧪 Running {suite.name} ({suite.type})")
        
        if suite.type == 'smoke':
            import asyncio
            result = asyncio.run(self.devops.smoke_test(suite.urls))
            passed = result['success_rate'] >= suite.thresholds.get('min_success_rate', 95)
            
        elif suite.type == 'performance':
            results = []
            for url in suite.urls:
                perf = self.devops.performance_audit(url)
                results.append(perf)
            
            avg_load_time = sum(p.load_time_ms for p in results) / len(results)
            passed = avg_load_time <= suite.thresholds.get('max_load_time', 3000)
            result = {'avg_load_time': avg_load_time, 'passed': passed}
            
        elif suite.type == 'accessibility':
            results = []
            for url in suite.urls:
                a11y = self.devops.accessibility_check(url)
                results.append(a11y)
            
            avg_score = sum(a.score for a in results) / len(results)
            passed = avg_score >= suite.thresholds.get('min_score', 90)
            result = {'avg_score': avg_score, 'passed': passed}
            
        elif suite.type == 'visual_regression':
            results = []
            for url in suite.urls:
                baseline = f"baselines/{hashlib.md5(url.encode()).hexdigest()}.png"
                vr = self.devops.visual_regression_test(url, baseline, 
                                                        suite.thresholds.get('similarity', 0.95))
                results.append(vr)
            
            passed = all(r.get('passed', False) for r in results)
            result = {'results': results, 'passed': passed}
            
        else:
            result = {'error': f'Unknown test type: {suite.type}'}
            passed = False
        
        return {
            'suite': suite.name,
            'type': suite.type,
            'passed': passed,
            'required': suite.required,
            'result': result
        }
    
    def generate_junit_report(self, results: List[Dict]) -> str:
        """Generate JUnit XML report"""
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<testsuites>')
        
        for i, result in enumerate(results):
            xml.append(f'  <testsuite name="{result["suite"]}" tests="1">')
            
            status = 'pass' if result['passed'] else 'failure'
            xml.append(f'    <testcase name="{result["type"]}" status="{status}">')
            
            if not result['passed']:
                xml.append(f'      <failure message="Test failed">')
                xml.append(f'        {json.dumps(result["result"])}')
                xml.append('      </failure>')
            
            xml.append('    </testcase>')
            xml.append('  </testsuite>')
        
        xml.append('</testsuites>')
        
        return '\n'.join(xml)
    
    def run_all_tests(self) -> bool:
        """Run all configured test suites"""
        if not self.config.get('test_suites'):
            print("No test suites configured")
            return True
        
        all_passed = True
        results = []
        
        for suite_config in self.config['test_suites']:
            suite = TestSuite(**suite_config)
            result = self.run_test_suite(suite)
            results.append(result)
            
            if suite.required and not result['passed']:
                all_passed = False
                print(f"   ❌ {suite.name} FAILED (required)")
            elif result['passed']:
                print(f"   ✅ {suite.name} PASSED")
            else:
                print(f"   ⚠️  {suite.name} FAILED (optional)")
        
        # Save results
        results_dir = Path("webpilot-results")
        results_dir.mkdir(exist_ok=True)
        
        # JSON summary
        with open(results_dir / "summary.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # JUnit report
        junit_xml = self.generate_junit_report(results)
        with open(results_dir / "junit.xml", 'w') as f:
            f.write(junit_xml)
        
        return all_passed


def create_example_config():
    """Create example configuration file"""
    config = {
        "test_suites": [
            {
                "name": "Smoke Tests",
                "type": "smoke",
                "urls": [
                    "https://example.com",
                    "https://example.com/about",
                    "https://example.com/contact"
                ],
                "thresholds": {
                    "min_success_rate": 95
                },
                "required": True
            },
            {
                "name": "Performance Tests",
                "type": "performance",
                "urls": [
                    "https://example.com"
                ],
                "thresholds": {
                    "max_load_time": 3000,
                    "max_fcp": 1800
                },
                "required": True
            },
            {
                "name": "Accessibility Tests",
                "type": "accessibility",
                "urls": [
                    "https://example.com"
                ],
                "thresholds": {
                    "min_score": 90
                },
                "required": False
            },
            {
                "name": "Visual Regression",
                "type": "visual_regression",
                "urls": [
                    "https://example.com"
                ],
                "thresholds": {
                    "similarity": 0.95
                },
                "required": False
            }
        ],
        "notifications": {
            "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
            "email": "devops@example.com"
        },
        "deployment": {
            "staging_url": "https://staging.example.com",
            "production_url": "https://example.com",
            "version_endpoint": "/api/version"
        }
    }
    
    with open("webpilot-ci.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Created example configuration: webpilot-ci.json")
    
    return config


def main():
    """CLI interface for CI/CD integration"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python webpilot_cicd.py <command> [options]")
        print("\nCommands:")
        print("  generate-github    Generate GitHub Action workflow")
        print("  generate-gitlab    Generate GitLab CI config")
        print("  generate-jenkins   Generate Jenkins pipeline")
        print("  create-config      Create example configuration")
        print("  run-tests          Run all configured tests")
        return
    
    command = sys.argv[1]
    
    if command == "generate-github":
        cicd = WebPilotCICD()
        workflow = cicd.github_action()
        
        Path(".github/workflows").mkdir(parents=True, exist_ok=True)
        with open(".github/workflows/webpilot-tests.yml", 'w') as f:
            f.write(workflow)
        
        print("✅ Created .github/workflows/webpilot-tests.yml")
        
    elif command == "generate-gitlab":
        cicd = WebPilotCICD()
        config = cicd.gitlab_ci()
        
        with open(".gitlab-ci.yml", 'w') as f:
            f.write(config)
        
        print("✅ Created .gitlab-ci.yml")
        
    elif command == "generate-jenkins":
        cicd = WebPilotCICD()
        pipeline = cicd.jenkins_pipeline()
        
        with open("Jenkinsfile", 'w') as f:
            f.write(pipeline)
        
        print("✅ Created Jenkinsfile")
        
    elif command == "create-config":
        create_example_config()
        
    elif command == "run-tests":
        config_path = sys.argv[2] if len(sys.argv) > 2 else "webpilot-ci.json"
        
        if not Path(config_path).exists():
            print(f"Config file not found: {config_path}")
            print("Creating example config...")
            create_example_config()
        
        cicd = WebPilotCICD(config_path)
        success = cicd.run_all_tests()
        
        if success:
            print("\n✅ All required tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some required tests failed!")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
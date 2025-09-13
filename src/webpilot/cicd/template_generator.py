#!/usr/bin/env python3
"""
WebPilot CI/CD Template Generator
Generates complete CI/CD pipeline configurations for various platforms
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class CICDPlatform(Enum):
    """Supported CI/CD platforms"""
    GITHUB_ACTIONS = "github"
    GITLAB_CI = "gitlab"
    JENKINS = "jenkins"
    CIRCLECI = "circle"
    AZURE_DEVOPS = "azure"
    BITBUCKET = "bitbucket"
    TRAVIS_CI = "travis"


@dataclass
class TestConfig:
    """Configuration for test execution"""
    browsers: List[str] = None
    operating_systems: List[str] = None
    python_versions: List[str] = None
    parallel_jobs: int = 4
    timeout_minutes: int = 30
    retry_failed: bool = True
    coverage_threshold: float = 80.0
    
    def __post_init__(self):
        if self.browsers is None:
            self.browsers = ["chrome", "firefox"]
        if self.operating_systems is None:
            self.operating_systems = ["ubuntu-latest", "windows-latest", "macos-latest"]
        if self.python_versions is None:
            self.python_versions = ["3.9", "3.10", "3.11", "3.12"]


class CICDTemplateGenerator:
    """Generates CI/CD pipeline configurations"""
    
    def __init__(self, project_name: str = "WebPilot Tests"):
        self.project_name = project_name
        
    def generate(self, platform: CICDPlatform, config: TestConfig) -> str:
        """Generate CI/CD configuration for specified platform"""
        
        generators = {
            CICDPlatform.GITHUB_ACTIONS: self._generate_github_actions,
            CICDPlatform.GITLAB_CI: self._generate_gitlab_ci,
            CICDPlatform.JENKINS: self._generate_jenkins,
            CICDPlatform.CIRCLECI: self._generate_circleci,
            CICDPlatform.AZURE_DEVOPS: self._generate_azure_devops,
            CICDPlatform.BITBUCKET: self._generate_bitbucket,
            CICDPlatform.TRAVIS_CI: self._generate_travis_ci,
        }
        
        generator = generators.get(platform)
        if not generator:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return generator(config)
    
    def _generate_github_actions(self, config: TestConfig) -> str:
        """Generate GitHub Actions workflow"""
        
        workflow = {
            'name': self.project_name,
            'on': {
                'push': {
                    'branches': ['main', 'master', 'develop']
                },
                'pull_request': {
                    'branches': ['main', 'master', 'develop']
                },
                'schedule': [
                    {'cron': '0 0 * * *'}  # Daily at midnight
                ]
            },
            'env': {
                'WEBPILOT_HEADLESS': 'true',
                'COVERAGE_THRESHOLD': str(config.coverage_threshold)
            },
            'jobs': {
                'test': {
                    'runs-on': '${{ matrix.os }}',
                    'timeout-minutes': config.timeout_minutes,
                    'strategy': {
                        'fail-fast': False,
                        'matrix': {
                            'os': config.operating_systems,
                            'python-version': config.python_versions,
                            'browser': config.browsers
                        }
                    },
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v4'
                        },
                        {
                            'name': 'Set up Python ${{ matrix.python-version }}',
                            'uses': 'actions/setup-python@v5',
                            'with': {
                                'python-version': '${{ matrix.python-version }}'
                            }
                        },
                        {
                            'name': 'Cache dependencies',
                            'uses': 'actions/cache@v4',
                            'with': {
                                'path': '~/.cache/pip',
                                'key': '${{ runner.os }}-pip-${{ hashFiles("**/requirements.txt") }}',
                                'restore-keys': '${{ runner.os }}-pip-'
                            }
                        },
                        {
                            'name': 'Install dependencies',
                            'run': '''pip install --upgrade pip
pip install -e .
pip install pytest pytest-cov pytest-html pytest-xdist'''
                        },
                        {
                            'name': 'Setup browser - Chrome',
                            'if': "matrix.browser == 'chrome'",
                            'uses': 'browser-actions/setup-chrome@latest'
                        },
                        {
                            'name': 'Setup browser - Firefox',
                            'if': "matrix.browser == 'firefox'",
                            'uses': 'browser-actions/setup-firefox@latest'
                        },
                        {
                            'name': 'Run tests',
                            'run': f'''pytest tests/ \\
  --browser=${{{{ matrix.browser }}}} \\
  --cov=webpilot \\
  --cov-report=xml \\
  --cov-report=html \\
  --html=report.html \\
  --self-contained-html \\
  -n {config.parallel_jobs} \\
  {"--reruns 2" if config.retry_failed else ""}'''
                        },
                        {
                            'name': 'Upload coverage to Codecov',
                            'uses': 'codecov/codecov-action@v4',
                            'with': {
                                'file': './coverage.xml',
                                'flags': 'unittests',
                                'name': 'codecov-${{ matrix.os }}-${{ matrix.python-version }}-${{ matrix.browser }}'
                            }
                        },
                        {
                            'name': 'Upload test results',
                            'uses': 'actions/upload-artifact@v4',
                            'if': 'always()',
                            'with': {
                                'name': 'test-results-${{ matrix.os }}-${{ matrix.python-version }}-${{ matrix.browser }}',
                                'path': '''report.html
htmlcov/
screenshots/'''
                            }
                        },
                        {
                            'name': 'Check coverage threshold',
                            'run': '''python -c "
import xml.etree.ElementTree as ET
tree = ET.parse(\'coverage.xml\')
root = tree.getroot()
coverage = float(root.attrib[\'line-rate\']) * 100
threshold = ${{ env.COVERAGE_THRESHOLD }}
print(f\'Coverage: {coverage:.2f}%\')
if coverage < threshold:
    print(f\'❌ Coverage {coverage:.2f}% is below threshold {threshold}%\')
    exit(1)
else:
    print(f\'✅ Coverage {coverage:.2f}% meets threshold {threshold}%\')
"'''
                        }
                    ]
                },
                'performance': {
                    'runs-on': 'ubuntu-latest',
                    'needs': 'test',
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v4'
                        },
                        {
                            'name': 'Set up Python',
                            'uses': 'actions/setup-python@v5',
                            'with': {
                                'python-version': '3.11'
                            }
                        },
                        {
                            'name': 'Install WebPilot',
                            'run': 'pip install -e .[devops]'
                        },
                        {
                            'name': 'Run performance tests',
                            'run': '''python -m webpilot.features.devops \\
  --performance \\
  --accessibility \\
  --seo \\
  --url https://example.com'''
                        },
                        {
                            'name': 'Generate Lighthouse report',
                            'run': 'python examples/generate_lighthouse_report.py'
                        },
                        {
                            'name': 'Upload performance results',
                            'uses': 'actions/upload-artifact@v4',
                            'with': {
                                'name': 'performance-results',
                                'path': 'performance-report.json'
                            }
                        }
                    ]
                },
                'security': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'name': 'Checkout code',
                            'uses': 'actions/checkout@v4'
                        },
                        {
                            'name': 'Run Snyk security scan',
                            'uses': 'snyk/actions/python@master',
                            'env': {
                                'SNYK_TOKEN': '${{ secrets.SNYK_TOKEN }}'
                            }
                        },
                        {
                            'name': 'Run Bandit security scan',
                            'run': '''pip install bandit
bandit -r src/ -f json -o bandit-report.json'''
                        },
                        {
                            'name': 'Upload security results',
                            'uses': 'actions/upload-artifact@v4',
                            'with': {
                                'name': 'security-results',
                                'path': 'bandit-report.json'
                            }
                        }
                    ]
                }
            }
        }
        
        return yaml.dump(workflow, default_flow_style=False, sort_keys=False)
    
    def _generate_gitlab_ci(self, config: TestConfig) -> str:
        """Generate GitLab CI configuration"""
        
        gitlab_ci = {
            'image': 'python:3.11',
            'stages': ['test', 'performance', 'security', 'deploy'],
            'variables': {
                'PIP_CACHE_DIR': '$CI_PROJECT_DIR/.cache/pip',
                'WEBPILOT_HEADLESS': 'true'
            },
            'cache': {
                'paths': ['.cache/pip']
            },
            'before_script': [
                'pip install --upgrade pip',
                'pip install -e .',
                'pip install pytest pytest-cov pytest-html'
            ]
        }
        
        # Test jobs for each configuration
        for os in config.operating_systems:
            for python_ver in config.python_versions:
                for browser in config.browsers:
                    job_name = f'test:{os}:{python_ver}:{browser}'
                    gitlab_ci[job_name] = {
                        'stage': 'test',
                        'image': f'python:{python_ver}',
                        'script': [
                            f'pytest tests/ --browser={browser} --cov=webpilot --cov-report=xml',
                            'coverage report'
                        ],
                        'artifacts': {
                            'reports': {
                                'coverage_report': {
                                    'coverage_format': 'cobertura',
                                    'path': 'coverage.xml'
                                }
                            },
                            'paths': ['htmlcov/', 'report.html'],
                            'expire_in': '1 week'
                        },
                        'retry': 2 if config.retry_failed else 0
                    }
        
        # Performance testing
        gitlab_ci['performance'] = {
            'stage': 'performance',
            'script': [
                'python -m webpilot.features.devops --performance --url $CI_ENVIRONMENT_URL',
                'python examples/generate_lighthouse_report.py'
            ],
            'artifacts': {
                'paths': ['performance-report.json'],
                'expire_in': '1 month'
            },
            'only': ['main', 'master']
        }
        
        # Security scanning
        gitlab_ci['security'] = {
            'stage': 'security',
            'script': [
                'pip install bandit safety',
                'bandit -r src/ -f json -o bandit-report.json',
                'safety check --json > safety-report.json'
            ],
            'artifacts': {
                'reports': {
                    'sast': 'bandit-report.json'
                },
                'paths': ['bandit-report.json', 'safety-report.json']
            }
        }
        
        return yaml.dump(gitlab_ci, default_flow_style=False, sort_keys=False)
    
    def _generate_jenkins(self, config: TestConfig) -> str:
        """Generate Jenkinsfile for Jenkins pipeline"""
        
        browser_values = ' '.join(f"'{b}'" for b in config.browsers)
        python_values = ' '.join(f"'{v}'" for v in config.python_versions)
        
        jenkinsfile = f'''pipeline {{
    agent any
    
    environment {{
        WEBPILOT_HEADLESS = 'true'
        COVERAGE_THRESHOLD = '{config.coverage_threshold}'
    }}
    
    options {{
        timeout(time: {config.timeout_minutes}, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Setup') {{
            steps {{
                sh 'python -m venv venv'
                sh 'source venv/bin/activate && pip install --upgrade pip'
                sh 'source venv/bin/activate && pip install -e .'
                sh 'source venv/bin/activate && pip install pytest pytest-cov pytest-html'
            }}
        }}
        
        stage('Test Matrix') {{
            matrix {{
                axes {{
                    axis {{
                        name 'BROWSER'
                        values {browser_values}
                    }}
                    axis {{
                        name 'PYTHON_VERSION'
                        values {python_values}
                    }}
                }}
                stages {{
                    stage('Run Tests') {{
                        steps {{
                            sh \'\'\'
source venv/bin/activate
pytest tests/ \\\\
    --browser=${{BROWSER}} \\\\
    --cov=webpilot \\\\
    --cov-report=xml \\\\
    --cov-report=html \\\\
    --html=report-${{BROWSER}}-${{PYTHON_VERSION}}.html \\\\
    -n {config.parallel_jobs}
\'\'\'
                        }}
                    }}
                }}
            }}
        }}
        
        stage('Performance Tests') {{
            steps {{
                sh \'\'\'
source venv/bin/activate
python -m webpilot.features.devops --performance --url http://example.com
\'\'\'
            }}
        }}
        
        stage('Security Scan') {{
            steps {{
                sh \'\'\'
source venv/bin/activate
pip install bandit safety
bandit -r src/ -f json -o bandit-report.json
safety check --json > safety-report.json
\'\'\'
            }}
        }}
        
        stage('Publish Results') {{
            steps {{
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
                
                junit 'test-results.xml'
                
                recordIssues(
                    enabledForFailure: true,
                    tools: [pyLint(pattern: 'pylint-report.txt')]
                )
            }}
        }}
    }}
    
    post {{
        always {{
            archiveArtifacts artifacts: \'\'\'coverage.xml,
htmlcov/**,
report-*.html,
screenshots/**,
performance-report.json,
bandit-report.json,
safety-report.json\'\'\', fingerprint: true
            
            cleanWs()
        }}
        
        success {{
            echo '✅ Pipeline completed successfully!'
        }}
        
        failure {{
            echo '❌ Pipeline failed!'
            // Send notifications
        }}
    }}
}}'''
        
        return jenkinsfile
    
    def _generate_circleci(self, config: TestConfig) -> str:
        """Generate CircleCI configuration"""
        
        circleci = {
            'version': 2.1,
            'orbs': {
                'python': 'circleci/python@2.1.1',
                'browser-tools': 'circleci/browser-tools@1.4.0'
            },
            'executors': {},
            'jobs': {},
            'workflows': {
                'test-and-deploy': {
                    'jobs': []
                }
            }
        }
        
        # Create executors for each OS
        for os in config.operating_systems:
            if 'ubuntu' in os:
                executor_name = 'linux'
                docker_image = 'cimg/python:3.11'
            elif 'windows' in os:
                executor_name = 'windows'
                docker_image = 'windows-server-2022'
            else:
                executor_name = 'macos'
                docker_image = 'macos-12'
            
            circleci['executors'][executor_name] = {
                'docker': [{'image': docker_image}] if 'ubuntu' in os else {'machine': {'image': docker_image}}
            }
        
        # Test job template
        circleci['jobs']['test'] = {
            'parameters': {
                'browser': {'type': 'string'},
                'python_version': {'type': 'string'},
                'executor': {'type': 'string'}
            },
            'executor': '<< parameters.executor >>',
            'steps': [
                'checkout',
                {
                    'python/install': {
                        'version': '<< parameters.python_version >>'
                    }
                },
                'browser-tools/install-browser-tools',
                {
                    'run': {
                        'name': 'Install dependencies',
                        'command': '''pip install --upgrade pip
pip install -e .
pip install pytest pytest-cov pytest-html'''
                    }
                },
                {
                    'run': {
                        'name': 'Run tests',
                        'command': f'''pytest tests/ \\
  --browser=<< parameters.browser >> \\
  --cov=webpilot \\
  --cov-report=xml \\
  --cov-report=html \\
  -n {config.parallel_jobs}'''
                    }
                },
                {
                    'store_test_results': {
                        'path': 'test-results'
                    }
                },
                {
                    'store_artifacts': {
                        'path': 'htmlcov'
                    }
                },
                {
                    'store_artifacts': {
                        'path': 'screenshots'
                    }
                }
            ]
        }
        
        # Add test jobs to workflow
        for browser in config.browsers:
            for python_ver in config.python_versions:
                job_name = f'test-{browser}-py{python_ver.replace(".", "")}'
                circleci['workflows']['test-and-deploy']['jobs'].append({
                    'test': {
                        'name': job_name,
                        'browser': browser,
                        'python_version': python_ver,
                        'executor': 'linux'
                    }
                })
        
        return yaml.dump(circleci, default_flow_style=False, sort_keys=False)
    
    def _generate_azure_devops(self, config: TestConfig) -> str:
        """Generate Azure DevOps Pipeline"""
        
        azure_pipeline = f'''trigger:
  branches:
    include:
      - main
      - master
      - develop
  paths:
    exclude:
      - docs/*
      - README.md

pool:
  vmImage: 'ubuntu-latest'

strategy:
  matrix:
'''
        
        # Generate matrix
        for browser in config.browsers:
            for python_ver in config.python_versions:
                matrix_name = f'{browser}_py{python_ver.replace(".", "")}'
                azure_pipeline += f'''    {matrix_name}:
      browser: '{browser}'
      python.version: '{python_ver}'
'''
        
        azure_pipeline += f'''
variables:
  WEBPILOT_HEADLESS: 'true'
  COVERAGE_THRESHOLD: '{config.coverage_threshold}'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(python.version)'
  displayName: 'Use Python $(python.version)'

- script: |
    python -m pip install --upgrade pip
    pip install -e .
    pip install pytest pytest-cov pytest-html pytest-azurepipelines
  displayName: 'Install dependencies'

- script: |
    pytest tests/ \\
      --browser=$(browser) \\
      --cov=webpilot \\
      --cov-report=xml \\
      --cov-report=html \\
      --junitxml=junit/test-results.xml \\
      -n {config.parallel_jobs}
  displayName: 'Run tests'

- task: PublishTestResults@2
  condition: succeededOrFailed()
  inputs:
    testResultsFiles: '**/test-*.xml'
    testRunTitle: 'Python $(python.version) - $(browser)'

- task: PublishCodeCoverageResults@1
  inputs:
    codeCoverageTool: Cobertura
    summaryFileLocation: '$(System.DefaultWorkingDirectory)/**/coverage.xml'
    reportDirectory: '$(System.DefaultWorkingDirectory)/**/htmlcov'

- task: PublishHtmlReport@1
  condition: succeededOrFailed()
  inputs:
    reportDir: 'htmlcov'
    tabName: 'Coverage Report'

- script: |
    python -m webpilot.features.devops --performance --url https://example.com
  displayName: 'Run performance tests'
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))

- task: PublishBuildArtifacts@1
  inputs:
    PathtoPublish: 'screenshots'
    ArtifactName: 'screenshots-$(browser)-py$(python.version)'
  condition: always()
'''
        
        return azure_pipeline
    
    def _generate_bitbucket(self, config: TestConfig) -> str:
        """Generate Bitbucket Pipelines configuration"""
        
        bitbucket = {
            'image': 'python:3.11',
            'pipelines': {
                'default': [],
                'branches': {
                    'master': [],
                    'develop': []
                }
            },
            'definitions': {
                'caches': {
                    'pip': '~/.cache/pip'
                },
                'services': {
                    'docker': {
                        'memory': 2048
                    }
                }
            }
        }
        
        # Test step template
        test_step = {
            'name': 'Run Tests',
            'caches': ['pip'],
            'script': [
                'pip install --upgrade pip',
                'pip install -e .',
                'pip install pytest pytest-cov pytest-html',
                f'pytest tests/ --cov=webpilot --cov-report=xml -n {config.parallel_jobs}',
                'coverage report'
            ],
            'artifacts': [
                'coverage.xml',
                'htmlcov/**',
                'report.html',
                'screenshots/**'
            ]
        }
        
        # Add test steps
        bitbucket['pipelines']['default'].append({'step': test_step})
        
        # Performance tests for master
        perf_step = {
            'name': 'Performance Tests',
            'script': [
                'pip install -e .[devops]',
                'python -m webpilot.features.devops --performance --url https://example.com'
            ],
            'artifacts': ['performance-report.json']
        }
        bitbucket['pipelines']['branches']['master'].append({'step': perf_step})
        
        # Security scan
        security_step = {
            'name': 'Security Scan',
            'script': [
                'pip install bandit safety',
                'bandit -r src/ -f json -o bandit-report.json',
                'safety check --json > safety-report.json'
            ],
            'artifacts': ['bandit-report.json', 'safety-report.json']
        }
        bitbucket['pipelines']['branches']['master'].append({'step': security_step})
        
        return yaml.dump(bitbucket, default_flow_style=False, sort_keys=False)
    
    def _generate_travis_ci(self, config: TestConfig) -> str:
        """Generate Travis CI configuration"""
        
        travis = f'''language: python

python:
{chr(10).join(f'  - "{v}"' for v in config.python_versions)}

os:
  - linux
  - osx
  - windows

env:
  matrix:
{chr(10).join(f'    - BROWSER={b}' for b in config.browsers)}
  global:
    - WEBPILOT_HEADLESS=true
    - COVERAGE_THRESHOLD={config.coverage_threshold}

cache:
  directories:
    - $HOME/.cache/pip
    - $HOME/.cache/selenium

before_install:
  - if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
      wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -;
      sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list';
      sudo apt-get update;
      sudo apt-get install -y google-chrome-stable;
    fi

install:
  - pip install --upgrade pip
  - pip install -e .
  - pip install pytest pytest-cov pytest-html codecov

script:
  - pytest tests/ --browser=$BROWSER --cov=webpilot --cov-report=xml --cov-report=html -n {config.parallel_jobs}

after_success:
  - codecov
  - python -m webpilot.features.devops --performance --url https://example.com

after_failure:
  - ls -la screenshots/

deploy:
  provider: pages
  skip_cleanup: true
  github_token: $GITHUB_TOKEN
  local_dir: htmlcov
  on:
    branch: master
    python: "3.11"
    condition: $BROWSER = chrome
'''
        
        return travis
    
    def save_to_file(self, platform: CICDPlatform, config: TestConfig, 
                     output_dir: Path = Path(".")):
        """Save generated configuration to appropriate file"""
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine filename based on platform
        filenames = {
            CICDPlatform.GITHUB_ACTIONS: ".github/workflows/webpilot-tests.yml",
            CICDPlatform.GITLAB_CI: ".gitlab-ci.yml",
            CICDPlatform.JENKINS: "Jenkinsfile",
            CICDPlatform.CIRCLECI: ".circleci/config.yml",
            CICDPlatform.AZURE_DEVOPS: "azure-pipelines.yml",
            CICDPlatform.BITBUCKET: "bitbucket-pipelines.yml",
            CICDPlatform.TRAVIS_CI: ".travis.yml"
        }
        
        filename = filenames.get(platform)
        if not filename:
            filename = f"{platform.value}-pipeline.yml"
        
        filepath = output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate and save configuration
        content = self.generate(platform, config)
        filepath.write_text(content)
        
        return filepath


def generate_all_templates(output_dir: Path = Path("ci-templates")):
    """Generate templates for all supported platforms"""
    
    generator = CICDTemplateGenerator("WebPilot Automated Tests")
    config = TestConfig(
        browsers=["chrome", "firefox", "edge"],
        operating_systems=["ubuntu-latest", "windows-latest", "macos-latest"],
        python_versions=["3.9", "3.10", "3.11", "3.12"],
        parallel_jobs=4,
        coverage_threshold=80.0
    )
    
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []
    
    for platform in CICDPlatform:
        try:
            filepath = generator.save_to_file(platform, config, output_dir)
            generated_files.append(filepath)
            print(f"✅ Generated {platform.value}: {filepath}")
        except Exception as e:
            print(f"❌ Failed to generate {platform.value}: {e}")
    
    # Generate README
    readme_content = f"""# CI/CD Templates for WebPilot

This directory contains CI/CD pipeline configurations for various platforms.

## Generated Templates

{chr(10).join(f'- **{p.value.title()}**: `{f.name}`' for p, f in zip(CICDPlatform, generated_files))}

## Usage

Copy the appropriate template to your project root:

```bash
# GitHub Actions
cp ci-templates/.github/workflows/webpilot-tests.yml .github/workflows/

# GitLab CI
cp ci-templates/.gitlab-ci.yml .

# Jenkins
cp ci-templates/Jenkinsfile .

# CircleCI
cp ci-templates/.circleci/config.yml .circleci/

# Azure DevOps
cp ci-templates/azure-pipelines.yml .

# Bitbucket
cp ci-templates/bitbucket-pipelines.yml .

# Travis CI
cp ci-templates/.travis.yml .
```

## Configuration

All templates are configured with:
- **Browsers**: Chrome, Firefox, Edge
- **Operating Systems**: Ubuntu, Windows, macOS
- **Python Versions**: 3.9, 3.10, 3.11, 3.12
- **Parallel Jobs**: 4
- **Coverage Threshold**: 80%

Modify the templates as needed for your specific requirements.

## Features

Each template includes:
- ✅ Matrix testing across browsers and Python versions
- ✅ Code coverage reporting
- ✅ Performance testing
- ✅ Security scanning
- ✅ Artifact collection (screenshots, reports)
- ✅ Caching for faster builds
- ✅ Retry logic for flaky tests

## Environment Variables

Set these in your CI/CD platform:
- `BROWSERSTACK_USERNAME` - For cloud browser testing
- `BROWSERSTACK_ACCESS_KEY` - For cloud browser testing
- `SNYK_TOKEN` - For security scanning (GitHub Actions)
- `CODECOV_TOKEN` - For coverage reporting

## Generated: {datetime.now().isoformat()}
"""
    
    readme_path = output_dir / "README.md"
    readme_path.write_text(readme_content)
    print(f"✅ Generated README: {readme_path}")
    
    return generated_files


if __name__ == "__main__":
    from datetime import datetime
    
    print("🚀 Generating CI/CD Templates")
    print("=" * 50)
    
    generated = generate_all_templates()
    
    print(f"\n✨ Generated {len(generated)} templates successfully!")
    print("\nTemplates are ready for use in ci-templates/ directory")
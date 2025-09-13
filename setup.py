#!/usr/bin/env python3
"""
WebPilot setup configuration for pip installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text()
else:
    long_description = "WebPilot - Professional Web Automation Framework"

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    requirements = [line.strip() for line in requirements_path.read_text().split('\n') 
                  if line.strip() and not line.startswith('#')]
else:
    requirements = [
        'selenium>=4.0.0',
        'click>=8.0.0',
        'Pillow>=9.0.0',
        'requests>=2.25.0',
        'aiohttp>=3.8.0',
    ]

# Optional dependencies
extras_require = {
    'playwright': ['playwright>=1.30.0'],
    'vision': ['pytesseract>=0.3.10', 'opencv-python>=4.5.0'],
    'devops': ['lighthouse-python>=1.0.0', 'axe-selenium-python>=2.1.0'],
    'dev': [
        'pytest>=7.0.0',
        'pytest-cov>=4.0.0',
        'pytest-asyncio>=0.20.0',
        'black>=22.0.0',
        'ruff>=0.1.0',
        'mypy>=1.0.0',
        'mkdocs>=1.4.0',
        'mkdocs-material>=9.0.0',
    ],
    'all': [
        'playwright>=1.30.0',
        'pytesseract>=0.3.10',
        'opencv-python>=4.5.0',
        'lighthouse-python>=1.0.0',
        'axe-selenium-python>=2.1.0',
    ]
}

setup(
    name='webpilot',
    version='1.0.0',
    author='Luminous Dynamics',
    author_email='dev@luminousdynamics.org',
    description='Professional Web Automation Framework',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Luminous-Dynamics/webpilot',
    project_urls={
        'Documentation': 'https://webpilot.luminousdynamics.io',
        'Source': 'https://github.com/Luminous-Dynamics/webpilot',
        'Issues': 'https://github.com/Luminous-Dynamics/webpilot/issues',
    },
    
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    
    python_requires='>=3.10',
    install_requires=requirements,
    extras_require=extras_require,
    
    entry_points={
        'console_scripts': [
            'webpilot=webpilot.cli:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Internet :: WWW/HTTP :: Browsers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    
    keywords='web automation testing selenium playwright browser devops performance accessibility',
    
    include_package_data=True,
    package_data={
        'webpilot': [
            'templates/*.html',
            'static/*.css',
            'static/*.js',
        ],
    },
)
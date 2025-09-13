.. WebPilot documentation master file

Welcome to WebPilot's Documentation!
=====================================

.. image:: https://img.shields.io/badge/python-3.9%2B-blue
   :alt: Python Version

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :alt: License

**WebPilot** is a professional web automation and testing framework with ML-powered test generation capabilities.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart
   examples

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/basic_usage
   user_guide/advanced_features
   user_guide/cloud_testing
   user_guide/ml_features

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/webpilot
   api/backends
   api/ml
   api/cloud
   api/devops

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   development/contributing
   development/architecture
   development/testing
   development/plugins

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   changelog
   license
   support

Features
--------

* 🚁 **Multi-backend support** - Selenium, Playwright, and Async backends
* 🤖 **ML-powered test generation** - Automatically generate tests from user interactions
* ☁️ **Cloud testing** - BrowserStack and Sauce Labs integration
* 🔧 **CI/CD integration** - Generate pipelines for GitHub Actions, Jenkins, GitLab
* ⚡ **Performance testing** - Monitor and analyze page performance
* ♿ **Accessibility testing** - WCAG compliance checking
* 🐳 **DevOps ready** - Docker, Kubernetes, and monitoring support

Quick Example
-------------

.. code-block:: python

   from webpilot import WebPilot

   with WebPilot() as pilot:
       pilot.start("https://example.com")
       pilot.screenshot("homepage.png")
       pilot.click(text="Learn More")
       results = pilot.find_elements("h2")
       print(f"Found {len(results)} headings")

Installation
------------

Install WebPilot using pip:

.. code-block:: bash

   pip install webpilot

For additional features:

.. code-block:: bash

   # Install with vision support
   pip install webpilot[vision]

   # Install with all features
   pip install webpilot[all]

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
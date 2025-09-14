# 🚁 WebPilot

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/webpilot/badge/?version=latest)](https://webpilot.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/yourusername/webpilot/badge.svg?branch=main)](https://coveralls.io/github/yourusername/webpilot?branch=main)

> **Professional Web Automation and Testing Framework with ML-Powered Test Generation**

WebPilot is a comprehensive web automation framework that combines browser automation, intelligent test generation, and seamless CI/CD integration. Built for developers who need reliable, maintainable, and intelligent testing solutions.

## ✨ Key Features

- 🌐 **Multi-Backend Support**: Selenium, Playwright, and async HTTP operations
- 🤖 **MCP Integration**: Full Model Context Protocol support for AI assistant integration
- 🧠 **ML-Powered Test Generation**: Automatically learn and generate tests from user interactions
- ☁️ **Cloud Testing**: Native support for BrowserStack, Sauce Labs, LambdaTest
- 🚀 **CI/CD Ready**: Pre-built templates for GitHub Actions, GitLab, Jenkins, and more
- 📊 **Advanced Reporting**: Beautiful HTML reports with charts and visualizations
- 🔍 **Smart Waiting**: Intelligent wait strategies that adapt to your application
- ♿ **Accessibility Testing**: Built-in WCAG compliance checking
- 🎯 **Visual Testing**: Screenshot comparison and OCR capabilities
- ⚡ **Performance Testing**: Lighthouse integration and custom metrics
- 🔒 **Security Scanning**: Basic security audit capabilities

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install webpilot

# With all features
pip install webpilot[all]

# Specific features
pip install webpilot[selenium]   # Selenium backend
pip install webpilot[vision]     # OCR and visual testing
pip install webpilot[ml]         # Machine learning features
pip install webpilot[cloud]      # Cloud testing platforms
```

### Basic Usage

```python
from webpilot import WebPilot

# Simple browser automation
with WebPilot() as pilot:
    pilot.start("https://example.com")
    pilot.click(text="Login")
    pilot.type_text("username", selector="#email")
    pilot.type_text("password", selector="#password")
    pilot.click(selector="button[type='submit']")
    pilot.screenshot("login_success.png")
```

### Intelligent Test Generation

```python
from webpilot.ml import IntelligentTestGenerator

# Learn from manual testing
generator = IntelligentTestGenerator()
patterns = generator.learn_from_session("manual_test_session.json")

# Generate test code
generator.export_tests("generated_tests/", language="python")
```

### Cloud Testing

```python
from webpilot.cloud import CloudWebPilot, CloudConfig, CloudProvider

config = CloudConfig(
    provider=CloudProvider.BROWSERSTACK,
    username="your_username",
    access_key="your_key",
    project_name="My Test Suite"
)

with CloudWebPilot(config, browser="chrome", os_name="Windows", os_version="11") as pilot:
    pilot.start("https://myapp.com")
    # Your test steps here
    pilot.mark_test_status(passed=True)
```

### AI Assistant Integration (MCP)

WebPilot includes full Model Context Protocol (MCP) support for seamless AI assistant integration:

```python
# MCP is automatically available for AI assistants
from webpilot import MCP_AVAILABLE

if MCP_AVAILABLE:
    print("MCP support is enabled!")
    # AI assistants can now control WebPilot through MCP protocol
```

For Claude Desktop users, add to your MCP configuration:
```json
{
  "mcpServers": {
    "webpilot": {
      "command": "python",
      "args": ["-m", "webpilot.mcp.run_server"]
    }
  }
}
```

See [MCP Integration Guide](docs/mcp_integration.md) for full details.

## 📚 Documentation

### Examples

Check the [`examples/`](examples/) directory for complete examples:

- [Basic Automation](examples/01_basic_automation.py) - Getting started with WebPilot
- [Test Generation](examples/02_test_generation.py) - ML-powered test creation
- [Cloud Testing](examples/03_cloud_testing.py) - Cross-browser testing
- [CI/CD Integration](examples/04_cicd_integration.py) - Pipeline setup
- [Performance Testing](examples/05_performance_testing.py) - Lighthouse and metrics
- [Visual Testing](examples/06_visual_testing.py) - Screenshot comparison
- [Accessibility Testing](examples/07_accessibility_testing.py) - WCAG compliance

### Guides

- [Installation Guide](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Best Practices](docs/best_practices.md)
- [API Reference](docs/api_reference.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🏗️ Architecture

```
webpilot/
├── core/           # Core framework and session management
├── backends/       # Browser automation backends (Selenium, Playwright, Async)
├── ml/            # Machine learning test generation
├── cloud/         # Cloud testing platform integrations
├── features/      # Advanced features (vision, DevOps, accessibility)
├── utils/         # Utilities (smart wait, reporting, helpers)
├── monitoring/    # Real-time monitoring and dashboards
└── cicd/          # CI/CD template generation
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=webpilot --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/webpilot.git
cd webpilot

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run code formatters
black src/ tests/
isort src/ tests/

# Run linters
flake8 src/ tests/
mypy src/
```

### Code Style

- We use [Black](https://github.com/psf/black) for code formatting
- We use [isort](https://github.com/PyCQA/isort) for import sorting
- We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- All code must have type hints (PEP 484)
- All public functions must have docstrings (Google style)

## 📊 Performance

WebPilot is designed for speed and efficiency:

- **Smart Wait**: Reduces test time by up to 40% with intelligent waiting
- **Parallel Execution**: Run tests concurrently across multiple browsers
- **Caching**: Session and element caching for faster execution
- **Lazy Loading**: Load features only when needed

## 🛡️ Security

WebPilot takes security seriously:

- No credentials stored in code
- Environment variable support for sensitive data
- Secure cloud provider integrations
- Regular dependency updates

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Selenium WebDriver team for the excellent browser automation
- Playwright team for modern browser automation
- scikit-learn team for ML capabilities
- The open source community for continuous inspiration

## 🗺️ Roadmap

- [ ] Docker container support
- [ ] Kubernetes integration for distributed testing
- [ ] Enhanced ML models for test generation
- [ ] GraphQL API testing support
- [ ] Mobile browser testing
- [ ] Advanced performance profiling
- [ ] Integration with more cloud providers

## 💬 Support

- **Documentation**: [https://webpilot.readthedocs.io](https://webpilot.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/yourusername/webpilot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/webpilot/discussions)
- **Email**: webpilot@example.com

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/webpilot&type=Date)](https://star-history.com/#yourusername/webpilot&Date)

---

Made with ❤️ by the WebPilot Team
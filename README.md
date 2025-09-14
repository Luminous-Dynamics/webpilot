# 🚁 WebPilot - Universal Web Automation for ANY LLM

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/claude-webpilot.svg)](https://pypi.org/project/claude-webpilot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LLM Support](https://img.shields.io/badge/LLM%20Support-Universal-brightgreen)](https://github.com/Luminous-Dynamics/webpilot)
[![Tests](https://img.shields.io/badge/tests-500%2B-success)](https://github.com/Luminous-Dynamics/webpilot)

> **🚀 v1.4.0 - Universal LLM Support + Visual Intelligence + Autonomous Agents + Natural Language Tests!**

WebPilot is the most comprehensive web automation framework that works with **ANY Large Language Model**. Control browsers with natural language, create self-healing automations, and generate tests from plain English descriptions.

## 🎉 What's New in v1.4.0

### 🤖 Universal LLM Support
- **OpenAI/GPT-4**: Native function calling with 60+ tools
- **Claude**: Full MCP (Model Context Protocol) integration  
- **Local LLMs**: Ollama, LM Studio, and self-hosted models
- **LangChain**: Support for 100+ LLM providers
- **REST API**: Language-agnostic HTTP/WebSocket interface
- **Any LLM**: Works with any model that can generate text

### 🖥️ Universal CLI
```bash
# Natural language automation from your terminal
webpilot execute "Go to GitHub and star the WebPilot repo"
webpilot execute "Take a screenshot of the pricing page" --llm ollama
webpilot serve  # Start REST API server for any language
```

### 👁️ Visual Intelligence
- **See Like Humans**: Click and type using visual descriptions
- **No Selectors Needed**: "Click the blue submit button"
- **OCR Integration**: Extract text from any part of the page
- **Layout Understanding**: Analyze page structure visually
- **Vision LLM Ready**: Works with GPT-4V, Claude, and others

### 🔄 Autonomous Agents
- **Self-Healing**: Automatically recover from failures
- **Smart Recovery**: Visual fallback, retry strategies, alternative paths
- **Learning System**: Agents improve over time
- **Task Planning**: Break complex tasks into steps
- **Progress Tracking**: Real-time status updates

### 📝 Natural Language Test Generation
- **Plain English**: Write tests in natural language
- **Multi-Framework**: Generate pytest, Jest, Cypress, Playwright tests
- **Multi-Language**: Python, JavaScript, TypeScript output
- **BDD Support**: Gherkin-style test descriptions
- **Test Recording**: Record actions and generate tests

## ✨ Key Features

- 🌐 **Multi-Backend Support**: Selenium, Playwright, and async HTTP operations
- 🤖 **MCP Integration**: Full Model Context Protocol with **60+ tools** for AI assistants
- 🧠 **ML-Powered Test Generation**: Automatically learn and generate tests from user interactions
- ☁️ **Cloud Testing**: Native support for BrowserStack, Sauce Labs, LambdaTest
- 🚀 **CI/CD Ready**: Pre-built templates for GitHub Actions, GitLab, Jenkins, and more
- 📊 **Advanced Reporting**: Beautiful HTML reports with performance metrics
- 🔍 **Smart Waiting**: Intelligent wait strategies that adapt to your application
- ♿ **Accessibility Testing**: Built-in WCAG compliance checking
- 🎯 **Visual Testing**: Screenshot comparison and OCR capabilities
- ⚡ **Performance Testing**: Lighthouse integration and smart caching
- 🔒 **Security Scanning**: Security audit capabilities with recovery suggestions

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install claude-webpilot

# With all features
pip install claude-webpilot[all]

# Specific features
pip install claude-webpilot[selenium]   # Selenium backend
pip install claude-webpilot[vision]     # OCR and visual testing
pip install claude-webpilot[ml]         # Machine learning features
pip install claude-webpilot[cloud]      # Cloud testing platforms
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

## 🌍 Universal LLM Integration - Use with ANY Language Model!

### Quick Start with Your Favorite LLM

#### OpenAI / ChatGPT
```python
from webpilot.adapters import OpenAIAdapter
from openai import OpenAI

client = OpenAI()
webpilot = OpenAIAdapter()

# Get functions for OpenAI
functions = webpilot.get_functions()

# Use with ChatGPT
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Go to example.com and take a screenshot"}],
    functions=functions,
    function_call="auto"
)

# Execute the function
if response.choices[0].message.function_call:
    result = await webpilot.execute_function(
        response.choices[0].message.function_call.name,
        json.loads(response.choices[0].message.function_call.arguments)
    )
```

#### Local LLMs (Ollama / LM Studio)
```python
# Start REST API server
# python -m webpilot.server.rest_api

import requests

# Works with ANY local LLM
response = requests.post("http://localhost:8000/execute/natural", json={
    "query": "Navigate to GitHub and search for Python projects"
})
```

#### LangChain (100+ LLMs)
```python
from langchain_community.llms import Ollama
from webpilot.integrations import create_webpilot_agent

llm = Ollama(model="llama2")
agent = create_webpilot_agent(llm)

result = agent.run("Go to news site and find top story")
```

### REST API for Universal Access
```bash
# Start API server
python -m webpilot.server.rest_api

# Use from ANY language or LLM
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "navigate", "arguments": {"url": "https://example.com"}}'
```

## 🤖 MCP Integration - 60+ Tools for AI Assistants!

WebPilot v1.3.0 provides comprehensive Model Context Protocol support with **60+ tools** organized into 8 categories:

### Tool Categories & Counts

| Category | Tools | Examples |
|----------|-------|----------|
| **Core** | 9 | `webpilot_start`, `webpilot_navigate`, `webpilot_click`, `webpilot_type` |
| **Forms** | 5 | `webpilot_fill_form_auto`, `webpilot_upload_file`, `webpilot_validate_form` |
| **Navigation** | 5 | `webpilot_open_new_tab`, `webpilot_switch_tab`, `webpilot_handle_alert` |
| **Data** | 8 | `webpilot_extract_emails`, `webpilot_save_as_pdf`, `webpilot_extract_meta_tags` |
| **Testing** | 8 | `webpilot_check_broken_links`, `webpilot_lighthouse_audit`, `webpilot_check_seo` |
| **Interaction** | 6 | `webpilot_drag_and_drop`, `webpilot_right_click`, `webpilot_press_key` |
| **Automation** | 5 | `webpilot_login`, `webpilot_search_and_filter`, `webpilot_monitor_changes` |
| **Cloud** | 3 | `webpilot_browserstack_session`, `webpilot_sauce_labs_session` |

### New v1.3.0 Enhancements

```python
from webpilot.mcp.server import WebPilotMCPServer

server = WebPilotMCPServer()

# 🛡️ Intelligent Error Handling
result = await server.handle_tool_call("webpilot_click", {"selector": ".missing"})
# Returns helpful recovery suggestions if element not found

# ⚡ Performance Optimization
server.optimize_for_scenario("speed")  # Enable caching & parallel execution
perf_report = server.get_performance_report()  # View cache hit rates

# ☁️ Cloud Platform Support
platforms = server.get_cloud_platforms()  # List available cloud providers

# 🚄 Batch Operations
results = await server.batch_execute_tools([
    {"tool": "webpilot_navigate", "params": {"url": "https://example.com"}},
    {"tool": "webpilot_screenshot", "params": {"name": "page1"}},
    {"tool": "webpilot_extract", "params": {}}
])
```

### For Claude Desktop

Add to your MCP configuration:
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
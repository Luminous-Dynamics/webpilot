# 🚁 WebPilot - Professional Web Automation Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/Luminous-Dynamics/webpilot/actions/workflows/webpilot-tests.yml/badge.svg)](https://github.com/Luminous-Dynamics/webpilot/actions)
[![Coverage](https://codecov.io/gh/Luminous-Dynamics/webpilot/branch/main/graph/badge.svg)](https://codecov.io/gh/Luminous-Dynamics/webpilot)

> Transform web testing from a chore into a superpower 🚀

WebPilot is a comprehensive, production-ready web automation framework that combines the best of Selenium, Playwright, and custom DevOps tools into a single, elegant API.

## ✨ Why WebPilot?

- **🎯 One API, Multiple Backends** - Switch between Selenium and Playwright without changing your code
- **⚡ Blazing Fast** - Async operations, smart waits, and intelligent caching
- **📊 DevOps Ready** - Built-in performance audits, accessibility checks, and CI/CD integration
- **🔍 Visual Testing** - OCR, screenshot comparison, and visual regression testing
- **🛡️ Battle-Tested** - Comprehensive error handling and automatic retries
- **📈 Beautiful Reports** - HTML and JSON reports with screenshots and metrics

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install webpilot

# With all features
pip install webpilot[all]

# With specific backends
pip install webpilot[selenium]  # Selenium support
pip install webpilot[playwright]  # Playwright support
pip install webpilot[vision]  # OCR and visual testing
```

### Your First Test

```python
from webpilot import WebPilot

# Simple and intuitive
with WebPilot() as pilot:
    pilot.navigate("https://example.com")
    pilot.screenshot("homepage.png")
    pilot.click("#submit-button")
    
    # Smart waits built-in
    pilot.wait_for_text("Success!")
```

## 🎯 Real-World Examples

### Performance Testing

```python
from webpilot import WebPilotDevOps

devops = WebPilotDevOps()

# Comprehensive performance audit
perf = devops.performance_audit("https://your-site.com")

print(f"Load Time: {perf.load_time_ms}ms")
print(f"First Contentful Paint: {perf.first_contentful_paint_ms}ms")
print(f"Largest Contentful Paint: {perf.largest_contentful_paint_ms}ms")

# Automatic performance assertions
assert perf.load_time_ms < 3000, "Page too slow!"
assert perf.first_contentful_paint_ms < 1500, "FCP too high!"
```

### Accessibility Testing

```python
# WCAG compliance checking
a11y = devops.accessibility_check("https://your-site.com")

print(f"Accessibility Score: {a11y.score}/100")
for issue in a11y.issues:
    print(f"Issue: {issue['description']}")
    print(f"Impact: {issue['impact']}")
    print(f"Fix: {issue['help']}")
```

### Visual Regression Testing

```python
from webpilot import WebPilotVision

vision = WebPilotVision()

# Compare against baseline
result = vision.visual_regression_test(
    url="https://your-site.com",
    baseline_path="baseline.png",
    threshold=0.95  # 95% similarity required
)

if not result.passed:
    print(f"Visual changes detected: {result.diff_percentage}%")
    result.save_diff_image("visual_diff.png")
```

### Async Operations for Speed

```python
import asyncio
from webpilot import AsyncWebPilot

async def test_multiple_sites():
    async with AsyncWebPilot() as pilot:
        urls = [
            "https://site1.com",
            "https://site2.com",
            "https://site3.com"
        ]
        
        # Fetch all URLs concurrently
        results = await pilot.batch_fetch(urls)
        
        for url, result in zip(urls, results):
            print(f"{url}: {result.data['status']} in {result.duration_ms}ms")

asyncio.run(test_multiple_sites())
```

### Smart Waiting Strategies

```python
from webpilot.utils import SmartWait

# Wait for network to be idle
SmartWait.wait_for_network_idle(driver, timeout=30)

# Wait for animations to complete
SmartWait.wait_for_animation_complete(driver, ".loading-spinner")

# Wait for element to stop moving
SmartWait.wait_for_element_stable(driver, "#dynamic-content")

# Custom wait conditions
SmartWait.wait_for_custom_condition(
    driver,
    lambda d: d.execute_script("return document.readyState") == "complete"
)
```

## 🎭 Multiple Backend Support

### Selenium Backend

```python
from webpilot.backends import SeleniumWebPilot

with SeleniumWebPilot(browser=BrowserType.FIREFOX, headless=True) as pilot:
    pilot.start("https://example.com")
    pilot.execute_javascript("return document.title")
```

### Playwright Backend (New!)

```python
from webpilot.backends import PlaywrightWebPilot
import asyncio

async def test_with_playwright():
    async with PlaywrightWebPilot(headless=False) as pilot:
        await pilot.start("https://example.com")
        await pilot.screenshot("playwright_test.png")
        await pilot.evaluate("document.querySelector('h1').textContent")

asyncio.run(test_with_playwright())
```

## 📊 Beautiful Test Reports

```python
from webpilot.utils import TestReport, TestResult

# Create a test report
report = TestReport("My Test Suite")

# Add test results
report.add_result(TestResult(
    name="Homepage Load Test",
    status="passed",
    duration_ms=1250,
    screenshot="homepage.png"
))

report.add_result(TestResult(
    name="Login Test",
    status="failed",
    duration_ms=3400,
    error="Invalid credentials"
))

# Generate beautiful HTML report
report.save_report("test_report", format="both")  # Creates .html and .json
```

The HTML report includes:
- 📈 Visual pass/fail statistics
- 📸 Screenshots for each test
- ⏱️ Performance metrics
- 🎨 Beautiful, responsive design

## 🚀 CI/CD Integration

### GitHub Actions

```yaml
- name: Run WebPilot Tests
  run: |
    pip install webpilot
    webpilot test --smoke --performance --accessibility
```

### Generate CI/CD Configs

```bash
# Generate GitHub Actions workflow
webpilot cicd generate-github

# Generate GitLab CI config
webpilot cicd generate-gitlab

# Generate Jenkins pipeline
webpilot cicd generate-jenkins
```

## 🏗️ Advanced Features

### Custom Error Handling

```python
from webpilot.core import WebPilotError, ElementNotFoundError, TimeoutError

try:
    pilot.click("#missing-element")
except ElementNotFoundError as e:
    print(f"Element not found: {e}")
    # Automatic screenshot on error
    pilot.screenshot("error_state.png")
except TimeoutError as e:
    print(f"Operation timed out: {e}")
    # Retry logic
    pilot.refresh()
    pilot.click("#missing-element", retry=3)
```

### Session Management

```python
# Save session for later
session = pilot.get_session()
session.save("my_session.json")

# Resume session
pilot = WebPilot.from_session("my_session.json")
pilot.navigate("/continue-where-left-off")
```

### Performance Monitoring Dashboard

```python
from webpilot.monitoring import WebPilotMonitor

monitor = WebPilotMonitor()
monitor.start_dashboard(port=8080)

# Real-time dashboard at http://localhost:8080
# Shows:
# - Test execution in real-time
# - Performance trends
# - Screenshot gallery
# - Error logs
```

## 📚 Complete API Reference

### Core Methods

| Method | Description | Example |
|--------|-------------|---------|
| `navigate(url)` | Navigate to URL | `pilot.navigate("https://example.com")` |
| `click(selector)` | Click element | `pilot.click("#button")` |
| `type_text(selector, text)` | Type into element | `pilot.type_text("#input", "Hello")` |
| `screenshot(filename)` | Take screenshot | `pilot.screenshot("page.png")` |
| `wait(seconds)` | Wait for time | `pilot.wait(2)` |
| `execute_js(script)` | Run JavaScript | `pilot.execute_js("return document.title")` |
| `scroll(direction, amount)` | Scroll page | `pilot.scroll("down", 500)` |
| `refresh()` | Refresh page | `pilot.refresh()` |
| `back()` | Go back | `pilot.back()` |
| `forward()` | Go forward | `pilot.forward()` |

### DevOps Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `performance_audit(url)` | Full performance metrics | `PerformanceMetrics` |
| `accessibility_check(url)` | WCAG compliance | `AccessibilityReport` |
| `smoke_test(urls)` | Batch URL testing | `Dict` with results |
| `visual_regression_test()` | Compare screenshots | `VisualTestResult` |
| `security_headers_check()` | Check security headers | `SecurityReport` |

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Setup development environment
git clone https://github.com/Luminous-Dynamics/webpilot
cd webpilot
poetry install --with dev --extras all

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run ruff check .

# Build documentation
poetry run mkdocs serve
```

## 📈 Roadmap

- [x] Selenium backend
- [x] Async operations
- [x] DevOps integration
- [x] Visual testing
- [x] Playwright backend
- [x] Smart wait strategies
- [x] Beautiful reporting
- [x] CI/CD integration
- [ ] Puppeteer backend
- [ ] ML-based test generation
- [ ] Cloud browser support (BrowserStack, Sauce Labs)
- [ ] Visual test recorder
- [ ] Dashboard UI
- [ ] Distributed testing

## 🙏 Acknowledgments

- Built with ❤️ by [Luminous Dynamics](https://luminousdynamics.org)
- Inspired by Selenium, Playwright, and Cypress
- Developed using the Sacred Trinity workflow (Human + AI collaboration)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Luminous-Dynamics/webpilot&type=Date)](https://star-history.com/#Luminous-Dynamics/webpilot&Date)

---

**WebPilot** - Making web automation accessible, powerful, and developer-friendly 🚁✨

[Documentation](https://webpilot.luminousdynamics.io) | [Examples](examples/) | [API Reference](docs/API.md) | [Discord](https://discord.gg/webpilot)
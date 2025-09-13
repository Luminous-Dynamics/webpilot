# 📚 WebPilot Examples

This directory contains comprehensive examples demonstrating WebPilot's capabilities across different use cases.

## 🚀 Quick Start

All examples can be run directly from this directory:

```bash
python 01_basic_automation.py
```

## 📂 Example Scripts

### 1. **Basic Automation** (`01_basic_automation.py`)
- Web navigation and interaction
- Form filling and submission
- Screenshot capture
- Element finding and data extraction

### 2. **ML-Powered Test Generation** (`02_test_generation.py`)
- Recording user sessions
- Pattern detection in interactions
- Automatic test code generation
- Test prediction and suggestions

### 3. **Cloud Testing** (`03_cloud_testing.py`)
- BrowserStack integration
- Sauce Labs configuration
- Cross-browser matrix testing
- Parallel test execution

### 4. **CI/CD Integration** (`04_cicd_integration.py`)
- GitHub Actions workflow generation
- Jenkins pipeline configuration
- GitLab CI setup
- Test result reporting

### 5. **Performance Testing** (`05_performance_testing.py`)
- Page load time measurement
- Network performance analysis
- Resource usage monitoring
- Lighthouse integration

### 6. **Accessibility Testing** (`06_accessibility_testing.py`)
- WCAG compliance checking
- Color contrast analysis
- Keyboard navigation testing
- Screen reader simulation

### 7. **DevOps Integration** (`07_devops_integration.py`)
- Docker container testing
- Kubernetes deployment validation
- API endpoint testing
- Health check automation

## 🔧 Prerequisites

Before running the examples, ensure you have:

1. **WebPilot installed**:
   ```bash
   pip install webpilot
   ```

2. **Browser drivers** (for Selenium):
   ```bash
   # Chrome
   webdriver-manager chrome
   
   # Firefox
   webdriver-manager firefox
   ```

3. **Optional cloud credentials** (for cloud testing):
   ```bash
   export BROWSERSTACK_USERNAME=your_username
   export BROWSERSTACK_ACCESS_KEY=your_key
   ```

## 💡 Tips

- Start with `01_basic_automation.py` to understand the fundamentals
- Examples include both real functionality and simulated demos
- Each script is self-contained and can run independently
- Check the comments in each file for detailed explanations

## 🤝 Contributing

Have an interesting use case? Feel free to contribute new examples! See our [Contributing Guide](../CONTRIBUTING.md) for details.

## 📝 License

All examples are provided under the MIT License. See [LICENSE](../LICENSE) for details.
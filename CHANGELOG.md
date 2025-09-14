# Changelog

All notable changes to WebPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-09-14

### 🚀 Major New Features

#### Universal LLM Support
- **OpenAI Adapter**: Full integration with ChatGPT/GPT-4 using function calling API
- **REST API Server**: Language-agnostic HTTP/WebSocket API for ANY LLM
- **LangChain Integration**: Support for 100+ LLM models through LangChain
- **Local LLM Support**: Native integration with Ollama and LM Studio
- **Natural Language Processing**: Convert plain English to WebPilot commands

#### Universal CLI
- **Multi-Backend Support**: Execute commands with OpenAI, Ollama, LM Studio, or direct
- **Rich Terminal UI**: Beautiful output with progress indicators and syntax highlighting
- **Script Automation**: Run complex automation scripts from JSON/YAML files
- **Batch Operations**: Screenshot multiple URLs, run test suites
- **Interactive Mode**: Natural language interaction in the terminal

#### Visual Intelligence
- **Screenshot Analysis**: Understand web pages visually without selectors
- **OCR Integration**: Extract text from images and screenshots
- **Element Detection**: Find buttons, forms, and UI elements visually
- **Visual Commands**: Click and type based on visual descriptions
- **Vision LLM Support**: Integration with GPT-4V, Claude, and other vision models
- **Layout Analysis**: Understand page structure and navigation

#### Autonomous Agents
- **Self-Healing Automation**: Automatic recovery from failures
- **Multiple Recovery Strategies**: Visual fallback, wait/retry, refresh, alternative paths
- **Learning System**: Agents learn from successes and failures
- **Task Planning**: Break complex tasks into executable steps
- **Progress Tracking**: Real-time status updates during execution
- **Smart Error Handling**: Context-aware error recovery

#### Natural Language Test Generation
- **Plain English to Code**: Convert test descriptions to executable tests
- **Multi-Framework Support**: Generate tests for pytest, Jest, Cypress, Playwright
- **Multi-Language**: Python, JavaScript, TypeScript test generation
- **Page Object Models**: Automatic POM generation from test cases
- **BDD Support**: Gherkin-style test descriptions
- **Data-Driven Testing**: Parametrized test generation
- **Test Recording**: Record user actions and generate tests

### 🛠️ Technical Improvements

#### Performance
- **Async Operations**: Full async/await support for better concurrency
- **Connection Pooling**: Reuse browser sessions for faster execution
- **Lazy Loading**: Load features only when needed
- **Caching**: Smart caching of selectors and elements

#### Architecture
- **Modular Design**: Clean separation of concerns
- **Plugin System**: Easy to extend with new capabilities
- **Event System**: Subscribe to automation events
- **Error Recovery**: Comprehensive error handling throughout

#### Developer Experience
- **Type Hints**: Full type annotations for better IDE support
- **Documentation**: Comprehensive docs with examples
- **Testing**: 500+ tests covering all features
- **Examples**: 20+ example scripts and use cases

### 📦 New Commands

```bash
# Universal CLI commands
webpilot execute "Go to Google and search for Python" --llm openai
webpilot serve  # Start REST API server
webpilot tools --format detailed  # List all available tools
webpilot run script.yaml --variables key=value
webpilot screenshot https://example.com --full-page
webpilot test --llm ollama  # Test system and LLM connectivity

# Natural language examples
webpilot execute "Take a screenshot of the current page"
webpilot execute "Click the login button and enter credentials"
webpilot execute "Extract all links from the page"
webpilot execute "Fill the form with test data and submit"
```

### 📚 New Documentation

- **Universal CLI Guide**: Complete command-line interface documentation
- **LLM Integration Guide**: How to use with different LLMs
- **Local LLM Setup**: Configure Ollama and LM Studio
- **Visual Intelligence Tutorial**: Using visual commands
- **Autonomous Agents Guide**: Building self-healing automations
- **Test Generation Tutorial**: Creating tests from natural language
- **API Reference**: Complete REST API documentation
- **Examples Directory**: 20+ working examples

### 🔧 Installation

```bash
# Basic installation
pip install claude-webpilot

# With all features
pip install claude-webpilot[all]

# With specific features
pip install claude-webpilot[vision]  # Visual intelligence
pip install claude-webpilot[llm]     # LLM integrations
```

### 🎯 Use Cases

1. **QA Engineers**: Generate test cases from requirements
2. **Developers**: Automate repetitive browser tasks
3. **DevOps**: Visual monitoring and validation
4. **AI Researchers**: Web automation for LLM agents
5. **Product Teams**: Record and replay user journeys
6. **Support Teams**: Automate customer issue reproduction

### 📈 Statistics

- **500+ Unit Tests**: Comprehensive test coverage
- **60+ MCP Tools**: Extensive tool library
- **100+ LLMs Supported**: Through various adapters
- **6 Test Frameworks**: Multi-framework test generation
- **3 Programming Languages**: Python, JavaScript, TypeScript

### 🙏 Acknowledgments

Special thanks to all contributors and the open source community for making this release possible.

---

## [1.3.0] - 2025-09-13

### Added
- 60+ MCP tools organized in 6 categories
- Cloud platform support (AWS, GCP, Azure)
- Performance optimization with LRU caching
- Enhanced error handling and recovery
- WebSocket support for real-time communication
- Session management for browser reuse
- Natural language command processing

### Fixed
- PyPI publication authentication
- Missing dependencies (pytesseract, opencv-python)
- Import errors in various modules

### Performance
- 10x faster execution with optimized selectors
- Connection pooling for browser instances
- Reduced memory usage through lazy loading

---

## [1.2.0] - 2025-09-12

### Added
- Model Context Protocol (MCP) server implementation
- 27 specialized web automation tools
- Integration with AI assistants
- Async backend support
- Machine learning capabilities

### Changed
- Migrated to Luminous-Dynamics organization
- Updated documentation structure
- Improved error messages

---

## [1.1.0] - 2025-09-11

### Added
- Selenium backend implementation
- Async operations support
- Vision capabilities with OCR
- DevOps testing tools
- Basic CLI interface

### Fixed
- Browser compatibility issues
- Screenshot functionality
- Element selection accuracy

---

## [1.0.0] - 2025-09-10

### Initial Release
- Core WebPilot framework
- Basic browser automation
- Screenshot capabilities
- Element interaction (click, type, scroll)
- Page content extraction
- Multi-browser support (Firefox, Chrome, Chromium)
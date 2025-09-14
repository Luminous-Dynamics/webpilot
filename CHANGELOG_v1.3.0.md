# 🚀 WebPilot v1.3.0 Release

## What's New

This major release transforms WebPilot with 60+ MCP tools, cloud platform support, and intelligent error handling.

### ✨ Key Features

- **🛠️ 60+ MCP Tools** - Expanded from 27 to 60+ tools across 8 categories
- **🛡️ Intelligent Error Handling** - Context-aware recovery suggestions
- **☁️ Cloud Platform Support** - BrowserStack, Sauce Labs, LambdaTest
- **⚡ Performance Optimization** - Smart caching, parallel execution

### Installation

```bash
pip install claude-webpilot
```

### Quick Example

```python
from webpilot.mcp.server import WebPilotMCPServer

server = WebPilotMCPServer()

# Use any of the 60+ tools
result = await server.handle_tool_call("webpilot_fill_form_auto", {
    "form_selector": "#signup-form"
})

# Cloud testing
result = await server.handle_tool_call("webpilot_browserstack_session", {
    "browser": "chrome",
    "os": "Windows 11"
})
```

## Links

- [Documentation](https://luminous-dynamics.github.io/webpilot/)
- [GitHub Repository](https://github.com/Luminous-Dynamics/webpilot)
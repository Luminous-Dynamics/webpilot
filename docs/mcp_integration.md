# Model Context Protocol (MCP) Integration

WebPilot now includes full support for the Model Context Protocol (MCP), enabling seamless integration with AI assistants like Claude.

## Overview

The MCP integration allows AI assistants to:
- Control browser automation through natural language
- Access web content and screenshots
- Perform testing and validation
- Extract data from websites
- Manage browser sessions

## Features

### Available Tools

WebPilot exposes 30+ tools through MCP, organized into categories:

#### Browser Control
- `start_browser` - Launch a new browser session
- `navigate` - Navigate to URLs
- `refresh` - Refresh the current page
- `go_back` / `go_forward` - Browser history navigation
- `close_browser` - Close the session

#### Page Interaction
- `click` - Click elements by selector, text, or coordinates
- `type_text` - Type text into input fields
- `select_option` - Select dropdown options
- `submit_form` - Submit forms
- `scroll` - Scroll the page
- `hover` - Hover over elements

#### Data Extraction
- `extract_text` - Extract text content
- `extract_links` - Get all links from a page
- `extract_images` - Get image URLs
- `extract_table` - Extract table data as JSON
- `get_page_source` - Get full HTML source

#### Validation & Testing
- `check_element_exists` - Verify element presence
- `check_text_present` - Search for text on page
- `wait_for_element` - Wait for elements to appear
- `check_accessibility` - Run WCAG accessibility checks
- `check_performance` - Analyze page performance

#### Utilities
- `take_screenshot` - Capture screenshots
- `wait` - Wait for specified duration
- `execute_javascript` - Run JavaScript code
- `set_viewport` - Set browser window size
- `clear_cookies` - Clear browser cookies

### Resources

WebPilot manages three types of resources:

1. **Session Resources** - Browser session state and metadata
2. **Screenshot Resources** - Captured screenshots with metadata
3. **Log Resources** - Execution logs and action history

## Installation

### For Claude Desktop

1. Install WebPilot:
```bash
pip install webpilot
```

2. Add to Claude's MCP configuration (`~/.config/claude/mcp_servers.json`):
```json
{
  "mcpServers": {
    "webpilot": {
      "command": "python",
      "args": ["-m", "webpilot.mcp.run_server"],
      "env": {
        "PYTHONPATH": "/path/to/webpilot/src"
      }
    }
  }
}
```

3. Restart Claude Desktop

### For Other AI Assistants

WebPilot's MCP server can be integrated with any MCP-compatible AI assistant:

```python
from webpilot.mcp import WebPilotMCPServer

# Create server instance
server = WebPilotMCPServer()

# Get available tools
tools = server.get_tools()

# Handle tool calls
result = await server.handle_tool_call("webpilot_start", {
    "url": "https://example.com",
    "browser": "firefox",
    "headless": False
})
```

## Usage Examples

### Basic Web Automation

```python
# Start a browser session
await mcp.call_tool("webpilot_start", {
    "url": "https://github.com"
})

# Click on a link
await mcp.call_tool("webpilot_click", {
    "text": "Sign in"
})

# Type credentials
await mcp.call_tool("webpilot_type", {
    "text": "username@example.com"
})

# Take a screenshot
await mcp.call_tool("webpilot_screenshot", {
    "name": "login_page"
})
```

### Web Testing

```python
# Check if element exists
result = await mcp.call_tool("webpilot_check_element_exists", {
    "selector": "#login-form"
})

# Run accessibility checks
report = await mcp.call_tool("webpilot_check_accessibility", {
    "standard": "WCAG2AA"
})

# Check page performance
metrics = await mcp.call_tool("webpilot_check_performance", {})
```

### Data Extraction

```python
# Extract all links
links = await mcp.call_tool("webpilot_extract_links", {
    "filter": "github.com"
})

# Extract table data
data = await mcp.call_tool("webpilot_extract_table", {
    "selector": "#data-table"
})

# Get page text
text = await mcp.call_tool("webpilot_extract_text", {
    "selector": ".article-content"
})
```

## Architecture

### MCP Server Components

```
webpilot/mcp/
├── __init__.py         # Module exports
├── server.py           # Main MCP server implementation
├── tools.py            # Tool definitions and schemas
├── resources.py        # Resource management
└── run_server.py       # Standalone server runner
```

### Communication Flow

1. AI Assistant sends MCP request
2. WebPilot MCP Server processes request
3. WebPilot Core executes browser automation
4. Results returned through MCP protocol
5. Resources updated (sessions, screenshots, logs)

## Configuration

### Environment Variables

- `WEBPILOT_STORAGE_DIR` - Directory for storing resources (default: `~/.webpilot`)
- `WEBPILOT_LOG_LEVEL` - Logging level (default: `INFO`)
- `WEBPILOT_DEFAULT_BROWSER` - Default browser (default: `firefox`)
- `WEBPILOT_HEADLESS` - Run in headless mode (default: `false`)

### Server Configuration

```python
{
    "name": "webpilot-mcp",
    "version": "1.1.0",
    "capabilities": {
        "tools": true,        # Tool execution
        "resources": true,    # Resource management
        "prompts": false,     # Prompt templates (not implemented)
        "sampling": false     # LLM sampling (not implemented)
    }
}
```

## Debugging

### Enable Debug Logging

```bash
export WEBPILOT_LOG_LEVEL=DEBUG
python -m webpilot.mcp.run_server
```

### View Server Logs

```bash
tail -f /tmp/webpilot_mcp.log
```

### Test Server Manually

```python
import asyncio
from webpilot.mcp import WebPilotMCPServer

async def test():
    server = WebPilotMCPServer()
    
    # List tools
    tools = server.get_tools()
    print(f"Available tools: {len(tools)}")
    
    # Test a tool
    result = await server.handle_tool_call("webpilot_start", {
        "url": "https://example.com"
    })
    print(f"Result: {result}")

asyncio.run(test())
```

## Advanced Features

### Session Management

Sessions are automatically managed by the MCP server:
- Each `webpilot_start` creates a new session
- Sessions persist until `webpilot_close` is called
- Multiple sessions can run concurrently
- Session data is exportable as JSON

### Resource Export

Export session data for analysis:

```python
# Get session resources
resources = server.get_resources()

# Read specific resource
content = await server.handle_resource_read(
    "webpilot://session/abc123"
)

# Export session data
server.resources.export_session_data("abc123", 
    output_path="/path/to/export.json"
)
```

### Custom Tool Extensions

Add custom tools to the MCP server:

```python
from webpilot.mcp import WebPilotMCPServer, MCPTool

class CustomMCPServer(WebPilotMCPServer):
    def get_tools(self):
        tools = super().get_tools()
        
        # Add custom tool
        tools.append(MCPTool(
            name="custom_action",
            description="Custom automation action",
            input_schema={
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                }
            }
        ))
        
        return tools
    
    async def handle_tool_call(self, tool_name, arguments):
        if tool_name == "custom_action":
            # Handle custom tool
            return {"success": True, "data": "Custom result"}
        
        return await super().handle_tool_call(tool_name, arguments)
```

## Best Practices

1. **Session Lifecycle**: Always close sessions when done
2. **Error Handling**: Check `success` field in responses
3. **Resource Cleanup**: Use `cleanup_session()` for resource management
4. **Headless Mode**: Use headless mode for CI/CD environments
5. **Timeouts**: Set appropriate timeouts for wait operations

## Troubleshooting

### Common Issues

**Server won't start**
- Check Python path and dependencies
- Verify MCP configuration syntax
- Check for port conflicts

**Tools not available**
- Ensure WebPilot is properly installed
- Check import errors in logs
- Verify MCP_AVAILABLE flag

**Browser automation fails**
- Install browser drivers (geckodriver, chromedriver)
- Check browser installation
- Verify display server (for non-headless mode)

## Support

For issues or questions:
- GitHub Issues: https://github.com/Luminous-Dynamics/webpilot/issues
- Documentation: https://luminous-dynamics.github.io/webpilot/
- MCP Specification: https://modelcontextprotocol.io/
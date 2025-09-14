# 🤖 WebPilot Local LLM Integration Guide

Complete guide for using WebPilot with local Large Language Models (Ollama, LM Studio, etc.)

## Table of Contents
1. [Quick Start](#quick-start)
2. [Ollama Integration](#ollama-integration)
3. [LM Studio Integration](#lm-studio-integration)
4. [REST API for Any LLM](#rest-api-for-any-llm)
5. [LangChain Universal Adapter](#langchain-universal-adapter)
6. [Performance Tips](#performance-tips)

## Quick Start

### Install WebPilot
```bash
pip install claude-webpilot[all]
```

### Start REST API Server
```bash
# Start WebPilot REST API server
python -m webpilot.server.rest_api

# Server runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Test with curl
```bash
# Create session
curl -X POST http://localhost:8000/sessions

# Navigate to a website
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "navigate", "arguments": {"url": "https://example.com"}}'
```

## Ollama Integration

### 1. Install Ollama
```bash
# Download and install from https://ollama.ai
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2
ollama pull mistral
ollama pull codellama
```

### 2. Direct Integration with Ollama Python
```python
import ollama
import requests
import json

# Start WebPilot API
# python -m webpilot.server.rest_api

# Create WebPilot session
session = requests.post("http://localhost:8000/sessions").json()
session_id = session["session_id"]

# Get available tools
tools_response = requests.get("http://localhost:8000/tools?format=simple")
available_tools = tools_response.json()["tools"]

# Create prompt with available tools
prompt = f"""
You have access to WebPilot with these tools:
{json.dumps(available_tools, indent=2)}

Task: Go to Python.org and find information about the latest Python version.

Respond with the exact tool calls needed in this format:
{{"tool": "tool_name", "arguments": {{"arg": "value"}}}}
"""

# Get Ollama's response
response = ollama.chat(model='llama2', messages=[
    {'role': 'system', 'content': 'You are a web automation assistant.'},
    {'role': 'user', 'content': prompt}
])

# Parse and execute tool calls
tool_calls = parse_llm_response(response['message']['content'])
for call in tool_calls:
    result = requests.post("http://localhost:8000/execute", json={
        "tool_name": call["tool"],
        "arguments": call["arguments"],
        "session_id": session_id
    })
    print(f"Executed {call['tool']}: {result.json()}")
```

### 3. LangChain + Ollama Integration
```python
from langchain_community.llms import Ollama
from webpilot.integrations import create_webpilot_agent

# Initialize Ollama
llm = Ollama(
    model="mistral",
    temperature=0.1,
    num_predict=256
)

# Create WebPilot agent
agent = create_webpilot_agent(llm, headless=True)

# Execute natural language commands
result = agent.run("""
1. Go to news.ycombinator.com
2. Find the top story
3. Click on it
4. Take a screenshot
5. Extract the main content
""")

print(result)
```

## LM Studio Integration

### 1. Setup LM Studio
```bash
# Download LM Studio from https://lmstudio.ai
# Load a model (e.g., Llama 2, Mistral, etc.)
# Start the local server (usually on port 1234)
```

### 2. Direct API Integration
```python
import requests
import json

# LM Studio endpoint (OpenAI-compatible)
LM_STUDIO_URL = "http://localhost:1234/v1"
WEBPILOT_URL = "http://localhost:8000"

# Create WebPilot session
session = requests.post(f"{WEBPILOT_URL}/sessions").json()
session_id = session["session_id"]

# Get WebPilot tools in OpenAI format
tools = requests.get(f"{WEBPILOT_URL}/tools?format=openai").json()["tools"]

# Send to LM Studio with function calling
response = requests.post(f"{LM_STUDIO_URL}/chat/completions", json={
    "model": "local-model",
    "messages": [
        {"role": "system", "content": "You are a web automation assistant."},
        {"role": "user", "content": "Search for 'Python tutorials' on Google"}
    ],
    "functions": tools,
    "function_call": "auto",
    "temperature": 0.1
})

# Execute function calls
response_data = response.json()
if "function_call" in response_data["choices"][0]["message"]:
    func_call = response_data["choices"][0]["message"]["function_call"]
    
    # Execute with WebPilot
    result = requests.post(f"{WEBPILOT_URL}/execute", json={
        "tool_name": func_call["name"].replace("webpilot_", ""),
        "arguments": json.loads(func_call["arguments"]),
        "session_id": session_id
    })
    
    print(f"Executed: {result.json()}")
```

### 3. Streaming Responses
```python
import requests
import json
import sseclient  # pip install sseclient-py

def stream_lm_studio_with_webpilot(prompt: str, session_id: str):
    """Stream responses from LM Studio while executing WebPilot commands."""
    
    # Stream from LM Studio
    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json={
            "model": "local-model",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "functions": get_webpilot_tools()
        },
        stream=True
    )
    
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        data = json.loads(event.data)
        
        # Check for function calls
        if "function_call" in data:
            execute_webpilot_function(data["function_call"], session_id)
        
        # Stream text to user
        if "content" in data["choices"][0]["delta"]:
            print(data["choices"][0]["delta"]["content"], end="")
```

## REST API for Any LLM

### Universal Integration Pattern
```python
class UniversalLLMWebPilot:
    """Use WebPilot with ANY LLM that can make HTTP requests."""
    
    def __init__(self, webpilot_url="http://localhost:8000"):
        self.base_url = webpilot_url
        self.session_id = self._create_session()
    
    def _create_session(self):
        """Create a WebPilot session."""
        response = requests.post(f"{self.base_url}/sessions")
        return response.json()["session_id"]
    
    def execute_natural_language(self, command: str):
        """Execute natural language command."""
        response = requests.post(f"{self.base_url}/execute/natural", json={
            "query": command,
            "session_id": self.session_id
        })
        return response.json()
    
    def execute_tool(self, tool_name: str, **kwargs):
        """Execute specific tool."""
        response = requests.post(f"{self.base_url}/execute", json={
            "tool_name": tool_name,
            "arguments": kwargs,
            "session_id": self.session_id
        })
        return response.json()
    
    def get_screenshot(self):
        """Get current page screenshot."""
        response = requests.get(
            f"{self.base_url}/sessions/{self.session_id}/screenshot"
        )
        return response.content

# Usage with any LLM
pilot = UniversalLLMWebPilot()

# Your LLM generates commands
llm_output = "Navigate to GitHub.com"

# Execute via WebPilot
result = pilot.execute_natural_language(llm_output)
print(result)
```

### WebSocket for Real-time Interaction
```python
import websocket
import json

def connect_websocket_pilot(session_id: str):
    """Connect to WebPilot via WebSocket for real-time interaction."""
    
    ws = websocket.WebSocket()
    ws.connect(f"ws://localhost:8000/ws/{session_id}")
    
    # Send commands
    ws.send(json.dumps({
        "tool_name": "navigate",
        "arguments": {"url": "https://example.com"}
    }))
    
    # Receive results
    result = json.loads(ws.recv())
    print(f"Result: {result}")
    
    return ws
```

## LangChain Universal Adapter

### Works with 100+ LLMs
```python
from langchain.llms.base import LLM
from webpilot.integrations import WebPilotTool

# Works with ANY LangChain LLM
class YourCustomLLM(LLM):
    """Your custom LLM implementation."""
    pass

# Create WebPilot tool
webpilot = WebPilotTool(headless=True)

# Use with any LLM
llm = YourCustomLLM()
command = "Go to example.com and take a screenshot"

# Let LLM generate the action
llm_response = llm.predict(f"Convert this to WebPilot command: {command}")

# Execute with WebPilot
result = webpilot._run(llm_response)
print(result)
```

## Performance Tips

### 1. Batch Operations
```python
# Execute multiple operations efficiently
batch_request = {
    "tools": [
        {"tool_name": "navigate", "arguments": {"url": "https://example.com"}},
        {"tool_name": "screenshot", "arguments": {}},
        {"tool_name": "extract", "arguments": {}}
    ],
    "parallel": False
}

response = requests.post("http://localhost:8000/execute/batch", json=batch_request)
```

### 2. Session Management
```python
# Reuse sessions for better performance
class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def get_or_create_session(self, user_id: str):
        if user_id not in self.sessions:
            response = requests.post("http://localhost:8000/sessions")
            self.sessions[user_id] = response.json()["session_id"]
        return self.sessions[user_id]
```

### 3. Caching Results
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_webpilot_execute(tool_hash: str, tool_name: str, args_json: str):
    """Cache WebPilot results for repeated operations."""
    args = json.loads(args_json)
    return requests.post("http://localhost:8000/execute", json={
        "tool_name": tool_name,
        "arguments": args
    }).json()

# Use cached execution
def execute_with_cache(tool_name: str, arguments: dict):
    args_json = json.dumps(arguments, sort_keys=True)
    tool_hash = hashlib.md5(f"{tool_name}{args_json}".encode()).hexdigest()
    return cached_webpilot_execute(tool_hash, tool_name, args_json)
```

## Example: Complete Automation Flow

```python
import requests
import json
from typing import List, Dict

class LocalLLMWebAutomation:
    """Complete automation system with local LLM + WebPilot."""
    
    def __init__(self, llm_url: str, webpilot_url: str = "http://localhost:8000"):
        self.llm_url = llm_url
        self.webpilot_url = webpilot_url
        self.session_id = self._init_session()
    
    def _init_session(self) -> str:
        """Initialize WebPilot session."""
        response = requests.post(f"{self.webpilot_url}/sessions")
        return response.json()["session_id"]
    
    def automate(self, task: str) -> List[Dict]:
        """Automate a complex task."""
        results = []
        
        # Get LLM to plan the task
        plan = self._get_llm_plan(task)
        
        # Execute each step
        for step in plan:
            result = self._execute_step(step)
            results.append(result)
            
            # Give feedback to LLM
            if not result["success"]:
                recovery = self._get_llm_recovery(step, result["error"])
                result = self._execute_step(recovery)
                results.append(result)
        
        return results
    
    def _get_llm_plan(self, task: str) -> List[Dict]:
        """Get LLM to create an execution plan."""
        prompt = f"""
        Create a WebPilot automation plan for: {task}
        
        Available tools: navigate, click, type, screenshot, extract, scroll
        
        Return JSON array of steps:
        [{{"tool": "navigate", "args": {{"url": "..."}}}}, ...]
        """
        
        response = requests.post(f"{self.llm_url}/completions", json={
            "prompt": prompt,
            "max_tokens": 500
        })
        
        return json.loads(response.json()["text"])
    
    def _execute_step(self, step: Dict) -> Dict:
        """Execute a single automation step."""
        return requests.post(f"{self.webpilot_url}/execute", json={
            "tool_name": step["tool"],
            "arguments": step.get("args", {}),
            "session_id": self.session_id
        }).json()
    
    def _get_llm_recovery(self, failed_step: Dict, error: str) -> Dict:
        """Get LLM to suggest recovery from error."""
        prompt = f"""
        WebPilot step failed:
        Step: {json.dumps(failed_step)}
        Error: {error}
        
        Suggest alternative approach as JSON:
        {{"tool": "...", "args": {{}}}}
        """
        
        response = requests.post(f"{self.llm_url}/completions", json={
            "prompt": prompt,
            "max_tokens": 200
        })
        
        return json.loads(response.json()["text"])

# Use the automation system
automation = LocalLLMWebAutomation(
    llm_url="http://localhost:1234/v1",  # LM Studio
    webpilot_url="http://localhost:8000"  # WebPilot
)

results = automation.automate(
    "Find the latest Python version on Python.org and take a screenshot"
)

for result in results:
    print(f"Step result: {result}")
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Ensure WebPilot API is running
   python -m webpilot.server.rest_api
   ```

2. **LLM Not Responding**
   ```bash
   # Check if Ollama is running
   ollama list
   
   # Check if LM Studio server is active
   curl http://localhost:1234/v1/models
   ```

3. **Function Calling Not Working**
   - Use models that support function calling (GPT-4, Claude, newer Llama models)
   - Provide clear function descriptions in prompts
   - Use structured output formats

4. **Performance Issues**
   - Use headless mode: `headless=True`
   - Reuse sessions instead of creating new ones
   - Batch operations when possible
   - Use smaller, faster models for simple tasks

## Next Steps

1. **Try Different Models**
   - Llama 2/3 for general automation
   - CodeLlama for technical tasks
   - Mistral for fast responses
   - Mixtral for complex reasoning

2. **Build Custom Integrations**
   - Create model-specific adapters
   - Optimize prompts for your LLM
   - Add custom tools and workflows

3. **Deploy in Production**
   - Use Docker for containerization
   - Set up proper authentication
   - Implement rate limiting
   - Add monitoring and logging

## Support

- GitHub Issues: https://github.com/Luminous-Dynamics/webpilot/issues
- Documentation: https://luminous-dynamics.github.io/webpilot/
- PyPI Package: https://pypi.org/project/claude-webpilot/

---

**Happy Automating with Local LLMs! 🤖🌐**
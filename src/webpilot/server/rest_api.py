"""
REST API Server for WebPilot

Provides HTTP endpoints for any LLM to interact with WebPilot,
enabling universal compatibility with local and remote models.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path

from ..core import WebPilot, ActionResult
from ..mcp.server import WebPilotMCPServer
from ..adapters import OpenAIAdapter
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# FastAPI app
app = FastAPI(
    title="WebPilot Universal API",
    description="REST API for web automation accessible to any LLM",
    version="1.4.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for browser-based access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default={}, description="Tool arguments")
    session_id: Optional[str] = Field(None, description="Session ID for persistent sessions")
    
    class Config:
        schema_extra = {
            "example": {
                "tool_name": "navigate",
                "arguments": {"url": "https://example.com"},
                "session_id": "abc123"
            }
        }


class BatchExecutionRequest(BaseModel):
    """Request model for batch tool execution."""
    tools: List[ToolExecutionRequest] = Field(..., description="List of tools to execute")
    parallel: bool = Field(False, description="Execute tools in parallel")
    stop_on_error: bool = Field(True, description="Stop batch on first error")


class NaturalLanguageRequest(BaseModel):
    """Request model for natural language commands."""
    query: str = Field(..., description="Natural language command")
    session_id: Optional[str] = Field(None, description="Session ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Go to Google and search for Python tutorials",
                "session_id": "abc123"
            }
        }


class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str
    created_at: datetime
    last_activity: datetime
    current_url: Optional[str]
    screenshot_path: Optional[str]
    is_active: bool


class ToolResponse(BaseModel):
    """Standard tool execution response."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    session_id: Optional[str] = None
    screenshot: Optional[str] = None


# Global session manager
class SessionManager:
    """Manages WebPilot sessions across API calls."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.mcp_server = WebPilotMCPServer()
        
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session."""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        self.sessions[session_id] = {
            "pilot": WebPilot(),
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "current_url": None,
            "is_active": False
        }
        
        logger.info(f"Created session: {session_id}")
        return session_id
        
    def get_session(self, session_id: str) -> Optional[WebPilot]:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        if session:
            session["last_activity"] = datetime.now()
            return session["pilot"]
        return None
        
    def update_session(self, session_id: str, **kwargs):
        """Update session metadata."""
        if session_id in self.sessions:
            self.sessions[session_id].update(kwargs)
            
    def close_session(self, session_id: str) -> bool:
        """Close and remove a session."""
        session = self.sessions.get(session_id)
        if session:
            pilot = session["pilot"]
            if session["is_active"]:
                pilot.close()
            del self.sessions[session_id]
            logger.info(f"Closed session: {session_id}")
            return True
        return False
        
    def list_sessions(self) -> List[SessionInfo]:
        """List all sessions."""
        sessions = []
        for sid, session in self.sessions.items():
            sessions.append(SessionInfo(
                session_id=sid,
                created_at=session["created_at"],
                last_activity=session["last_activity"],
                current_url=session.get("current_url"),
                screenshot_path=None,  # TODO: Add screenshot tracking
                is_active=session["is_active"]
            ))
        return sessions


# Initialize global session manager
session_manager = SessionManager()


# API Endpoints
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "WebPilot Universal API",
        "version": "1.4.0",
        "description": "REST API for web automation accessible to any LLM",
        "endpoints": {
            "documentation": "/docs",
            "tools": "/tools",
            "execute": "/execute",
            "sessions": "/sessions"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "sessions_active": len(session_manager.sessions),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/tools")
async def list_tools(format: str = "standard"):
    """
    List all available WebPilot tools.
    
    Args:
        format: Output format (standard, openai, mcp, simple)
    """
    if format == "openai":
        adapter = OpenAIAdapter()
        return {"tools": adapter.get_functions()}
    elif format == "mcp":
        server = WebPilotMCPServer()
        tools = server.get_all_tools()
        return {"tools": [t.to_dict() for t in tools]}
    elif format == "simple":
        # Simple list of tool names
        server = WebPilotMCPServer()
        tools = server.get_all_tools()
        return {"tools": [t.name for t in tools]}
    else:
        # Standard format with categories
        server = WebPilotMCPServer()
        tools = server.get_all_tools()
        categorized = {}
        for tool in tools:
            category = "basic" if tool.name in [
                "webpilot_start", "webpilot_navigate", "webpilot_click",
                "webpilot_type", "webpilot_screenshot", "webpilot_close"
            ] else "extended"
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(tool.to_dict())
        return {"tools": categorized, "total_count": len(tools)}


@app.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific tool."""
    server = WebPilotMCPServer()
    for tool in server.get_all_tools():
        if tool.name == tool_name or tool.name == f"webpilot_{tool_name}":
            return {
                "tool": tool.to_dict(),
                "examples": generate_tool_examples(tool.name)
            }
    
    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@app.post("/execute", response_model=ToolResponse)
async def execute_tool(request: ToolExecutionRequest):
    """
    Execute a single WebPilot tool.
    
    This is the main endpoint for LLMs to interact with WebPilot.
    """
    try:
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = session_manager.create_session()
            
        # Special handling for start command
        if request.tool_name in ["start", "webpilot_start"]:
            pilot = session_manager.get_session(session_id)
            if pilot:
                result = pilot.start(request.arguments.get("url", "about:blank"))
                session_manager.update_session(
                    session_id,
                    is_active=True,
                    current_url=request.arguments.get("url")
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to create session")
        else:
            # Execute through MCP server for consistency
            result_dict = await session_manager.mcp_server.handle_tool_call(
                f"webpilot_{request.tool_name}" if not request.tool_name.startswith("webpilot_") else request.tool_name,
                request.arguments
            )
            result = ActionResult(
                success=result_dict.get("success", False),
                data=result_dict.get("data"),
                error=result_dict.get("error"),
                duration_ms=result_dict.get("duration_ms")
            )
            
        # Take screenshot if successful navigation/interaction
        screenshot_path = None
        if result.success and request.tool_name in ["navigate", "click", "type", "scroll"]:
            pilot = session_manager.get_session(session_id)
            if pilot:
                screenshot_result = pilot.screenshot()
                if screenshot_result.success:
                    screenshot_path = screenshot_result.data
                    
        return ToolResponse(
            success=result.success,
            data=result.data,
            error=result.error,
            duration_ms=result.duration_ms,
            session_id=session_id,
            screenshot=screenshot_path
        )
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return ToolResponse(
            success=False,
            error=str(e),
            session_id=request.session_id
        )


@app.post("/execute/batch")
async def execute_batch(request: BatchExecutionRequest):
    """Execute multiple tools in sequence or parallel."""
    results = []
    
    if request.parallel:
        # Execute tools in parallel
        tasks = []
        for tool_req in request.tools:
            tasks.append(execute_tool(tool_req))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                results[i] = ToolResponse(
                    success=False,
                    error=str(result)
                )
    else:
        # Execute tools sequentially
        for tool_req in request.tools:
            result = await execute_tool(tool_req)
            results.append(result)
            
            # Stop on error if requested
            if not result.success and request.stop_on_error:
                break
                
    return {
        "results": results,
        "total": len(request.tools),
        "executed": len(results),
        "success_count": sum(1 for r in results if r.success)
    }


@app.post("/execute/natural")
async def execute_natural_language(request: NaturalLanguageRequest):
    """
    Execute commands from natural language.
    
    This endpoint attempts to parse natural language into tool calls.
    For best results, use with an LLM that can generate structured commands.
    """
    # This is a simplified implementation
    # In production, you'd use NLP to parse the query
    
    # Basic pattern matching for common commands
    query_lower = request.query.lower()
    
    tools_to_execute = []
    
    # Parse common patterns
    if "go to" in query_lower or "navigate to" in query_lower:
        # Extract URL
        import re
        url_match = re.search(r'https?://[^\s]+', request.query)
        if url_match:
            tools_to_execute.append(ToolExecutionRequest(
                tool_name="navigate",
                arguments={"url": url_match.group()},
                session_id=request.session_id
            ))
    
    if "click" in query_lower:
        # Extract what to click
        words = request.query.split()
        click_index = words.index("click") if "click" in words else -1
        if click_index >= 0 and click_index < len(words) - 1:
            target = " ".join(words[click_index + 1:])
            tools_to_execute.append(ToolExecutionRequest(
                tool_name="click",
                arguments={"text": target},
                session_id=request.session_id
            ))
    
    if "type" in query_lower or "enter" in query_lower:
        # Extract text to type
        import re
        quoted = re.findall(r'"([^"]*)"', request.query)
        if quoted:
            tools_to_execute.append(ToolExecutionRequest(
                tool_name="type",
                arguments={"text": quoted[0]},
                session_id=request.session_id
            ))
    
    if "screenshot" in query_lower:
        tools_to_execute.append(ToolExecutionRequest(
            tool_name="screenshot",
            arguments={},
            session_id=request.session_id
        ))
    
    # Execute parsed tools
    if tools_to_execute:
        batch_request = BatchExecutionRequest(
            tools=tools_to_execute,
            parallel=False,
            stop_on_error=True
        )
        return await execute_batch(batch_request)
    else:
        return {
            "success": False,
            "error": "Could not parse natural language query into tool calls",
            "suggestion": "Try using more specific commands like 'go to URL' or 'click button'"
        }


# Session Management Endpoints
@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    return {
        "sessions": session_manager.list_sessions(),
        "count": len(session_manager.sessions)
    }


@app.post("/sessions")
async def create_session():
    """Create a new session."""
    session_id = session_manager.create_session()
    return {
        "session_id": session_id,
        "created_at": datetime.now().isoformat()
    }


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information."""
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = session_manager.sessions[session_id]
    return SessionInfo(
        session_id=session_id,
        created_at=session["created_at"],
        last_activity=session["last_activity"],
        current_url=session.get("current_url"),
        screenshot_path=None,
        is_active=session["is_active"]
    )


@app.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    """Close and delete a session."""
    if session_manager.close_session(session_id):
        return {"success": True, "message": f"Session {session_id} closed"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/sessions/{session_id}/screenshot")
async def get_session_screenshot(session_id: str):
    """Get current screenshot from session."""
    pilot = session_manager.get_session(session_id)
    if not pilot:
        raise HTTPException(status_code=404, detail="Session not found")
        
    result = pilot.screenshot()
    if result.success and result.data:
        screenshot_path = Path(result.data)
        if screenshot_path.exists():
            return FileResponse(
                screenshot_path,
                media_type="image/png",
                filename=f"screenshot_{session_id}.png"
            )
    
    raise HTTPException(status_code=404, detail="Screenshot not available")


# WebSocket endpoint for real-time interaction
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time interaction with WebPilot.
    
    Useful for streaming updates and maintaining persistent connections.
    """
    await websocket.accept()
    
    # Create or get session
    if session_id not in session_manager.sessions:
        session_manager.create_session(session_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Execute tool
            request = ToolExecutionRequest(**data)
            request.session_id = session_id
            result = await execute_tool(request)
            
            # Send result
            await websocket.send_json(result.dict())
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


# Utility functions
def generate_tool_examples(tool_name: str) -> List[Dict[str, Any]]:
    """Generate usage examples for a tool."""
    examples = {
        "webpilot_navigate": [
            {
                "description": "Navigate to Google",
                "request": {
                    "tool_name": "navigate",
                    "arguments": {"url": "https://www.google.com"}
                }
            }
        ],
        "webpilot_click": [
            {
                "description": "Click search button",
                "request": {
                    "tool_name": "click",
                    "arguments": {"text": "Search"}
                }
            },
            {
                "description": "Click by selector",
                "request": {
                    "tool_name": "click",
                    "arguments": {"selector": "#submit-button"}
                }
            }
        ],
        "webpilot_type": [
            {
                "description": "Type in search box",
                "request": {
                    "tool_name": "type",
                    "arguments": {"text": "Python tutorials"}
                }
            }
        ]
    }
    
    return examples.get(tool_name, [])


# OpenAPI customization
@app.get("/openapi.yaml")
async def get_openapi_yaml():
    """Get OpenAPI specification in YAML format."""
    from fastapi.openapi.utils import get_openapi
    import yaml
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    return yaml.dump(openapi_schema)


# Integration examples endpoint
@app.get("/examples/{platform}")
async def get_integration_example(platform: str):
    """
    Get integration example for specific platform.
    
    Platforms: ollama, lm-studio, langchain, openai, gemini
    """
    examples = {
        "ollama": """
# Ollama Integration Example

import requests
import json

# Start WebPilot API server
# python -m webpilot.server.rest_api

# Create session
session = requests.post("http://localhost:8000/sessions").json()
session_id = session["session_id"]

# Use with Ollama
import ollama

# Get response from Ollama
response = ollama.chat(model='llama2', messages=[
    {'role': 'user', 'content': 'Navigate to example.com and take a screenshot'}
])

# Parse and execute with WebPilot
result = requests.post("http://localhost:8000/execute", json={
    "tool_name": "navigate",
    "arguments": {"url": "https://example.com"},
    "session_id": session_id
}).json()

print(f"Navigation result: {result}")
""",
        "lm-studio": """
# LM Studio Integration Example

import requests

# LM Studio API endpoint
lm_studio_url = "http://localhost:1234/v1/chat/completions"

# WebPilot API endpoint
webpilot_url = "http://localhost:8000"

# Create WebPilot session
session = requests.post(f"{webpilot_url}/sessions").json()
session_id = session["session_id"]

# Get available tools
tools = requests.get(f"{webpilot_url}/tools?format=openai").json()

# Send to LM Studio with tools
response = requests.post(lm_studio_url, json={
    "model": "local-model",
    "messages": [{"role": "user", "content": "Search for Python tutorials"}],
    "functions": tools["tools"],
    "function_call": "auto"
})

# Execute function calls with WebPilot
function_call = response.json()["choices"][0]["message"].get("function_call")
if function_call:
    result = requests.post(f"{webpilot_url}/execute", json={
        "tool_name": function_call["name"],
        "arguments": json.loads(function_call["arguments"]),
        "session_id": session_id
    })
    print(f"Execution result: {result.json()}")
""",
        "langchain": """
# LangChain Integration Example

from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.llms import Ollama
import requests

class WebPilotTool:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self._create_session()
    
    def _create_session(self):
        response = requests.post(f"{self.base_url}/sessions")
        self.session_id = response.json()["session_id"]
    
    def execute(self, command: str) -> str:
        # Use natural language endpoint
        response = requests.post(f"{self.base_url}/execute/natural", json={
            "query": command,
            "session_id": self.session_id
        })
        return json.dumps(response.json())

# Create WebPilot tool for LangChain
webpilot = WebPilotTool()
webpilot_tool = Tool(
    name="WebPilot",
    func=webpilot.execute,
    description="Web automation tool for browsing and interacting with websites"
)

# Create agent with local LLM
llm = Ollama(model="llama2")
agent = initialize_agent(
    [webpilot_tool],
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Use the agent
result = agent.run("Go to Python.org and find documentation about asyncio")
print(result)
"""
    }
    
    if platform not in examples:
        raise HTTPException(
            status_code=404,
            detail=f"No example available for '{platform}'. Available: {list(examples.keys())}"
        )
    
    return {
        "platform": platform,
        "example": examples[platform],
        "description": f"Integration example for {platform}"
    }


# Run server
if __name__ == "__main__":
    import uvicorn
    
    # Run with: python -m webpilot.server.rest_api
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
#!/usr/bin/env python3
"""
Run the WebPilot MCP server.

This script starts the MCP server and handles the MCP protocol
communication with AI assistants.
"""

import asyncio
import json
import sys
from typing import Dict, Any
import logging

from webpilot.mcp.server import WebPilotMCPServer


class MCPProtocolHandler:
    """Handles MCP protocol communication."""
    
    def __init__(self, server: WebPilotMCPServer):
        """Initialize the protocol handler."""
        self.server = server
        self.logger = logging.getLogger(__name__)
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP protocol request.
        
        Args:
            request: MCP request object
            
        Returns:
            MCP response object
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                # Initialize handshake
                response = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": self.server.get_server_info()["capabilities"],
                    "serverInfo": self.server.get_server_info()
                }
            
            elif method == "tools/list":
                # List available tools
                tools = [tool.to_dict() for tool in self.server.get_tools()]
                response = {"tools": tools}
            
            elif method == "tools/call":
                # Execute a tool
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self.server.handle_tool_call(tool_name, arguments)
                response = {"result": result}
            
            elif method == "resources/list":
                # List available resources
                resources = [r.to_dict() for r in self.server.get_resources()]
                response = {"resources": resources}
            
            elif method == "resources/read":
                # Read a resource
                uri = params.get("uri")
                result = await self.server.handle_resource_read(uri)
                response = {"contents": [result]}
            
            elif method == "ping":
                # Health check
                response = {"pong": True}
            
            else:
                # Unknown method
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response
            }
            
        except Exception as e:
            self.logger.error(f"Request handling failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    async def run_stdio_server(self):
        """Run the MCP server using stdio for communication."""
        self.logger.info("WebPilot MCP server started (stdio mode)")
        
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        writer = asyncio.StreamWriter(
            transport=sys.stdout,
            protocol=None,
            reader=None,
            loop=asyncio.get_event_loop()
        )
        
        while True:
            try:
                # Read a line from stdin
                line = await reader.readline()
                if not line:
                    break
                
                # Parse JSON-RPC request
                request = json.loads(line.decode())
                self.logger.debug(f"Received request: {request}")
                
                # Handle the request
                response = await self.handle_request(request)
                
                # Send response
                response_line = json.dumps(response) + "\n"
                writer.write(response_line.encode())
                await writer.drain()
                self.logger.debug(f"Sent response: {response}")
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                writer.write((json.dumps(error_response) + "\n").encode())
                await writer.drain()
            
            except Exception as e:
                self.logger.error(f"Server error: {e}")
                break
        
        self.logger.info("WebPilot MCP server stopped")


async def main():
    """Main entry point for the MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/tmp/webpilot_mcp.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create server and handler
    server = WebPilotMCPServer()
    handler = MCPProtocolHandler(server)
    
    # Print server info for debugging
    print(f"WebPilot MCP Server v{server.get_server_info()['version']}", file=sys.stderr)
    print(f"Capabilities: {json.dumps(server.get_server_info()['capabilities'], indent=2)}", file=sys.stderr)
    print(f"Available tools: {len(server.get_tools())}", file=sys.stderr)
    
    # Run the server
    await handler.run_stdio_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
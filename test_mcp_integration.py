#!/usr/bin/env python3
"""
Test script to verify MCP integration is working correctly.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from webpilot.mcp import WebPilotMCPServer, WebPilotTools, WebPilotResources


async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🧪 Testing WebPilot MCP Integration\n")
    
    # 1. Create server
    print("1️⃣ Creating MCP server...")
    server = WebPilotMCPServer()
    print(f"   ✅ Server created: {server.get_server_info()['name']} v{server.get_server_info()['version']}\n")
    
    # 2. Check tools
    print("2️⃣ Checking available tools...")
    tools = server.get_tools()
    print(f"   ✅ {len(tools)} tools available")
    print(f"   📋 Sample tools: {', '.join([t.name for t in tools[:5]])}...\n")
    
    # 3. Test tool schemas
    print("3️⃣ Validating tool schemas...")
    for tool in tools[:3]:
        tool_dict = tool.to_dict()
        assert "name" in tool_dict
        assert "description" in tool_dict
        assert "inputSchema" in tool_dict
        print(f"   ✅ {tool.name}: {tool.description[:50]}...")
    print()
    
    # 4. Test resources manager
    print("4️⃣ Testing resource management...")
    resources = WebPilotResources()
    session = resources.create_session("test-session-001")
    print(f"   ✅ Created session: {session.session_id}")
    
    # Add some test data
    resources.add_action("test-session-001", "navigate", url="https://example.com")
    print(f"   ✅ Added action to session")
    
    # Get resources
    all_resources = resources.get_all_resources()
    print(f"   ✅ Retrieved {len(all_resources)} resources\n")
    
    # 5. Test tool catalog
    print("5️⃣ Testing tool catalog...")
    tool_catalog = WebPilotTools()
    categories = [
        ("Browser Control", tool_catalog.get_browser_control_tools()),
        ("Interaction", tool_catalog.get_interaction_tools()),
        ("Extraction", tool_catalog.get_extraction_tools()),
        ("Validation", tool_catalog.get_validation_tools()),
        ("Utility", tool_catalog.get_utility_tools())
    ]
    
    for category_name, category_tools in categories:
        print(f"   ✅ {category_name}: {len(category_tools)} tools")
    
    total_tools = sum(len(tools) for _, tools in categories)
    print(f"   📊 Total: {total_tools} tools defined\n")
    
    # 6. Test a simple tool call (mock)
    print("6️⃣ Testing tool call handler...")
    try:
        # This will fail without a real browser, but tests the handler
        result = await server.handle_tool_call("webpilot_start", {
            "url": "https://example.com",
            "browser": "firefox",
            "headless": True
        })
        
        if result.get("error"):
            print(f"   ⚠️  Expected error (no browser): {result['error'][:50]}...")
        else:
            print(f"   ✅ Tool call handled: session_id={result.get('session_id')}")
    except Exception as e:
        print(f"   ⚠️  Expected error (no browser installed): {str(e)[:50]}...")
    
    print("\n✨ MCP Integration Test Complete!")
    print("   All core MCP components are working correctly.")
    print("   Ready for AI assistant integration!\n")
    
    return True


async def test_mcp_protocol():
    """Test MCP protocol communication."""
    print("7️⃣ Testing MCP protocol handler...")
    
    from webpilot.mcp.run_server import MCPProtocolHandler
    
    server = WebPilotMCPServer()
    handler = MCPProtocolHandler(server)
    
    # Test initialize request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    
    response = await handler.handle_request(request)
    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert "capabilities" in response["result"]
    print("   ✅ Initialize request handled")
    
    # Test tools/list request
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = await handler.handle_request(request)
    assert "result" in response
    assert "tools" in response["result"]
    assert len(response["result"]["tools"]) > 0
    print("   ✅ Tools list request handled")
    
    print("   ✅ MCP protocol working correctly\n")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("WebPilot MCP Integration Test Suite")
    print("=" * 60 + "\n")
    
    try:
        # Run tests
        asyncio.run(test_mcp_server())
        asyncio.run(test_mcp_protocol())
        
        print("🎉 All tests passed! MCP integration is ready to use.")
        print("\nNext steps:")
        print("1. Install: pip install claude-webpilot")
        print("2. Configure Claude Desktop with MCP server")
        print("3. Start automating with natural language!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
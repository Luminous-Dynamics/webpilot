#!/usr/bin/env python3
"""
Quick start examples for using WebPilot with MCP.

These examples show how AI assistants can use WebPilot
through the Model Context Protocol.
"""

# For AI Assistant Users (Claude, etc.)
# ======================================
# Your AI assistant can control WebPilot through natural language.
# Just ask things like:
#
# "Go to GitHub and search for Python projects"
# "Fill out the contact form on this website"
# "Take screenshots of all product pages"
# "Check if this website is accessible"
# "Extract all email addresses from this page"

# For Developers Integrating MCP
# ==============================

import asyncio
from webpilot.mcp import WebPilotMCPServer


async def example_search_github():
    """Example: Search GitHub for repositories."""
    server = WebPilotMCPServer()
    
    # Start browser and navigate to GitHub
    result = await server.handle_tool_call("webpilot_start", {
        "url": "https://github.com",
        "browser": "firefox",
        "headless": False
    })
    
    session_id = result.get("session_id")
    print(f"Started session: {session_id}")
    
    # Click on search box
    await server.handle_tool_call("webpilot_click", {
        "selector": "input[type='search']"
    })
    
    # Type search query
    await server.handle_tool_call("webpilot_type", {
        "text": "web automation python"
    })
    
    # Press Enter to search
    await server.handle_tool_call("webpilot_type", {
        "text": "\n"  # Enter key
    })
    
    # Wait for results
    await server.handle_tool_call("webpilot_wait", {
        "seconds": 2
    })
    
    # Take screenshot
    await server.handle_tool_call("webpilot_screenshot", {
        "name": "github_search_results"
    })
    
    # Extract search results
    result = await server.handle_tool_call("webpilot_extract", {})
    print("Search results extracted!")
    
    # Close browser
    await server.handle_tool_call("webpilot_close", {})


async def example_form_filling():
    """Example: Fill out a web form."""
    server = WebPilotMCPServer()
    
    # Start browser
    await server.handle_tool_call("webpilot_start", {
        "url": "https://example.com/contact",
        "browser": "firefox"
    })
    
    # Fill form fields
    await server.handle_tool_call("webpilot_type", {
        "text": "John Doe",
        "selector": "#name"
    })
    
    await server.handle_tool_call("webpilot_type", {
        "text": "john@example.com",
        "selector": "#email"
    })
    
    await server.handle_tool_call("webpilot_type", {
        "text": "This is a test message",
        "selector": "#message"
    })
    
    # Submit form
    await server.handle_tool_call("webpilot_click", {
        "selector": "button[type='submit']"
    })
    
    # Wait and screenshot
    await server.handle_tool_call("webpilot_wait", {
        "seconds": 2
    })
    
    await server.handle_tool_call("webpilot_screenshot", {
        "name": "form_submitted"
    })
    
    await server.handle_tool_call("webpilot_close", {})


async def example_accessibility_check():
    """Example: Check website accessibility."""
    server = WebPilotMCPServer()
    
    # Start browser
    await server.handle_tool_call("webpilot_start", {
        "url": "https://example.com",
        "browser": "firefox",
        "headless": True
    })
    
    # Run accessibility check
    # Note: This would integrate with actual accessibility testing tools
    print("Running WCAG 2.0 AA compliance check...")
    
    # Take screenshots for visual inspection
    await server.handle_tool_call("webpilot_screenshot", {
        "name": "accessibility_check"
    })
    
    # Check for common issues
    # - Alt text on images
    # - Proper heading structure
    # - Color contrast
    # - Keyboard navigation
    
    await server.handle_tool_call("webpilot_close", {})
    print("Accessibility check complete!")


# Natural Language Examples for AI Assistants
# ===========================================

NATURAL_LANGUAGE_EXAMPLES = """
Examples of what you can ask your AI assistant:

Basic Navigation:
- "Go to amazon.com and search for wireless headphones"
- "Navigate to the login page and take a screenshot"
- "Open three tabs with different news websites"

Form Interaction:
- "Fill out the contact form with test data"
- "Login with username 'test' and password 'demo123'"
- "Select 'California' from the state dropdown"

Data Extraction:
- "Get all the product prices from this page"
- "Extract the email addresses from the contact page"
- "Copy all the headlines from this news site"
- "Get the table data and save it as CSV"

Testing & Validation:
- "Check if the login button is visible"
- "Verify that the page title contains 'Welcome'"
- "Test if all links on this page are working"
- "Check this site for accessibility issues"

Advanced Automation:
- "Go through the checkout process but don't complete the purchase"
- "Compare prices for this product across three different sites"
- "Monitor this page and alert me when the status changes"
- "Take screenshots of all pages in the site navigation"
"""


if __name__ == "__main__":
    print("WebPilot MCP Quick Start Examples")
    print("=" * 40)
    print("\nChoose an example to run:")
    print("1. Search GitHub")
    print("2. Fill a form")
    print("3. Check accessibility")
    print("4. Show natural language examples")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        asyncio.run(example_search_github())
    elif choice == "2":
        asyncio.run(example_form_filling())
    elif choice == "3":
        asyncio.run(example_accessibility_check())
    elif choice == "4":
        print(NATURAL_LANGUAGE_EXAMPLES)
    else:
        print("Invalid choice!")
#!/usr/bin/env python
"""
Universal CLI for WebPilot

Command-line interface that works with any LLM backend.
"""

import click
import json
import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown

from ..core import WebPilot
from ..adapters import OpenAIAdapter
from ..integrations import create_webpilot_agent, LANGCHAIN_AVAILABLE
from ..server.rest_api import app
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
console = Console()


@click.group()
@click.version_option(version="1.4.0", prog_name="WebPilot")
@click.option('--config', '-c', type=click.Path(), help='Config file path')
@click.pass_context
def cli(ctx, config):
    """
    WebPilot Universal CLI - Web automation from the command line.
    
    Works with any LLM backend: OpenAI, Ollama, LM Studio, or direct commands.
    """
    ctx.ensure_object(dict)
    
    # Load config if provided
    if config and Path(config).exists():
        with open(config) as f:
            if config.endswith('.yaml') or config.endswith('.yml'):
                ctx.obj['config'] = yaml.safe_load(f)
            else:
                ctx.obj['config'] = json.load(f)
    else:
        ctx.obj['config'] = {}


@cli.command()
@click.argument('url')
@click.option('--screenshot', '-s', is_flag=True, help='Take screenshot after navigation')
@click.option('--extract', '-e', is_flag=True, help='Extract page content')
@click.option('--headless', '-h', is_flag=True, help='Run in headless mode')
@click.option('--browser', '-b', type=click.Choice(['firefox', 'chrome', 'chromium']), default='firefox')
@click.pass_context
def browse(ctx, url, screenshot, extract, headless, browser):
    """Navigate to a URL and optionally screenshot/extract content."""
    
    with console.status(f"[bold green]Starting {browser}..."):
        pilot = WebPilot(browser=browser, headless=headless)
        result = pilot.start(url)
        
    if result.success:
        console.print(f"✅ Navigated to [bold blue]{url}[/bold blue]")
        
        if screenshot:
            with console.status("[bold green]Taking screenshot..."):
                screenshot_result = pilot.screenshot()
                if screenshot_result.success:
                    console.print(f"📸 Screenshot saved: {screenshot_result.data}")
                    
        if extract:
            with console.status("[bold green]Extracting content..."):
                extract_result = pilot.extract_page_content()
                if extract_result.success:
                    content = extract_result.data
                    if isinstance(content, dict):
                        console.print(Panel(json.dumps(content, indent=2), title="Page Content"))
                    else:
                        console.print(Panel(str(content)[:1000], title="Page Content (truncated)"))
    else:
        console.print(f"❌ Failed: {result.error}", style="red")
        
    pilot.close()


@cli.command()
@click.argument('command')
@click.option('--llm', type=click.Choice(['openai', 'ollama', 'lmstudio', 'langchain', 'direct']), default='direct')
@click.option('--model', '-m', help='LLM model to use')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='API key for LLM')
@click.option('--api-url', help='API URL for local LLMs')
@click.option('--headless', '-h', is_flag=True, help='Run browser in headless mode')
@click.option('--output', '-o', type=click.Path(), help='Save output to file')
@click.pass_context
def execute(ctx, command, llm, model, api_key, api_url, headless, output):
    """
    Execute natural language commands using specified LLM backend.
    
    Examples:
        webpilot execute "Go to Google and search for Python"
        webpilot execute "Take screenshot of current page" --llm ollama
        webpilot execute "Extract all links" --llm openai --model gpt-4
    """
    
    result = None
    
    if llm == 'direct':
        # Direct execution without LLM interpretation
        result = execute_direct_command(command, headless)
    elif llm == 'openai':
        result = execute_with_openai(command, model or 'gpt-4', api_key, headless)
    elif llm == 'ollama':
        result = execute_with_ollama(command, model or 'llama2', api_url or 'http://localhost:11434', headless)
    elif llm == 'lmstudio':
        result = execute_with_lmstudio(command, api_url or 'http://localhost:1234', headless)
    elif llm == 'langchain':
        if LANGCHAIN_AVAILABLE:
            result = execute_with_langchain(command, model, headless)
        else:
            console.print("❌ LangChain not installed. Install with: pip install langchain", style="red")
            return
    
    # Display result
    if result:
        if result.get('success'):
            console.print(f"✅ {result.get('message', 'Command executed successfully')}", style="green")
            if result.get('data'):
                console.print(Panel(json.dumps(result['data'], indent=2), title="Result"))
        else:
            console.print(f"❌ {result.get('error', 'Command failed')}", style="red")
            
        # Save output if requested
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            console.print(f"💾 Output saved to {output}")


@cli.command()
@click.option('--host', '-h', default='0.0.0.0', help='Server host')
@click.option('--port', '-p', default=8000, help='Server port')
@click.option('--reload', is_flag=True, help='Auto-reload on code changes')
def serve(host, port, reload):
    """Start the WebPilot REST API server for LLM integration."""
    
    console.print(Panel.fit(
        f"[bold green]Starting WebPilot REST API Server[/bold green]\n\n"
        f"🌐 Server: http://{host}:{port}\n"
        f"📚 Docs: http://{host}:{port}/docs\n"
        f"🔌 WebSocket: ws://{host}:{port}/ws/{{session_id}}\n\n"
        f"Press [bold red]Ctrl+C[/bold red] to stop",
        title="WebPilot API Server"
    ))
    
    import uvicorn
    uvicorn.run(
        "webpilot.server.rest_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@cli.command()
@click.option('--format', '-f', type=click.Choice(['simple', 'detailed', 'openai', 'mcp']), default='simple')
@click.option('--category', '-c', help='Filter by category')
def tools(format, category):
    """List all available WebPilot tools."""
    
    if format == 'simple':
        show_tools_simple(category)
    elif format == 'detailed':
        show_tools_detailed(category)
    elif format == 'openai':
        show_tools_openai(category)
    elif format == 'mcp':
        show_tools_mcp(category)


@cli.command()
@click.argument('script_file', type=click.Path(exists=True))
@click.option('--variables', '-v', multiple=True, help='Variables in key=value format')
@click.option('--dry-run', is_flag=True, help='Show what would be executed without running')
@click.option('--headless', '-h', is_flag=True, help='Run browser in headless mode')
def run(script_file, variables, dry_run, headless):
    """
    Run a WebPilot automation script.
    
    Scripts can be in JSON or YAML format.
    """
    
    # Load script
    with open(script_file) as f:
        if script_file.endswith('.yaml') or script_file.endswith('.yml'):
            script = yaml.safe_load(f)
        else:
            script = json.load(f)
    
    # Parse variables
    vars_dict = {}
    for var in variables:
        key, value = var.split('=', 1)
        vars_dict[key] = value
    
    # Replace variables in script
    script_str = json.dumps(script)
    for key, value in vars_dict.items():
        script_str = script_str.replace(f"${{{key}}}", value)
    script = json.loads(script_str)
    
    if dry_run:
        console.print(Panel(json.dumps(script, indent=2), title="Script to Execute (Dry Run)"))
        return
    
    # Execute script
    execute_script(script, headless)


@cli.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--output', '-o', type=click.Path(), help='Output directory for screenshots')
@click.option('--full-page', is_flag=True, help='Capture full page')
@click.option('--headless', '-h', is_flag=True, help='Run in headless mode')
def screenshot(urls, output, full_page, headless):
    """Take screenshots of one or more URLs."""
    
    output_dir = Path(output) if output else Path.cwd()
    output_dir.mkdir(exist_ok=True)
    
    pilot = WebPilot(headless=headless)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task(f"Taking screenshots...", total=len(urls))
        
        for url in urls:
            progress.update(task, description=f"Capturing {url}")
            
            result = pilot.start(url)
            if result.success:
                # Generate filename from URL
                from urllib.parse import urlparse
                parsed = urlparse(url)
                filename = f"{parsed.netloc}_{parsed.path.replace('/', '_')}.png"
                filepath = output_dir / filename
                
                screenshot_result = pilot.screenshot(str(filepath), full_page=full_page)
                if screenshot_result.success:
                    console.print(f"✅ Saved: {filepath}")
                else:
                    console.print(f"❌ Failed to screenshot {url}: {screenshot_result.error}", style="red")
            else:
                console.print(f"❌ Failed to navigate to {url}: {result.error}", style="red")
                
            progress.advance(task)
    
    pilot.close()
    console.print(f"\n📸 Screenshots saved to {output_dir}")


@cli.command()
@click.option('--llm', type=click.Choice(['openai', 'ollama', 'local']), help='LLM backend to test')
@click.option('--api-url', help='API URL for local LLMs')
def test(llm, api_url):
    """Test WebPilot installation and LLM connectivity."""
    
    console.print(Panel.fit("[bold]WebPilot System Test[/bold]", style="cyan"))
    
    tests = []
    
    # Test WebPilot core
    try:
        pilot = WebPilot(headless=True)
        pilot.close()
        tests.append(("WebPilot Core", "✅ Working"))
    except Exception as e:
        tests.append(("WebPilot Core", f"❌ Failed: {e}"))
    
    # Test REST API
    try:
        import requests
        if api_url:
            response = requests.get(f"{api_url}/health", timeout=2)
        else:
            response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            tests.append(("REST API Server", "✅ Running"))
        else:
            tests.append(("REST API Server", "⚠️ Not running (start with 'webpilot serve')"))
    except:
        tests.append(("REST API Server", "⚠️ Not running (start with 'webpilot serve')"))
    
    # Test LLM backends
    if llm == 'openai':
        try:
            import openai
            tests.append(("OpenAI Integration", "✅ Available"))
        except:
            tests.append(("OpenAI Integration", "❌ Not installed (pip install openai)"))
            
    elif llm == 'ollama':
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                tests.append(("Ollama", f"✅ Running ({len(models)} models)"))
            else:
                tests.append(("Ollama", "⚠️ Not running"))
        except:
            tests.append(("Ollama", "⚠️ Not running (install from ollama.ai)"))
    
    # Test LangChain
    if LANGCHAIN_AVAILABLE:
        tests.append(("LangChain", "✅ Available"))
    else:
        tests.append(("LangChain", "⚠️ Not installed (optional)"))
    
    # Display results
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    
    for component, status in tests:
        table.add_row(component, status)
    
    console.print(table)


# Helper functions

def execute_direct_command(command: str, headless: bool) -> Dict[str, Any]:
    """Execute command directly without LLM interpretation."""
    pilot = WebPilot(headless=headless)
    
    try:
        # Parse simple commands
        cmd_lower = command.lower()
        
        if "navigate" in cmd_lower or "go to" in cmd_lower:
            import re
            url_match = re.search(r'https?://[^\s]+', command)
            if url_match:
                result = pilot.start(url_match.group())
                return {"success": result.success, "data": result.data, "error": result.error}
                
        elif "screenshot" in cmd_lower:
            result = pilot.screenshot()
            return {"success": result.success, "data": result.data, "error": result.error}
            
        elif "click" in cmd_lower:
            # Extract what to click
            import re
            quoted = re.findall(r'"([^"]*)"', command)
            if quoted:
                result = pilot.click(text=quoted[0])
                return {"success": result.success, "data": result.data, "error": result.error}
                
        elif "type" in cmd_lower:
            import re
            quoted = re.findall(r'"([^"]*)"', command)
            if quoted:
                result = pilot.type_text(quoted[0])
                return {"success": result.success, "data": result.data, "error": result.error}
                
        else:
            return {"success": False, "error": f"Could not parse command: {command}"}
            
    finally:
        pilot.close()


def execute_with_openai(command: str, model: str, api_key: str, headless: bool) -> Dict[str, Any]:
    """Execute command using OpenAI."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        adapter = OpenAIAdapter(headless=headless)
        functions = adapter.get_functions()
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a web automation assistant. Convert user commands to function calls."},
                {"role": "user", "content": command}
            ],
            functions=functions,
            function_call="auto"
        )
        
        if response.choices[0].message.function_call:
            func_call = response.choices[0].message.function_call
            result = asyncio.run(adapter.execute_function(
                func_call.name,
                json.loads(func_call.arguments)
            ))
            return result
        else:
            return {"success": False, "error": "No function call generated"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_with_ollama(command: str, model: str, api_url: str, headless: bool) -> Dict[str, Any]:
    """Execute command using Ollama."""
    try:
        import requests
        
        # Get Ollama to interpret the command
        response = requests.post(f"{api_url}/api/generate", json={
            "model": model,
            "prompt": f"Convert this to WebPilot tool calls: {command}\nRespond only with JSON.",
            "stream": False
        })
        
        if response.status_code == 200:
            # Parse response and execute
            # This is simplified - in production you'd parse the Ollama output
            return execute_direct_command(command, headless)
        else:
            return {"success": False, "error": f"Ollama error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_with_lmstudio(command: str, api_url: str, headless: bool) -> Dict[str, Any]:
    """Execute command using LM Studio."""
    try:
        import requests
        
        adapter = OpenAIAdapter(headless=headless)
        functions = adapter.get_simplified_functions()
        
        response = requests.post(f"{api_url}/v1/chat/completions", json={
            "model": "local-model",
            "messages": [
                {"role": "user", "content": command}
            ],
            "functions": functions,
            "function_call": "auto"
        })
        
        if response.status_code == 200:
            data = response.json()
            if "function_call" in data["choices"][0]["message"]:
                func_call = data["choices"][0]["message"]["function_call"]
                result = asyncio.run(adapter.execute_function(
                    func_call["name"],
                    json.loads(func_call["arguments"])
                ))
                return result
                
        return {"success": False, "error": "LM Studio did not generate function call"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_with_langchain(command: str, model: str, headless: bool) -> Dict[str, Any]:
    """Execute command using LangChain."""
    try:
        from langchain_community.llms import Ollama
        from ..integrations import create_webpilot_agent
        
        llm = Ollama(model=model or "llama2")
        agent = create_webpilot_agent(llm, headless=headless, verbose=False)
        
        result = agent.run(command)
        return {"success": True, "data": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def show_tools_simple(category: Optional[str] = None):
    """Show tools in simple format."""
    from ..mcp.server import WebPilotMCPServer
    
    server = WebPilotMCPServer()
    tools = server.get_all_tools()
    
    if category:
        # Filter by category (this is simplified)
        pass
    
    console.print(Panel.fit("[bold]Available WebPilot Tools[/bold]", style="cyan"))
    
    for tool in tools[:20]:  # Show first 20
        console.print(f"• {tool.name}: {tool.description}")
    
    if len(tools) > 20:
        console.print(f"\n... and {len(tools) - 20} more tools")
    
    console.print(f"\nTotal: {len(tools)} tools available")


def show_tools_detailed(category: Optional[str] = None):
    """Show tools in detailed format."""
    from ..mcp.server import WebPilotMCPServer
    
    server = WebPilotMCPServer()
    tools = server.get_all_tools()
    
    table = Table(title="WebPilot Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Description")
    table.add_column("Parameters")
    
    for tool in tools[:10]:  # Show first 10 in detail
        params = ", ".join(tool.input_schema.get("properties", {}).keys())
        table.add_row(tool.name, tool.description[:50] + "...", params)
    
    console.print(table)


def show_tools_openai(category: Optional[str] = None):
    """Show tools in OpenAI format."""
    adapter = OpenAIAdapter()
    functions = adapter.get_functions()
    
    syntax = Syntax(json.dumps(functions[:3], indent=2), "json", theme="monokai")
    console.print(Panel(syntax, title="OpenAI Function Format (first 3 tools)"))


def show_tools_mcp(category: Optional[str] = None):
    """Show tools in MCP format."""
    from ..mcp.server import WebPilotMCPServer
    
    server = WebPilotMCPServer()
    tools = server.get_all_tools()
    
    mcp_format = [t.to_dict() for t in tools[:3]]
    syntax = Syntax(json.dumps(mcp_format, indent=2), "json", theme="monokai")
    console.print(Panel(syntax, title="MCP Format (first 3 tools)"))


def execute_script(script: Dict[str, Any], headless: bool):
    """Execute an automation script."""
    pilot = WebPilot(headless=headless)
    
    try:
        steps = script.get('steps', [])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Executing script...", total=len(steps))
            
            for i, step in enumerate(steps):
                progress.update(task, description=f"Step {i+1}: {step.get('action', 'unknown')}")
                
                action = step.get('action')
                args = step.get('arguments', {})
                
                if action == 'navigate':
                    result = pilot.navigate(args.get('url'))
                elif action == 'click':
                    result = pilot.click(**args)
                elif action == 'type':
                    result = pilot.type_text(**args)
                elif action == 'screenshot':
                    result = pilot.screenshot(**args)
                elif action == 'wait':
                    result = pilot.wait(args.get('seconds', 1))
                elif action == 'extract':
                    result = pilot.extract_page_content()
                else:
                    console.print(f"Unknown action: {action}", style="yellow")
                    continue
                
                if not result.success:
                    console.print(f"❌ Step {i+1} failed: {result.error}", style="red")
                    if not script.get('continue_on_error', False):
                        break
                        
                progress.advance(task)
        
        console.print("✅ Script execution complete", style="green")
        
    finally:
        pilot.close()


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
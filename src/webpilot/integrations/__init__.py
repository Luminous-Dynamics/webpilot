"""
WebPilot Integrations

Integrations with various LLM frameworks and platforms.
"""

from .langchain_tools import (
    WebPilotTool,
    create_webpilot_tools,
    create_webpilot_agent,
    LANGCHAIN_AVAILABLE
)

__all__ = [
    'WebPilotTool',
    'create_webpilot_tools',
    'create_webpilot_agent',
    'LANGCHAIN_AVAILABLE'
]
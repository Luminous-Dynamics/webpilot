"""
WebPilot LLM Adapters

Adapters for integrating WebPilot with various LLM providers.
"""

from .openai_adapter import OpenAIAdapter, OpenAIFunction

__all__ = ['OpenAIAdapter', 'OpenAIFunction']
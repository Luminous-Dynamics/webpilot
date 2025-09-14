"""
Extended MCP Tools for advanced web automation.

This module adds 25+ additional tools to expand WebPilot's MCP capabilities.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ExtendedToolParameter:
    """Extended parameter definition."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None
    enum: List[str] = None


class WebPilotExtendedTools:
    """
    Extended tools for advanced automation scenarios.
    """
    
    @staticmethod
    def get_form_tools() -> List[Dict[str, Any]]:
        """Advanced form interaction tools."""
        return [
            {
                "name": "fill_form_auto",
                "description": "Automatically fill form with test data",
                "category": "forms",
                "parameters": [
                    ExtendedToolParameter("form_selector", "string", "Form selector"),
                    ExtendedToolParameter("use_faker", "boolean", "Use fake data", default=True)
                ]
            },
            {
                "name": "upload_file",
                "description": "Upload a file to a file input",
                "category": "forms",
                "parameters": [
                    ExtendedToolParameter("selector", "string", "File input selector", required=True),
                    ExtendedToolParameter("file_path", "string", "Path to file", required=True)
                ]
            },
            {
                "name": "handle_captcha",
                "description": "Attempt to handle CAPTCHA (limited success)",
                "category": "forms",
                "parameters": [
                    ExtendedToolParameter("selector", "string", "CAPTCHA selector"),
                    ExtendedToolParameter("service", "string", "CAPTCHA service", 
                                        enum=["recaptcha", "hcaptcha", "simple"])
                ]
            },
            {
                "name": "validate_form",
                "description": "Check form validation errors",
                "category": "forms",
                "parameters": [
                    ExtendedToolParameter("form_selector", "string", "Form selector")
                ]
            },
            {
                "name": "clear_form",
                "description": "Clear all form fields",
                "category": "forms",
                "parameters": [
                    ExtendedToolParameter("form_selector", "string", "Form selector")
                ]
            }
        ]
    
    @staticmethod
    def get_navigation_tools() -> List[Dict[str, Any]]:
        """Enhanced navigation tools."""
        return [
            {
                "name": "open_new_tab",
                "description": "Open URL in new tab",
                "category": "navigation",
                "parameters": [
                    ExtendedToolParameter("url", "string", "URL to open", required=True)
                ]
            },
            {
                "name": "switch_tab",
                "description": "Switch to tab by index or title",
                "category": "navigation",
                "parameters": [
                    ExtendedToolParameter("index", "integer", "Tab index"),
                    ExtendedToolParameter("title", "string", "Tab title pattern")
                ]
            },
            {
                "name": "close_tab",
                "description": "Close current or specified tab",
                "category": "navigation",
                "parameters": [
                    ExtendedToolParameter("index", "integer", "Tab index to close")
                ]
            },
            {
                "name": "open_incognito",
                "description": "Open URL in incognito/private mode",
                "category": "navigation",
                "parameters": [
                    ExtendedToolParameter("url", "string", "URL to open", required=True)
                ]
            },
            {
                "name": "handle_alert",
                "description": "Handle JavaScript alerts/confirms",
                "category": "navigation",
                "parameters": [
                    ExtendedToolParameter("action", "string", "Action to take",
                                        enum=["accept", "dismiss", "read"])
                ]
            }
        ]
    
    @staticmethod
    def get_data_tools() -> List[Dict[str, Any]]:
        """Advanced data extraction tools."""
        return [
            {
                "name": "extract_structured_data",
                "description": "Extract structured data using schema",
                "category": "data",
                "parameters": [
                    ExtendedToolParameter("schema", "object", "Data schema", required=True)
                ]
            },
            {
                "name": "extract_json_ld",
                "description": "Extract JSON-LD structured data",
                "category": "data",
                "parameters": []
            },
            {
                "name": "extract_meta_tags",
                "description": "Extract all meta tags",
                "category": "data",
                "parameters": []
            },
            {
                "name": "extract_emails",
                "description": "Extract all email addresses",
                "category": "data",
                "parameters": [
                    ExtendedToolParameter("unique", "boolean", "Return unique only", default=True)
                ]
            },
            {
                "name": "extract_phone_numbers",
                "description": "Extract phone numbers",
                "category": "data",
                "parameters": [
                    ExtendedToolParameter("country_code", "string", "Country code filter")
                ]
            },
            {
                "name": "extract_social_links",
                "description": "Extract social media links",
                "category": "data",
                "parameters": []
            },
            {
                "name": "save_as_pdf",
                "description": "Save page as PDF",
                "category": "data",
                "parameters": [
                    ExtendedToolParameter("filename", "string", "PDF filename")
                ]
            },
            {
                "name": "save_as_mhtml",
                "description": "Save complete page as MHTML",
                "category": "data",
                "parameters": [
                    ExtendedToolParameter("filename", "string", "MHTML filename")
                ]
            }
        ]
    
    @staticmethod
    def get_testing_tools() -> List[Dict[str, Any]]:
        """Comprehensive testing tools."""
        return [
            {
                "name": "check_broken_links",
                "description": "Find all broken links on page",
                "category": "testing",
                "parameters": [
                    ExtendedToolParameter("check_external", "boolean", "Check external links", default=False)
                ]
            },
            {
                "name": "check_console_errors",
                "description": "Check browser console for errors",
                "category": "testing",
                "parameters": []
            },
            {
                "name": "measure_load_time",
                "description": "Measure page load performance",
                "category": "testing",
                "parameters": []
            },
            {
                "name": "check_mobile_view",
                "description": "Test mobile responsiveness",
                "category": "testing",
                "parameters": [
                    ExtendedToolParameter("device", "string", "Device to emulate",
                                        enum=["iPhone", "iPad", "Android"])
                ]
            },
            {
                "name": "validate_html",
                "description": "Validate HTML structure",
                "category": "testing",
                "parameters": []
            },
            {
                "name": "check_seo",
                "description": "Basic SEO analysis",
                "category": "testing",
                "parameters": []
            },
            {
                "name": "security_headers_check",
                "description": "Check security headers",
                "category": "testing",
                "parameters": []
            },
            {
                "name": "lighthouse_audit",
                "description": "Run Lighthouse performance audit",
                "category": "testing",
                "parameters": [
                    ExtendedToolParameter("categories", "array", "Audit categories",
                                        default=["performance", "accessibility", "seo"])
                ]
            }
        ]
    
    @staticmethod
    def get_interaction_tools() -> List[Dict[str, Any]]:
        """Advanced interaction tools."""
        return [
            {
                "name": "drag_and_drop",
                "description": "Drag element and drop to target",
                "category": "interaction",
                "parameters": [
                    ExtendedToolParameter("source", "string", "Source element selector", required=True),
                    ExtendedToolParameter("target", "string", "Target element selector", required=True)
                ]
            },
            {
                "name": "right_click",
                "description": "Right-click on element",
                "category": "interaction",
                "parameters": [
                    ExtendedToolParameter("selector", "string", "Element selector", required=True)
                ]
            },
            {
                "name": "double_click",
                "description": "Double-click on element",
                "category": "interaction",
                "parameters": [
                    ExtendedToolParameter("selector", "string", "Element selector", required=True)
                ]
            },
            {
                "name": "press_key",
                "description": "Press keyboard key or combination",
                "category": "interaction",
                "parameters": [
                    ExtendedToolParameter("key", "string", "Key to press", required=True),
                    ExtendedToolParameter("modifiers", "array", "Modifier keys",
                                        enum=["ctrl", "alt", "shift", "meta"])
                ]
            },
            {
                "name": "select_text",
                "description": "Select text on page",
                "category": "interaction",
                "parameters": [
                    ExtendedToolParameter("start_selector", "string", "Start selection"),
                    ExtendedToolParameter("end_selector", "string", "End selection"),
                    ExtendedToolParameter("text", "string", "Text to select")
                ]
            },
            {
                "name": "zoom",
                "description": "Zoom in or out",
                "category": "interaction",
                "parameters": [
                    ExtendedToolParameter("level", "number", "Zoom level (1.0 = 100%)", required=True)
                ]
            }
        ]
    
    @staticmethod
    def get_automation_tools() -> List[Dict[str, Any]]:
        """High-level automation tools."""
        return [
            {
                "name": "login",
                "description": "Automated login detection and execution",
                "category": "automation",
                "parameters": [
                    ExtendedToolParameter("username", "string", "Username/email", required=True),
                    ExtendedToolParameter("password", "string", "Password", required=True),
                    ExtendedToolParameter("auto_detect", "boolean", "Auto-detect login form", default=True)
                ]
            },
            {
                "name": "checkout",
                "description": "Navigate through checkout process",
                "category": "automation",
                "parameters": [
                    ExtendedToolParameter("stop_before_payment", "boolean", "Stop before payment", default=True)
                ]
            },
            {
                "name": "search_and_filter",
                "description": "Search and apply filters",
                "category": "automation",
                "parameters": [
                    ExtendedToolParameter("query", "string", "Search query", required=True),
                    ExtendedToolParameter("filters", "object", "Filters to apply")
                ]
            },
            {
                "name": "paginate",
                "description": "Navigate through pagination",
                "category": "automation",
                "parameters": [
                    ExtendedToolParameter("max_pages", "integer", "Maximum pages to traverse", default=10),
                    ExtendedToolParameter("extract_each", "boolean", "Extract data from each page", default=True)
                ]
            },
            {
                "name": "monitor_changes",
                "description": "Monitor page for changes",
                "category": "automation",
                "parameters": [
                    ExtendedToolParameter("selector", "string", "Element to monitor"),
                    ExtendedToolParameter("interval", "integer", "Check interval in seconds", default=5),
                    ExtendedToolParameter("timeout", "integer", "Total timeout in seconds", default=60)
                ]
            }
        ]
    
    @staticmethod
    def get_cloud_tools() -> List[Dict[str, Any]]:
        """Cloud platform integration tools."""
        return [
            {
                "name": "browserstack_session",
                "description": "Start BrowserStack session",
                "category": "cloud",
                "parameters": [
                    ExtendedToolParameter("browser", "string", "Browser name", required=True),
                    ExtendedToolParameter("os", "string", "Operating system", required=True),
                    ExtendedToolParameter("resolution", "string", "Screen resolution")
                ]
            },
            {
                "name": "sauce_labs_session",
                "description": "Start Sauce Labs session",
                "category": "cloud",
                "parameters": [
                    ExtendedToolParameter("platform", "string", "Platform", required=True),
                    ExtendedToolParameter("browser_version", "string", "Browser version")
                ]
            },
            {
                "name": "lambda_test_session",
                "description": "Start LambdaTest session",
                "category": "cloud",
                "parameters": [
                    ExtendedToolParameter("build_name", "string", "Build name"),
                    ExtendedToolParameter("test_name", "string", "Test name")
                ]
            }
        ]
    
    @classmethod
    def get_all_extended_tools(cls) -> List[Dict[str, Any]]:
        """Get all extended tools."""
        all_tools = []
        all_tools.extend(cls.get_form_tools())
        all_tools.extend(cls.get_navigation_tools())
        all_tools.extend(cls.get_data_tools())
        all_tools.extend(cls.get_testing_tools())
        all_tools.extend(cls.get_interaction_tools())
        all_tools.extend(cls.get_automation_tools())
        all_tools.extend(cls.get_cloud_tools())
        return all_tools
    
    @classmethod
    def count_tools(cls) -> Dict[str, int]:
        """Count tools by category."""
        return {
            "forms": len(cls.get_form_tools()),
            "navigation": len(cls.get_navigation_tools()),
            "data": len(cls.get_data_tools()),
            "testing": len(cls.get_testing_tools()),
            "interaction": len(cls.get_interaction_tools()),
            "automation": len(cls.get_automation_tools()),
            "cloud": len(cls.get_cloud_tools()),
            "total": len(cls.get_all_extended_tools())
        }
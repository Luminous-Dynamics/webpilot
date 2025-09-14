"""
MCP Resources management for WebPilot.

This module handles resource management for the MCP interface,
including session data, screenshots, and execution logs.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import base64
from pathlib import Path


@dataclass
class ResourceMetadata:
    """Metadata for a resource."""
    created_at: datetime
    updated_at: datetime
    size_bytes: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionResource:
    """Represents a WebPilot session resource."""
    session_id: str
    start_time: datetime
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    actions_performed: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Optional[ResourceMetadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "current_url": self.current_url,
            "page_title": self.page_title,
            "screenshots": self.screenshots,
            "actions_performed": self.actions_performed,
            "metadata": self.metadata.__dict__ if self.metadata else None
        }
    
    def to_mcp_resource(self) -> Dict[str, Any]:
        """Convert to MCP resource format."""
        return {
            "uri": f"webpilot://session/{self.session_id}",
            "name": f"Session {self.session_id}",
            "description": f"WebPilot session started at {self.start_time.isoformat()}",
            "mimeType": "application/json",
            "content": self.to_dict()
        }


@dataclass
class ScreenshotResource:
    """Represents a screenshot resource."""
    session_id: str
    screenshot_id: str
    path: Path
    timestamp: datetime
    url: str
    page_title: Optional[str] = None
    metadata: Optional[ResourceMetadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "screenshot_id": self.screenshot_id,
            "path": str(self.path),
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
            "page_title": self.page_title,
            "metadata": self.metadata.__dict__ if self.metadata else None
        }
    
    def to_mcp_resource(self) -> Dict[str, Any]:
        """Convert to MCP resource format."""
        return {
            "uri": f"webpilot://screenshot/{self.session_id}/{self.screenshot_id}",
            "name": f"Screenshot {self.screenshot_id}",
            "description": f"Screenshot of {self.url} at {self.timestamp.isoformat()}",
            "mimeType": "image/png",
            "content": self.to_dict()
        }
    
    def get_base64_content(self) -> Optional[str]:
        """Get screenshot content as base64."""
        if self.path.exists():
            with open(self.path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        return None


@dataclass
class LogResource:
    """Represents an execution log resource."""
    session_id: str
    log_entries: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Optional[ResourceMetadata] = None
    
    def add_entry(self, level: str, message: str, **kwargs):
        """Add a log entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.log_entries.append(entry)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "log_entries": self.log_entries,
            "metadata": self.metadata.__dict__ if self.metadata else None
        }
    
    def to_mcp_resource(self) -> Dict[str, Any]:
        """Convert to MCP resource format."""
        return {
            "uri": f"webpilot://logs/{self.session_id}",
            "name": f"Logs for session {self.session_id}",
            "description": f"Execution logs for WebPilot session {self.session_id}",
            "mimeType": "application/json",
            "content": self.to_dict()
        }


class WebPilotResources:
    """
    Manages resources for WebPilot MCP interface.
    
    This class handles creation, storage, and retrieval of resources
    like sessions, screenshots, and logs.
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize resources manager.
        
        Args:
            storage_dir: Directory for storing resources (screenshots, logs, etc.)
        """
        self.storage_dir = storage_dir or Path.home() / ".webpilot" / "resources"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.sessions: Dict[str, SessionResource] = {}
        self.screenshots: Dict[str, List[ScreenshotResource]] = {}
        self.logs: Dict[str, LogResource] = {}
    
    def create_session(self, session_id: str) -> SessionResource:
        """
        Create a new session resource.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Created session resource
        """
        session = SessionResource(
            session_id=session_id,
            start_time=datetime.now(),
            metadata=ResourceMetadata(
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
        self.sessions[session_id] = session
        
        # Initialize related resources
        self.screenshots[session_id] = []
        self.logs[session_id] = LogResource(session_id=session_id)
        
        return session
    
    def update_session(self, session_id: str, **kwargs) -> Optional[SessionResource]:
        """
        Update session information.
        
        Args:
            session_id: Session to update
            **kwargs: Fields to update
            
        Returns:
            Updated session or None if not found
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            if session.metadata:
                session.metadata.updated_at = datetime.now()
            return session
        return None
    
    def add_screenshot(self, session_id: str, screenshot_path: Path,
                      url: str, page_title: Optional[str] = None) -> Optional[ScreenshotResource]:
        """
        Add a screenshot resource.
        
        Args:
            session_id: Session ID
            screenshot_path: Path to screenshot file
            url: URL where screenshot was taken
            page_title: Optional page title
            
        Returns:
            Created screenshot resource or None if session not found
        """
        if session_id not in self.sessions:
            return None
        
        screenshot_id = f"screenshot_{len(self.screenshots[session_id])}"
        screenshot = ScreenshotResource(
            session_id=session_id,
            screenshot_id=screenshot_id,
            path=screenshot_path,
            timestamp=datetime.now(),
            url=url,
            page_title=page_title,
            metadata=ResourceMetadata(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                size_bytes=screenshot_path.stat().st_size if screenshot_path.exists() else None
            )
        )
        
        self.screenshots[session_id].append(screenshot)
        self.sessions[session_id].screenshots.append(str(screenshot_path))
        
        return screenshot
    
    def add_action(self, session_id: str, action: str, **details) -> bool:
        """
        Add an action to session history.
        
        Args:
            session_id: Session ID
            action: Action name
            **details: Action details
            
        Returns:
            True if added, False if session not found
        """
        if session_id not in self.sessions:
            return False
        
        action_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            **details
        }
        self.sessions[session_id].actions_performed.append(action_entry)
        
        # Also log the action
        if session_id in self.logs:
            self.logs[session_id].add_entry("INFO", f"Action: {action}", **details)
        
        return True
    
    def get_session_resources(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all resources for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of MCP resources
        """
        resources = []
        
        # Add session resource
        if session_id in self.sessions:
            resources.append(self.sessions[session_id].to_mcp_resource())
        
        # Add screenshot resources
        if session_id in self.screenshots:
            for screenshot in self.screenshots[session_id]:
                resources.append(screenshot.to_mcp_resource())
        
        # Add log resource
        if session_id in self.logs:
            resources.append(self.logs[session_id].to_mcp_resource())
        
        return resources
    
    def get_all_resources(self) -> List[Dict[str, Any]]:
        """
        Get all available resources.
        
        Returns:
            List of all MCP resources
        """
        resources = []
        for session_id in self.sessions:
            resources.extend(self.get_session_resources(session_id))
        return resources
    
    def get_resource_by_uri(self, uri: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific resource by URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content or None if not found
        """
        # Parse URI format: webpilot://type/session_id/[resource_id]
        if not uri.startswith("webpilot://"):
            return None
        
        parts = uri[11:].split('/')  # Remove "webpilot://" prefix
        if len(parts) < 2:
            return None
        
        resource_type = parts[0]
        session_id = parts[1]
        
        if resource_type == "session":
            if session_id in self.sessions:
                return self.sessions[session_id].to_mcp_resource()
        
        elif resource_type == "screenshot" and len(parts) > 2:
            screenshot_id = parts[2]
            if session_id in self.screenshots:
                for screenshot in self.screenshots[session_id]:
                    if screenshot.screenshot_id == screenshot_id:
                        resource = screenshot.to_mcp_resource()
                        # Include base64 content for screenshots
                        base64_content = screenshot.get_base64_content()
                        if base64_content:
                            resource["content"]["base64"] = base64_content
                        return resource
        
        elif resource_type == "logs":
            if session_id in self.logs:
                return self.logs[session_id].to_mcp_resource()
        
        return None
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up resources for a session.
        
        Args:
            session_id: Session to clean up
            
        Returns:
            True if cleaned up, False if not found
        """
        if session_id not in self.sessions:
            return False
        
        # Clean up screenshots (optionally delete files)
        if session_id in self.screenshots:
            for screenshot in self.screenshots[session_id]:
                if screenshot.path.exists():
                    # Optionally delete screenshot files
                    # screenshot.path.unlink()
                    pass
            del self.screenshots[session_id]
        
        # Clean up logs
        if session_id in self.logs:
            del self.logs[session_id]
        
        # Clean up session
        del self.sessions[session_id]
        
        return True
    
    def export_session_data(self, session_id: str, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Export all session data to a JSON file.
        
        Args:
            session_id: Session to export
            output_path: Optional output path
            
        Returns:
            Path to exported file or None if session not found
        """
        if session_id not in self.sessions:
            return None
        
        if not output_path:
            output_path = self.storage_dir / f"session_{session_id}_export.json"
        
        export_data = {
            "session": self.sessions[session_id].to_dict(),
            "screenshots": [s.to_dict() for s in self.screenshots.get(session_id, [])],
            "logs": self.logs[session_id].to_dict() if session_id in self.logs else None,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return output_path
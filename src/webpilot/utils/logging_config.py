"""
Logging configuration for WebPilot.

This module provides centralized logging configuration with support for:
- Console and file output
- Structured logging
- Log rotation
- Performance metrics
- Error tracking
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.
        
        Args:
            record: The log record to format
            
        Returns:
            Colored log string
        """
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        result = super().format(record)
        
        # Reset levelname for other handlers
        record.levelname = levelname
        
        return result


class WebPilotLogger:
    """Central logger configuration for WebPilot."""
    
    _instance: Optional['WebPilotLogger'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'WebPilotLogger':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger configuration."""
        if not self._initialized:
            self.loggers: Dict[str, logging.Logger] = {}
            self.handlers: Dict[str, logging.Handler] = {}
            self.log_dir = Path.home() / '.webpilot' / 'logs'
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True
    
    def setup_logging(
        self,
        level: str = 'INFO',
        console: bool = True,
        file: bool = True,
        structured: bool = False,
        log_file: Optional[Path] = None
    ) -> None:
        """Set up logging configuration.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console: Enable console output
            file: Enable file output
            structured: Use structured JSON logging
            log_file: Custom log file path
        """
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        root_logger.handlers = []
        
        # Console handler
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            
            if structured:
                console_formatter = StructuredFormatter()
            else:
                console_formatter = ColoredFormatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
            self.handlers['console'] = console_handler
        
        # File handler
        if file:
            if log_file is None:
                log_file = self.log_dir / f"webpilot_{datetime.now():%Y%m%d}.log"
            
            # Use rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            
            if structured:
                file_formatter = StructuredFormatter()
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            self.handlers['file'] = file_handler
        
        # Error file handler (always enabled for ERROR and above)
        error_file = self.log_dir / f"webpilot_errors_{datetime.now():%Y%m%d}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n%(exc_info)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(error_handler)
        self.handlers['error'] = error_handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Configured logger instance
        """
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def log_performance(
        self,
        logger_name: str,
        operation: str,
        duration: float,
        **kwargs
    ) -> None:
        """Log performance metrics.
        
        Args:
            logger_name: Name of the logger to use
            operation: Name of the operation
            duration: Duration in seconds
            **kwargs: Additional metrics
        """
        logger = self.get_logger(logger_name)
        metrics = {
            'operation': operation,
            'duration_ms': duration * 1000,
            **kwargs
        }
        logger.info(f"Performance: {operation}", extra={'extra_fields': metrics})
    
    def log_error(
        self,
        logger_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log error with context.
        
        Args:
            logger_name: Name of the logger to use
            error: The exception to log
            context: Additional context information
        """
        logger = self.get_logger(logger_name)
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        logger.error(
            f"Error occurred: {error}",
            exc_info=True,
            extra={'extra_fields': error_info}
        )
    
    def set_log_level(self, level: str, logger_name: Optional[str] = None) -> None:
        """Change log level dynamically.
        
        Args:
            level: New log level
            logger_name: Specific logger to update (None for root)
        """
        log_level = getattr(logging, level.upper())
        
        if logger_name:
            logger = self.get_logger(logger_name)
            logger.setLevel(log_level)
        else:
            logging.getLogger().setLevel(log_level)
            for handler in self.handlers.values():
                if handler.name != 'error':  # Keep error handler at ERROR level
                    handler.setLevel(log_level)


# Global logger instance
logger_config = WebPilotLogger()


def setup_logging(**kwargs) -> None:
    """Convenience function to set up logging.
    
    Args:
        **kwargs: Arguments to pass to WebPilotLogger.setup_logging()
    """
    logger_config.setup_logging(**kwargs)


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logger_config.get_logger(name)
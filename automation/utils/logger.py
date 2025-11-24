"""
Structured logging utility for automation pipeline.

Provides simple, human-readable logging with structured output.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


class AutomationLogger:
    """
    Structured logger for automation pipeline.
    
    Provides:
    - Simple, human-readable format
    - Structured output
    - File and console logging
    - Error tracking
    """
    
    def __init__(self, name: str, log_dir: Path = None):
        """
        Initialize logger.
        
        Args:
            name: Logger name (e.g., 'pipeline', 'injuries')
            log_dir: Directory for log files (optional)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (DEBUG and above)
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data."""
        if kwargs:
            message = f"{message} | {self._format_data(kwargs)}"
        self.logger.info(message)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data."""
        if kwargs:
            message = f"{message} | {self._format_data(kwargs)}"
        self.logger.error(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data."""
        if kwargs:
            message = f"{message} | {self._format_data(kwargs)}"
        self.logger.warning(message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data."""
        if kwargs:
            message = f"{message} | {self._format_data(kwargs)}"
        self.logger.debug(message)
    
    def _format_data(self, data: dict) -> str:
        """Format structured data as key=value pairs."""
        return " | ".join(f"{k}={v}" for k, v in data.items())
    
    def section(self, title: str):
        """Log a section header."""
        separator = "=" * 70
        self.logger.info(f"\n{separator}")
        self.logger.info(f"  {title}")
        self.logger.info(f"{separator}")


def get_logger(name: str, log_dir: Path = None) -> AutomationLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        log_dir: Optional log directory
        
    Returns:
        AutomationLogger instance
    """
    return AutomationLogger(name, log_dir)

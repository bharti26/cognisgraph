import logging
import sys
from typing import Optional, Union
from pathlib import Path
from cognisgraph.config import Config

class CognisGraphLogger:
    """Logger for CognisGraph operations."""
    
    def __init__(self, name: str = "cognisgraph", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if log file is specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def setLevel(self, level: Union[int, str]) -> None:
        """Set the logging level for the logger.
        
        Args:
            level: The logging level to set (can be string or int)
        """
        self.logger.setLevel(level)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, *args, **kwargs)

def get_logger(name: str = "cognisgraph", log_file: Optional[str] = None) -> CognisGraphLogger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        
    Returns:
        A configured CognisGraphLogger instance
    """
    return CognisGraphLogger(name, log_file)

def setup_logging(level: int = logging.DEBUG) -> None:
    """Set up logging configuration.
    
    Args:
        level: Logging level (default: DEBUG)
    """
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Set up specific loggers
    loggers = [
        'cognisgraph',
        'cognisgraph.agents',
        'cognisgraph.core',
        'cognisgraph.nlp',
        'cognisgraph.xai',
        'cognisgraph.visualization'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(console_handler)

__all__ = ['CognisGraphLogger', 'get_logger', 'setup_logging'] 
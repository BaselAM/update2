"""Centralized logging configuration for the application."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level=logging.INFO):
    """Set up consistent logging across the application.

    Args:
        log_level: The minimum logging level to display

    Returns:
        The configured root logger
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create a timestamp-based log filename
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"app_{timestamp}.log"

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # File handler with UTF-8 encoding
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # Log to console if file logging fails
        print(f"Warning: Could not set up file logging: {e}")

    # Configure specific loggers
    module_loggers = {
        'database': log_level,
        'widgets': log_level,
        'gui': log_level,
        'translator': log_level
    }

    for name, level in module_loggers.items():
        module_logger = logging.getLogger(name)
        module_logger.setLevel(level)

    # Log application startup
    logging.info(f"Application started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Log file: {log_file.absolute()}")

    return root_logger


def get_logger(module_name):
    """Get a logger for a specific module.

    Args:
        module_name: Name of the module (e.g., 'database.car_parts_db')

    Returns:
        A configured logger instance
    """
    return logging.getLogger(module_name)
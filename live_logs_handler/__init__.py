"""
Live Logs Handler - Thread-Safe Structured Logging SDK for Jupyter Notebooks.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .handler import (
    ThreadSafeStructuredLogger,
    get_logger,
    start_logging
)

__all__ = [
    "ThreadSafeStructuredLogger",
    "get_logger",
    "start_logging"
]

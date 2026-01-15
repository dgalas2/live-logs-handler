"""
Thread-Safe Structured Logging SDK for Jupyter Notebooks.

Usage in notebook:
    from notebook_logger import NotebookLogger
    logger = NotebookLogger("app.log")
    logger.start()
    
    # Use standard logging or print
    import logging
    logging.info("My message")
    print("Hello world")
"""

import sys
import os
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Any, Dict, Optional
from IPython import get_ipython


LIVE_LOGS_FILE_PATH = "LIVE_LOGS_FILE_PATH"

class ThreadSafeStructuredLogger:
    """Thread-safe structured logger that captures all output from notebook cells."""
    
    def __init__(
        self, 
        log_file: str = "notebook.log",
        buffer_size: int = 1000,
        include_cell_info: bool = True,
        capture_print: bool = False
    ):
        """
        Initialize the logger.
        
        Args:
            log_file: Path to log file
            buffer_size: Size of the log queue buffer
            include_cell_info: Include cell execution context
            capture_print: Capture print statements
        """
        self.log_file = Path(log_file)
        self.include_cell_info = include_cell_info
        self.capture_print = capture_print
        
        # Thread-safe queue for log entries
        self.log_queue = Queue(maxsize=buffer_size)
        self.lock = threading.Lock()
        self.running = False
        self.writer_thread = None
        
        # Cell tracking
        self.current_cell = None
        self.cell_count = 0
        
        # IPython instance
        self.ipython = get_ipython()
        
        # Original stdout/stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Setup Python logging handler
        self.log_handler = None
    
    def start(self):
        """Start capturing logs."""
        with self.lock:
            if self.running:
                print("Logger already running")
                return
            
            self.running = True
            
            # Start background writer thread
            self.writer_thread = threading.Thread(target=self._log_writer, daemon=True)
            self.writer_thread.start()
            
            # Register IPython hooks
            # if self.ipython:
            #     self.ipython.events.register('pre_run_cell', self._pre_run_cell)
            #     self.ipython.events.register('post_run_cell', self._post_run_cell)
            
            # Setup logging handler
            self._setup_logging_handler()
            
            # Capture print statements
            if self.capture_print:
                self._setup_print_capture()
            
            # Log startup
            self._log({
                "severity_text": "INFO",
                "body": "Notebook logger started",
				"timestamp": datetime.utcnow().isoformat() + "Z",
                "log_file": str(self.log_file)
            })
            
            print(f"Structured logging started: {self.log_file}")
    
    def stop(self):
        """Stop capturing logs."""
        with self.lock:
            if not self.running:
                return
            
            # Log shutdown
            self._log({
                "severity_text": "INFO",
                "body": "Notebook logger stopped",
                "total_cells": self.cell_count,
				"timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            self.running = False
            
            # Unregister hooks
            # if self.ipython:
            #     self.ipython.events.unregister('pre_run_cell', self._pre_run_cell)
            #     self.ipython.events.unregister('post_run_cell', self._post_run_cell)
            
            # Remove logging handler
            if self.log_handler:
                logging.getLogger().removeHandler(self.log_handler)
            
            # Restore stdout/stderr
            if self.capture_print:
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr
            
            # Wait for queue to empty
            self.log_queue.join()
            
            print(f"Structured logging stopped")
    
    def _setup_logging_handler(self):
        """Setup Python logging handler to capture logging.* calls."""

        # Setup basic logging to stdout first
        logging.basicConfig(
            level=logging.INFO,
        )
        
        class StructuredLogHandler(logging.Handler):
            def __init__(self, logger_instance):
                super().__init__()
                self.logger_instance = logger_instance
            
            def emit(self, record):
                log_entry = {
                    "severity_text": record.levelname,
                    "body": self.format(record),
                    "logger_name": record.name,
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
					"timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                
                self.logger_instance._log(log_entry)
        
        self.log_handler = StructuredLogHandler(self)
        logging.getLogger().addHandler(self.log_handler)
    
    def _setup_print_capture(self):
        """Setup print statement capture."""
        class PrintCapture:
            def __init__(self, original, logger_instance, stream_name):
                self.original = original
                self.logger_instance = logger_instance
                self.stream_name = stream_name
            
            def write(self, text):
                # Write to original
                self.original.write(text)
                self.original.flush()
                
                # Log if not empty
                if text and text.strip():
                    self.logger_instance._log({
                        "severity_text": "ERROR" if self.stream_name == "stderr" else "INFO",
                        "body": text.rstrip(),
                        "source": "print",
                        "stream": self.stream_name,
						"timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                
                return len(text)
            
            def flush(self):
                self.original.flush()
        
        sys.stdout = PrintCapture(self.original_stdout, self, "stdout")
        sys.stderr = PrintCapture(self.original_stderr, self, "stderr")
    
    def _pre_run_cell(self, info):
        """Called before cell execution."""
        self.cell_count += 1
        self.current_cell = {
            "cell_number": self.cell_count,
            "cell_id": getattr(info, 'cell_id', None),
            "start_time": datetime.utcnow().isoformat()
        }
        
        if self.include_cell_info:
            self._log({
                "severity_text": "DEBUG",
                "body": f"Cell {self.cell_count} execution started",
                "event": "cell_start",
                "cell_preview": info.raw_cell[:100] if info.raw_cell else "",
				"timestamp": datetime.utcnow().isoformat() + "Z"
            })
    
    def _post_run_cell(self, result):
        """Called after cell execution."""
        if self.include_cell_info and self.current_cell:
            log_entry = {
                "severity_text": "ERROR" if result.error_in_exec else "DEBUG",
                "body": f"Cell {self.cell_count} execution completed",
                "event": "cell_end",
                "success": result.success,
				"timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            if result.error_in_exec:
                log_entry["error"] = str(result.error_in_exec)
            
            self._log(log_entry)
        
        self.current_cell = None
    
    def _log(self, entry: Dict[str, Any]):
        """Add log entry to queue."""
        if not self.running:
            return
        
        # Add standard fields
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
        entry["thread_id"] = threading.get_ident()
        entry["thread_name"] = threading.current_thread().name
        
        # Add cell context if available
        if self.include_cell_info and self.current_cell:
            entry["cell_number"] = self.current_cell["cell_number"]
            if self.current_cell.get("cell_id"):
                entry["cell_id"] = self.current_cell["cell_id"]
        
        # Add to queue (non-blocking)
        try:
            self.log_queue.put_nowait(entry)
        except:
            # Queue full, skip this entry
            pass
    
    def _log_writer(self):
        """Background thread that writes logs to file."""
        with open(self.log_file, 'a') as f:
            while self.running or not self.log_queue.empty():
                try:
                    # Get log entry from queue (with timeout)
                    entry = self.log_queue.get(timeout=0.1)
                    
                    # Format and write
                    line = json.dumps(entry, default=str)
                    
                    f.write(line + "\n")
                    f.flush()
                    
                    self.log_queue.task_done()
                except:
                    continue
    
    def log(self, level: str, message: str, **kwargs):
        """Manually log a structured message."""
        entry = {
            "severity_text": level.upper(),
            "body": message,
            **kwargs
        }
        self._log(entry)


# Singleton instance
_logger_instance: Optional[ThreadSafeStructuredLogger] = None


def get_logger(log_file: str = "notebook.log", **kwargs) -> ThreadSafeStructuredLogger:
    """Get or create the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ThreadSafeStructuredLogger(log_file, **kwargs)
    return _logger_instance


def start_logging(log_file: str = "notebook.log", **kwargs):
    """Quick start function."""

    json_file_path = os.getenv(LIVE_LOGS_FILE_PATH, "")
    if json_file_path == "":
        print("Environment variable LIVE_LOGS_FILE_PATH not set. Logging not started.")
        return None

    logger = get_logger(json_file_path, **kwargs)
    logger.start()
    return logger

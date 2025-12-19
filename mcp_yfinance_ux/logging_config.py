"""Async logging configuration using QueueHandler

Offloads logging to a background thread to avoid blocking I/O operations.
All modules should use get_logger() instead of logging.getLogger() directly.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from queue import Queue


class AsyncLoggingManager:
    """Manages async logging state without using global variables"""

    def __init__(self) -> None:
        self.log_queue: Queue[logging.LogRecord] = Queue(-1)
        self.queue_handler: logging.handlers.QueueHandler | None = None
        self.listener: logging.handlers.QueueListener | None = None

    def setup(self, log_file: Path | None = None, level: int = logging.INFO) -> None:
        """Set up async logging with QueueHandler and QueueListener

        This should be called once at application startup.

        Args:
            log_file: Optional path to log file. If None, only logs to stderr.
            level: Logging level (default: INFO)
        """
        # Create handlers that will run in background thread
        handlers: list[logging.Handler] = []

        # Console handler (stderr)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
        )
        handlers.append(console_handler)

        # File handler (if log_file specified)
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
            )
            handlers.append(file_handler)

        # Create QueueListener to process logs in background thread
        self.listener = logging.handlers.QueueListener(
            self.log_queue, *handlers, respect_handler_level=True
        )
        self.listener.start()

        # Create QueueHandler for main thread
        self.queue_handler = logging.handlers.QueueHandler(self.log_queue)

        # Configure root logger to use QueueHandler
        root = logging.getLogger()
        root.setLevel(level)
        root.handlers.clear()
        root.addHandler(self.queue_handler)

        # If we're at DEBUG, suppress third-party DEBUG spam by setting them to INFO
        if level < logging.INFO:
            logging.getLogger("yfinance").setLevel(logging.INFO)
            logging.getLogger("urllib3").setLevel(logging.INFO)
            logging.getLogger("requests").setLevel(logging.INFO)
            logging.getLogger("peewee").setLevel(logging.INFO)
            logging.getLogger("sse_starlette.sse").setLevel(logging.INFO)
            logging.getLogger("mcp.server.sse").setLevel(logging.INFO)

    def shutdown(self) -> None:
        """Shut down async logging (call on application exit)

        Ensures all queued log records are processed before stopping.
        """
        if self.listener is not None:
            # QueueListener.stop() waits for queue to be processed,
            # but we ensure the queue is empty first for extra safety
            self.log_queue.join()  # Wait for all tasks to be processed
            self.listener.stop()
            self.listener = None


# Singleton instance
_manager = AsyncLoggingManager()


def setup_async_logging(log_file: Path | None = None, level: int = logging.INFO) -> None:
    """Set up async logging - convenience wrapper around manager.setup()"""
    _manager.setup(log_file, level)


def shutdown_async_logging() -> None:
    """Shut down async logging - convenience wrapper around manager.shutdown()"""
    _manager.shutdown()


def get_logger(name: str) -> logging.Logger:
    """Get a logger configured for async logging

    Use this instead of logging.getLogger() to ensure async behavior.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

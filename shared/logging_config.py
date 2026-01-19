"""
Logging Configuration for FibreFlow Agent Workforce

Provides structured logging with:
- JSON formatting for production
- Colored console output for development
- Automatic request tracking
- Performance metrics
- Error aggregation
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
import os


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add custom fields
        if hasattr(record, "agent_name"):
            log_data["agent_name"] = record.agent_name
        if hasattr(record, "skill_name"):
            log_data["skill_name"] = record.skill_name
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "tokens_used"):
            log_data["tokens_used"] = record.tokens_used

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console output for development"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    name: str = "fibreflow",
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    json_logs: bool = False,
    console: bool = True,
) -> logging.Logger:
    """
    Setup logging configuration

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: logs/)
        json_logs: Use JSON formatting for file logs
        console: Enable console output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()  # Clear existing handlers

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        if os.getenv("ENVIRONMENT") == "production":
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )

        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_dir is None:
        log_dir = Path("logs")

    log_dir.mkdir(parents=True, exist_ok=True)

    # Main log file (rotated daily)
    log_file = log_dir / f"{name}.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    if json_logs:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )

    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Error log file (errors only)
    error_file = log_dir / f"{name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    return logger


def get_agent_logger(agent_name: str) -> logging.Logger:
    """
    Get a logger configured for a specific agent

    Args:
        agent_name: Name of the agent

    Returns:
        Logger instance
    """
    logger = logging.getLogger(f"fibreflow.agent.{agent_name}")

    # Add agent name to all log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.agent_name = agent_name
        return record

    logging.setLogRecordFactory(record_factory)

    return logger


def get_skill_logger(skill_name: str) -> logging.Logger:
    """
    Get a logger configured for a specific skill

    Args:
        skill_name: Name of the skill

    Returns:
        Logger instance
    """
    logger = logging.getLogger(f"fibreflow.skill.{skill_name}")

    # Add skill name to all log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.skill_name = skill_name
        return record

    logging.setLogRecordFactory(record_factory)

    return logger


class PerformanceLogger:
    """Context manager for logging performance metrics"""

    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.debug(f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000

        if exc_type is None:
            self.logger.info(
                f"Completed: {self.operation}",
                extra={"duration_ms": duration}
            )
        else:
            self.logger.error(
                f"Failed: {self.operation}",
                extra={"duration_ms": duration},
                exc_info=True
            )


# Default configuration
default_logger = setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "false").lower() == "true",
)


if __name__ == "__main__":
    # Test logging configuration
    logger = setup_logging("test", level="DEBUG")

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Test performance logging
    with PerformanceLogger(logger, "test_operation"):
        import time
        time.sleep(0.1)

    print("\n✅ Logging configuration test complete")
    print(f"Log files created in: logs/")

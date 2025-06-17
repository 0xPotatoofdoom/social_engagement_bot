"""
Advanced Logging Configuration for X Engagement Bot

Provides structured logging with component separation, rotation, and email tracking.
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import structlog


class EmailEventLogger:
    """Dedicated logger for email events and delivery tracking"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_file = log_dir / "email_events.log"
        self.logger = self._setup_email_logger()
    
    def _setup_email_logger(self) -> logging.Logger:
        """Configure dedicated email event logger"""
        logger = logging.getLogger("email_events")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_email_attempt(self, to_email: str, subject: str, alert_type: str, 
                         opportunity_count: int, success: bool = True, 
                         error: str = None, smtp_response: str = None):
        """Log email sending attempt with key details"""
        event_data = {
            "event": "email_send",
            "timestamp": datetime.now().isoformat(),
            "to_email": to_email,
            "subject": subject[:100],  # Truncate long subjects
            "alert_type": alert_type,
            "opportunity_count": opportunity_count,
            "success": success,
            "error": error,
            "smtp_response": smtp_response
        }
        
        if success:
            self.logger.info(f"EMAIL_SENT: {json.dumps(event_data)}")
        else:
            self.logger.error(f"EMAIL_FAILED: {json.dumps(event_data)}")
    
    def log_email_bounce(self, to_email: str, bounce_reason: str):
        """Log email bounce events"""
        event_data = {
            "event": "email_bounce",
            "timestamp": datetime.now().isoformat(),
            "to_email": to_email,
            "bounce_reason": bounce_reason
        }
        self.logger.warning(f"EMAIL_BOUNCED: {json.dumps(event_data)}")


class ComponentLogger:
    """Component-specific logger with structured output"""
    
    def __init__(self, component_name: str, log_dir: Path):
        self.component_name = component_name
        self.log_dir = log_dir
        self.log_file = log_dir / f"{component_name}.log"
        self.logger = self._setup_component_logger()
    
    def _setup_component_logger(self) -> structlog.stdlib.BoundLogger:
        """Configure component-specific structured logger"""
        # Standard library logger for file output
        stdlib_logger = logging.getLogger(f"component.{self.component_name}")
        stdlib_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        stdlib_logger.handlers.clear()
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=20*1024*1024,  # 20MB
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        stdlib_logger.addHandler(handler)
        
        # Return structured logger bound to component
        return structlog.get_logger(self.component_name)


class LoggingManager:
    """Centralized logging management with rotation and component separation"""
    
    def __init__(self, base_log_dir: str = "logs"):
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(exist_ok=True)
        
        # Component loggers
        self.component_loggers: Dict[str, ComponentLogger] = {}
        self.email_logger: Optional[EmailEventLogger] = None
        
        self._rotate_logs_on_startup()
        self._configure_structlog()
        self._setup_main_logger()
    
    def _rotate_logs_on_startup(self):
        """Rotate existing logs on application startup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dir = self.base_log_dir / "archive" / timestamp
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Move existing logs to archive
        for log_file in self.base_log_dir.glob("*.log"):
            if log_file.is_file():
                archive_path = archive_dir / log_file.name
                log_file.rename(archive_path)
                print(f"Archived log: {log_file.name} -> {archive_path}")
        
        # Clean up old archives (keep last 30 startup sessions)
        archive_dirs = sorted(
            [d for d in (self.base_log_dir / "archive").glob("*") if d.is_dir()]
        )
        if len(archive_dirs) > 30:
            for old_dir in archive_dirs[:-30]:
                import shutil
                shutil.rmtree(old_dir)
                print(f"Cleaned up old archive: {old_dir}")
    
    def _configure_structlog(self):
        """Configure structlog for structured logging"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def _setup_main_logger(self):
        """Setup main application logger"""
        self.main_log_file = self.base_log_dir / "x_engagement_bot.log"
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for persistence
        file_handler = logging.handlers.RotatingFileHandler(
            self.main_log_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    def get_component_logger(self, component_name: str) -> structlog.stdlib.BoundLogger:
        """Get or create component-specific logger"""
        if component_name not in self.component_loggers:
            self.component_loggers[component_name] = ComponentLogger(
                component_name, self.base_log_dir
            )
        return self.component_loggers[component_name].logger
    
    def get_email_logger(self) -> EmailEventLogger:
        """Get email event logger"""
        if self.email_logger is None:
            self.email_logger = EmailEventLogger(self.base_log_dir)
        return self.email_logger
    
    def log_startup_info(self):
        """Log application startup information"""
        main_logger = structlog.get_logger("startup")
        main_logger.info(
            "x_engagement_bot_starting",
            timestamp=datetime.now().isoformat(),
            log_dir=str(self.base_log_dir),
            components_available=[
                "monitoring", "email_alerts", "x_api", "claude_api", 
                "strategic_accounts", "opportunity_detection"
            ]
        )


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def setup_logging(log_dir: str = "logs") -> LoggingManager:
    """Setup and configure logging system"""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager(log_dir)
        _logging_manager.log_startup_info()
    return _logging_manager


def get_component_logger(component_name: str) -> structlog.stdlib.BoundLogger:
    """Get component-specific logger (convenience function)"""
    if _logging_manager is None:
        setup_logging()
    return _logging_manager.get_component_logger(component_name)


def get_email_logger() -> EmailEventLogger:
    """Get email event logger (convenience function)"""
    if _logging_manager is None:
        setup_logging()
    return _logging_manager.get_email_logger()


# Pre-configured component loggers for common use
def get_monitoring_logger():
    """Get monitoring component logger"""
    return get_component_logger("monitoring")


def get_x_api_logger():
    """Get X API component logger"""
    return get_component_logger("x_api")


def get_claude_api_logger():
    """Get Claude API component logger"""
    return get_component_logger("claude_api")


def get_strategic_accounts_logger():
    """Get strategic accounts component logger"""
    return get_component_logger("strategic_accounts")


def get_opportunity_detection_logger():
    """Get opportunity detection component logger"""
    return get_component_logger("opportunity_detection")
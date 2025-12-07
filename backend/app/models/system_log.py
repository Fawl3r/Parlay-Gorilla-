"""
System Log model for API and error tracking.

Stores logs from external API calls, internal errors, and system events.
Enables admin monitoring without external log aggregation services.
"""

from sqlalchemy import Column, String, DateTime, Index, Text, JSON
from sqlalchemy.sql import func
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID


class LogLevel(str, enum.Enum):
    """Log level enumeration"""
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class LogSource(str, enum.Enum):
    """Log source enumeration"""
    odds_api = "odds_api"
    sportsradar = "sportsradar"
    espn_scraper = "espn_scraper"
    openai = "openai"
    internal = "internal"
    scheduler = "scheduler"
    prediction_resolver = "prediction_resolver"
    webhook = "webhook"


class SystemLog(Base):
    """
    System log entry for monitoring and debugging.
    
    Captures:
    - External API call results (Odds API, SportsRadar, OpenAI)
    - Internal errors and warnings
    - Background job status
    - Webhook events
    """
    
    __tablename__ = "system_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Log classification
    source = Column(String(50), nullable=False, index=True)
    level = Column(String(20), default=LogLevel.info.value, nullable=False, index=True)
    
    # Log content
    message = Column(Text, nullable=False)
    
    # Structured metadata
    # e.g., {"endpoint": "/v4/sports", "status_code": 200, "duration_ms": 150}
    # Note: Using 'metadata_' as Python attribute name because 'metadata' is reserved in SQLAlchemy
    # Using JSON instead of JSONB for SQLite compatibility
    metadata_ = Column("metadata", JSON, nullable=True)
    
    # Error details (for error/critical levels)
    error_type = Column(String(255), nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Request context (if applicable)
    request_id = Column(String(64), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes for efficient log queries
    __table_args__ = (
        Index("idx_system_logs_source_level", "source", "level"),
        Index("idx_system_logs_source_date", "source", "created_at"),
        Index("idx_system_logs_level_date", "level", "created_at"),
    )
    
    def __repr__(self):
        return f"<SystemLog(source={self.source}, level={self.level}, msg={self.message[:50]}...)>"
    
    @classmethod
    def log(cls, source: str, level: str, message: str, **kwargs):
        """
        Factory method to create a log entry.
        
        Usage:
            log = SystemLog.log("odds_api", "info", "Fetched NFL odds", 
                               metadata={"games": 16, "duration_ms": 234})
        """
        return cls(
            source=source,
            level=level,
            message=message,
            metadata_=kwargs.get("metadata"),
            error_type=kwargs.get("error_type"),
            stack_trace=kwargs.get("stack_trace"),
            request_id=kwargs.get("request_id"),
        )


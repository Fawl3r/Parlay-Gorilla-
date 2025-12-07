"""
Feature Flag model for feature toggles.

Allows admin control over feature availability without code deployments.
"""

from sqlalchemy import Column, String, DateTime, Index, Boolean, Text
from sqlalchemy import JSON
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class FeatureFlag(Base):
    """
    Feature flag for controlling feature availability.
    
    Use cases:
    - Toggle Upset Finder access
    - Enable/disable high-leg parlays (15-20 legs)
    - Roll out beta features gradually
    - Emergency feature kill switches
    """
    
    __tablename__ = "feature_flags"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Flag identification
    key = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=True)  # Human-readable name
    description = Column(Text, nullable=True)
    
    # Flag state
    enabled = Column(Boolean, default=False, nullable=False)
    
    # Targeting (optional - for future user-specific flags)
    # e.g., {"plans": ["elite"], "roles": ["admin"], "user_ids": [...]}
    targeting_rules = Column(JSON, nullable=True)
    
    # Metadata
    category = Column(String(50), nullable=True)  # "beta", "premium", "experimental"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_feature_flags_enabled", "enabled"),
        Index("idx_feature_flags_category", "category"),
    )
    
    def __repr__(self):
        status = "ON" if self.enabled else "OFF"
        return f"<FeatureFlag(key={self.key}, {status})>"
    
    def is_enabled_for_user(self, user) -> bool:
        """
        Check if feature is enabled for a specific user.
        
        Checks global enabled state first, then targeting rules.
        """
        if not self.enabled:
            return False
        
        if not self.targeting_rules:
            return True
        
        # Check plan targeting
        if "plans" in self.targeting_rules:
            if user.plan not in self.targeting_rules["plans"]:
                return False
        
        # Check role targeting
        if "roles" in self.targeting_rules:
            if user.role not in self.targeting_rules["roles"]:
                return False
        
        # Check specific user targeting
        if "user_ids" in self.targeting_rules:
            if str(user.id) not in self.targeting_rules["user_ids"]:
                return False
        
        return True


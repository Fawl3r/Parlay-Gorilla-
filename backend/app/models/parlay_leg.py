"""Parlay leg model for settlement tracking."""

from __future__ import annotations

import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class ParlayLeg(Base):
    """Parlay leg model for tracking individual leg settlement."""
    
    __tablename__ = "parlay_legs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    parlay_id = Column(GUID(), ForeignKey("parlays.id", ondelete="CASCADE"), nullable=True, index=True)
    saved_parlay_id = Column(GUID(), ForeignKey("saved_parlays.id", ondelete="CASCADE"), nullable=True, index=True)
    game_id = Column(GUID(), ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    
    market_type = Column(String, nullable=False)  # h2h, spreads, totals
    selection = Column(String, nullable=False)  # team name, home/away, over/under
    line = Column(Numeric, nullable=True)  # spread/total line
    price = Column(String, nullable=True)  # American odds
    
    status = Column(String, nullable=False, server_default="PENDING")  # PENDING, LIVE, WON, LOST, PUSH, VOID
    result_reason = Column(String, nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    parlay = relationship("Parlay", backref="parlay_legs")
    saved_parlay = relationship("SavedParlay", backref="parlay_legs")
    game = relationship("Game", backref="parlay_legs")
    
    # Indexes
    __table_args__ = (
        Index("idx_parlay_legs_parlay_status", "parlay_id", "status"),
        Index("idx_parlay_legs_saved_parlay_status", "saved_parlay_id", "status"),
        Index("idx_parlay_legs_game_status", "game_id", "status"),
        Index("idx_parlay_legs_status_settled", "status", "settled_at"),
    )
    
    def __repr__(self):
        return f"<ParlayLeg(id={self.id}, game_id={self.game_id}, status={self.status})>"

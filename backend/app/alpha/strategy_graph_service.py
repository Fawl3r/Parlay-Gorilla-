"""
Strategy Graph Service: strategies as nodes, edges = interaction strength.

Updates graph weights from contribution success; discovers combinations of signals
producing strongest edge. Persists graph state in alpha_strategy_nodes and alpha_strategy_edges.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alpha_strategy_node import AlphaStrategyNode
from app.models.alpha_strategy_edge import AlphaStrategyEdge

logger = logging.getLogger(__name__)


class StrategyGraphService:
    """
    Manages strategy graph: nodes (predictive signals) and edges (interaction strength).
    Weights updated based on contribution success; state persisted in DB.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_node(self, signal_name: str) -> AlphaStrategyNode:
        """Get or create a node for the given signal name."""
        result = await self.db.execute(
            select(AlphaStrategyNode).where(AlphaStrategyNode.signal_name == signal_name)
        )
        node = result.scalars().first()
        if node:
            return node
        node = AlphaStrategyNode(
            id=uuid.uuid4(),
            signal_name=signal_name,
            weight=0.0,
        )
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        logger.info("[StrategyGraph] Created node signal_name=%s", signal_name)
        return node

    async def ensure_edge(
        self,
        from_signal: str,
        to_signal: str,
        interaction_strength: float = 0.0,
    ) -> AlphaStrategyEdge:
        """Get or create an edge between two nodes (by signal name)."""
        from_node = await self.ensure_node(from_signal)
        to_node = await self.ensure_node(to_signal)
        result = await self.db.execute(
            select(AlphaStrategyEdge)
            .where(AlphaStrategyEdge.from_node_id == from_node.id)
            .where(AlphaStrategyEdge.to_node_id == to_node.id)
        )
        edge = result.scalars().first()
        if edge:
            edge.interaction_strength = interaction_strength
            await self.db.commit()
            await self.db.refresh(edge)
            return edge
        edge = AlphaStrategyEdge(
            id=uuid.uuid4(),
            from_node_id=from_node.id,
            to_node_id=to_node.id,
            interaction_strength=interaction_strength,
        )
        self.db.add(edge)
        await self.db.commit()
        await self.db.refresh(edge)
        return edge

    async def update_node_weight(self, signal_name: str, weight: float) -> None:
        """Update weight for a node (e.g. from contribution success)."""
        result = await self.db.execute(
            select(AlphaStrategyNode).where(AlphaStrategyNode.signal_name == signal_name)
        )
        node = result.scalars().first()
        if node:
            node.weight = max(0.0, min(1.0, weight))
            await self.db.commit()
            logger.debug("[StrategyGraph] Updated weight signal_name=%s weight=%.4f", signal_name, node.weight)

    async def get_graph_state(self) -> Dict[str, Any]:
        """Return nodes and edges for persistence/display."""
        nodes_q = await self.db.execute(select(AlphaStrategyNode))
        nodes = nodes_q.scalars().all()
        edges_q = await self.db.execute(select(AlphaStrategyEdge))
        edges = edges_q.scalars().all()
        return {
            "nodes": [{"id": str(n.id), "signal_name": n.signal_name, "weight": n.weight} for n in nodes],
            "edges": [
                {"from": str(e.from_node_id), "to": str(e.to_node_id), "interaction_strength": e.interaction_strength}
                for e in edges
            ],
        }

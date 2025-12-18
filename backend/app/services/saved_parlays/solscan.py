"""Solscan URL helpers for inscription verification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolscanConfig:
    cluster: str  # mainnet | devnet
    base_url: str  # e.g. https://solscan.io/tx


class SolscanUrlBuilder:
    """Builds Solscan links for transaction signatures."""

    def __init__(self, config: SolscanConfig):
        self._config = config

    def tx_url(self, tx_signature: str) -> str:
        base = (self._config.base_url or "https://solscan.io/tx").rstrip("/")
        cluster = (self._config.cluster or "mainnet").strip().lower()
        if cluster == "devnet":
            return f"{base}/{tx_signature}?cluster=devnet"
        return f"{base}/{tx_signature}"




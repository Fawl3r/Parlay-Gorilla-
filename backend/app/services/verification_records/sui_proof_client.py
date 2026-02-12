"""Thin wrapper around pysui for SUI create_proof (parlay verification).

Matches the contract of the TS verification worker: create_proof(data_hash_hex, created_at_seconds)
returns (tx_digest, object_id). Used by the Pattern A verifier (sui_verifier.py).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProofCreationResult:
    tx_digest: str
    object_id: str


def _hex_to_bytes32(hex_str: str) -> bytes:
    h = (hex_str or "").strip().lower()
    if len(h) != 64 or not all(c in "0123456789abcdef" for c in h):
        raise ValueError("Invalid data_hash hex (expected 64 hex chars)")
    return bytes.fromhex(h)


def _extract_created_object_id(object_changes: list, expected_suffix: str) -> str:
    for c in object_changes or []:
        if not c or c.get("type") != "created":
            continue
        object_type = (c.get("objectType") or "").strip()
        if not object_type.endswith(expected_suffix):
            continue
        object_id = (c.get("objectId") or "").strip()
        if object_id:
            return object_id
    raise ValueError("Created proof object id not found in transaction object changes")


def _normalize_private_key_for_pysui(raw: str) -> str:
    """Return a key format pysui accepts: base64 keystring (key_type_flag | private_key_seed)."""
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Missing SUI_PRIVATE_KEY")
    if raw.startswith("suiprivkey"):
        try:
            import base64
            from pysui.sui.sui_crypto import KeyPair
            decoded = KeyPair.decode_sui_private_key(raw)
            if hasattr(decoded, "secret_key"):
                return base64.b64encode(getattr(decoded, "secret_key", decoded)).decode()
            if isinstance(decoded, bytes):
                return base64.b64encode(decoded).decode()
        except Exception:
            pass
    return raw


def create_proof(
    data_hash_hex: str,
    created_at_seconds: int,
    *,
    rpc_url: str,
    private_key: str,
    package_id: str,
    module_name: str,
    function_name: str,
    gas_budget: Optional[int] = None,
) -> ProofCreationResult:
    """Create an on-chain proof for a verification record.

    Calls package_id::module_name::function_name(data_hash: vector<u8>, created_at: u64).
    Returns tx_digest and the created Proof object id.
    """
    try:
        from pysui import SuiClient, SuiConfig, handle_result
        from pysui.sui.sui_txn import SyncTransaction
        from pysui.sui.sui_types import SuiU64
    except ImportError as e:
        raise RuntimeError("pysui is required for SUI verification; install with: pip install pysui") from e

    hash_bytes = _hex_to_bytes32(data_hash_hex)
    created_at = max(0, int(created_at_seconds or 0))
    budget = gas_budget or int(os.environ.get("SUI_GAS_BUDGET", "50000000"))

    key_for_config = _normalize_private_key_for_pysui(private_key)
    cfg = SuiConfig.user_config(rpc_url=rpc_url, prv_keys=[key_for_config])
    client = SuiClient(cfg)

    txn = SyncTransaction(client=client)
    target = f"{package_id}::{module_name}::{function_name}"
    txn.move_call(
        target=target,
        arguments=[list(hash_bytes), SuiU64(created_at)],
    )
    options = {"showEffects": True, "showObjectChanges": True}
    result = handle_result(txn.execute(gas_budget=str(budget), options=options))

    # handle_result may return SuiRpcResult; unwrap result_data if present.
    data = getattr(result, "result_data", result)
    j = (getattr(data, "to_json_dict", lambda: None)() or {}) if hasattr(data, "to_json_dict") else {}
    if not j and hasattr(result, "to_json_dict"):
        j = result.to_json_dict() or {}
    tx_digest = (j.get("digest") or getattr(data, "digest", "") or getattr(result, "digest", "") or "").strip()
    if not tx_digest:
        raise ValueError("Missing transaction digest in result")

    object_changes = j.get("objectChanges") or getattr(data, "object_changes", None) or getattr(result, "object_changes", None) or []
    proof_suffix = f"::{module_name}::Proof"
    object_id = _extract_created_object_id(list(object_changes), proof_suffix)

    logger.info("verification proof created tx_digest=%s object_id=%s", tx_digest, object_id)
    return ProofCreationResult(tx_digest=tx_digest, object_id=object_id)

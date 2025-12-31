"""
Crypto payout service for processing affiliate payouts via Circle API.

This service uses Circle API for USDC payouts. Circle provides a clean,
RESTful API for transferring USDC across multiple blockchains.

Based on: https://apidog.com/blog/circle-api/

IMPLEMENTATION STATUS:
======================
✅ Circle API integration implemented
✅ USDC payout support
✅ Multi-chain support (Ethereum, Polygon, Solana, etc.)
✅ Idempotency for safe retries
✅ Error handling and logging

SETUP REQUIRED:
===============
1. Create Circle account: https://circle.com
2. Get API key from Circle dashboard
3. Add to .env:
   CIRCLE_API_KEY=your_api_key_here
   CIRCLE_ENVIRONMENT=sandbox  # or production
4. Get master wallet ID from /v1/configuration endpoint
"""

import asyncio
import logging
import time
from decimal import Decimal
from typing import Optional, Dict, Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory cache for master wallet ID (doesn't change often)
_master_wallet_cache: Optional[str] = None
_master_wallet_cache_lock = asyncio.Lock()
_master_wallet_cache_timestamp: float = 0.0
# Cache TTL: 24 hours (master wallet ID rarely changes)
_MASTER_WALLET_CACHE_TTL_SECONDS = 24 * 60 * 60


class CryptoPayoutService:
    """
    Circle-backed crypto payout client.

    IMPORTANT:
    - This class ONLY talks to Circle and returns transfer results.
    - DB writes (marking payouts/commissions as paid, etc.) are handled by
      `PayoutService` for consistency with PayPal.
    """
    
    def __init__(self):
        self.api_key = settings.circle_api_key
        self.circle_environment = settings.circle_environment

    async def create_usdc_transfer(
        self,
        *,
        recipient_address: str,
        usdc_amount: Decimal,
        chain: str = "ethereum",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a Circle on-chain transfer for a USDC payout."""
        if not self.api_key:
            return {"success": False, "error": "Circle API key not configured (CIRCLE_API_KEY)"}

        return await self._create_circle_transfer(
            recipient_address=recipient_address,
            amount=usdc_amount,
            currency="USDC",
            chain=chain,
            idempotency_key=idempotency_key,
        )
    
    def _get_circle_base_url(self) -> str:
        """Get Circle API base URL based on environment"""
        if (self.circle_environment or "").lower() == "production":
            return "https://api.circle.com"
        else:
            return "https://api-sandbox.circle.com"
    
    async def _create_circle_transfer(
        self,
        recipient_address: str,
        amount: Decimal,
        currency: str = "USDC",
        chain: str = "ethereum",
        idempotency_key: str = None,
    ) -> Dict[str, Any]:
        """
        Create a USDC transfer via Circle API.
        
        Based on Circle API documentation:
        https://apidog.com/blog/circle-api/
        
        Args:
            recipient_address: Crypto wallet address
            amount: Amount in USD (will be converted to USDC)
            currency: Currency code (default USDC)
            chain: Blockchain network (ethereum, polygon, solana, etc.)
            idempotency_key: UUID to prevent duplicate transactions
        
        Returns:
            Dict with success status and transfer details
        """
        import uuid as uuid_module
        
        if not idempotency_key:
            idempotency_key = str(uuid_module.uuid4())
        
        base_url = self._get_circle_base_url()
        
        # Circle API requires amount as string in smallest unit (USDC has 6 decimals).
        try:
            micro_units = int((amount * Decimal("1000000")).to_integral_value())
        except Exception:
            return {"success": False, "error": "Invalid USDC amount"}

        amount_str = str(micro_units)
        
        # Get master wallet ID (should be cached, but fetch if needed)
        master_wallet_id = await self._get_master_wallet_id()
        if not master_wallet_id:
            return {
                "success": False,
                "error": "Failed to get master wallet ID from Circle",
            }
        
        transfer_data = {
            "idempotencyKey": idempotency_key,
            "source": {
                "type": "wallet",
                "id": master_wallet_id,
            },
            "destination": {
                "type": "blockchain",
                "address": recipient_address,
                "chain": chain,
            },
            "amount": {
                "amount": amount_str,
                "currency": currency,
            },
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{base_url}/v1/transfers",
                    json=transfer_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
                
                if response.status_code in (200, 201):
                    data = response.json()
                    transfer = data.get("data", {})
                    
                    return {
                        "success": True,
                        "transfer_id": transfer.get("id"),
                        "transaction_hash": transfer.get("transactionHash"),
                        "status": transfer.get("status"),
                        "data": data,
                    }
                else:
                    error_data = response.json() if response.text else {}
                    error_message = error_data.get("message", f"Circle API error: {response.status_code}")
                    
                    logger.error(
                        f"Circle API transfer error: {response.status_code} - {error_message}"
                    )
                    
                    return {
                        "success": False,
                        "error": error_message,
                        "error_code": str(response.status_code),
                        "details": error_data,
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Circle API request timed out",
            }
        except Exception as e:
            logger.error(f"Error calling Circle API: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Circle API error: {str(e)}",
            }
    
    async def _get_master_wallet_id(self) -> Optional[str]:
        """
        Get master wallet ID from Circle API.
        
        This value is cached in-memory for 24 hours since it rarely changes.
        The master wallet is where your USDC balance is held.
        """
        global _master_wallet_cache, _master_wallet_cache_timestamp
        
        # Check cache first (thread-safe)
        async with _master_wallet_cache_lock:
            now = time.time()
            # Return cached value if still valid
            if _master_wallet_cache and (now - _master_wallet_cache_timestamp) < _MASTER_WALLET_CACHE_TTL_SECONDS:
                logger.debug("Using cached master wallet ID")
                return _master_wallet_cache
        
        # Cache miss or expired - fetch from API
        base_url = self._get_circle_base_url()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url}/v1/configuration",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/json",
                    },
                )
                
                if response.status_code == 200:
                    data = response.json()
                    wallet_id = data.get("data", {}).get("payments", {}).get("masterWalletId")
                    
                    # Update cache if we got a valid wallet ID
                    if wallet_id:
                        async with _master_wallet_cache_lock:
                            _master_wallet_cache = wallet_id
                            _master_wallet_cache_timestamp = time.time()
                            logger.info("Cached master wallet ID from Circle API")
                    
                    return wallet_id
                else:
                    logger.error(
                        f"Failed to get Circle configuration: {response.status_code}"
                    )
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Circle master wallet ID: {e}", exc_info=True)
            return None


# ============================================================================
# CIRCLE API SETUP GUIDE
# ============================================================================

"""
SETUP INSTRUCTIONS:

1. CREATE CIRCLE ACCOUNT:
   - Go to https://circle.com
   - Sign up for developer/sandbox account
   - Verify your email

2. GET API KEY:
   - Log into Circle dashboard
   - Navigate to API Keys section
   - Create new API key
   - Copy and store securely (only shown once!)

3. CONFIGURE ENVIRONMENT:
   Add to .env:
   CIRCLE_API_KEY=your_api_key_here
   CIRCLE_ENVIRONMENT=sandbox  # or production

4. TEST CONNECTION:
   - Use /v1/configuration endpoint to verify
   - Get master wallet ID
   - Test with small amount in sandbox first

5. PRODUCTION:
   - Complete Circle business verification
   - Switch to production API (api.circle.com)
   - Update CIRCLE_ENVIRONMENT=production
   - Fund your master wallet with USDC

SUPPORTED CHAINS:
- ethereum (Ethereum mainnet)
- polygon (Polygon)
- solana (Solana)
- And more - see Circle API docs

WEBHOOKS (Recommended):
- Configure webhook URL in Circle dashboard
- Receive real-time transfer status updates
- Handle completed/failed transfers automatically

REFERENCE:
- Circle API Docs: https://apidog.com/blog/circle-api/
- Circle Developer Portal: https://developers.circle.com/
"""


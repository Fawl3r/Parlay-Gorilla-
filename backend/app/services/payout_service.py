"""
Affiliate payout service for processing PayPal and crypto payouts.
"""

import json
import logging
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.config import settings
from app.models.affiliate import Affiliate
from app.models.affiliate_commission import AffiliateCommission, CommissionStatus
from app.models.affiliate_payout import AffiliatePayout, PayoutStatus, PayoutMethod
from app.models.user import User
from app.services.paypal_payouts_client import PayPalPayoutsClient

logger = logging.getLogger(__name__)


class PayoutService:
    """
    Service for processing affiliate payouts via PayPal and crypto.
    
    Handles:
    - PayPal batch payouts via PayPal Payouts API
    - Crypto payouts (USDC/USDT on various chains)
    - Payout history and tracking
    - Retry logic for failed payouts
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.paypal_client = PayPalPayoutsClient(
            environment=settings.environment,
            client_id=settings.paypal_client_id,
            client_secret=settings.paypal_client_secret,
        )
    
    async def get_ready_commissions_for_affiliate(
        self,
        affiliate_id: str,
        min_amount: Decimal = Decimal("10.00")
    ) -> List[AffiliateCommission]:
        """
        Get all ready commissions for an affiliate that haven't been paid.
        
        Args:
            affiliate_id: Affiliate UUID
            min_amount: Minimum payout amount (default $10)
        
        Returns:
            List of ready commissions
        """
        result = await self.db.execute(
            select(AffiliateCommission)
            .where(
                and_(
                    AffiliateCommission.affiliate_id == affiliate_id,
                    AffiliateCommission.status == CommissionStatus.READY.value,
                )
            )
            .order_by(AffiliateCommission.ready_at.asc())
        )
        
        commissions = list(result.scalars().all())
        
        # Filter by minimum amount
        total = sum(c.amount for c in commissions)
        if total < min_amount:
            return []
        
        return commissions
    
    async def create_payout(
        self,
        affiliate_id: str,
        commission_ids: List[str],
        payout_method: str,
        notes: Optional[str] = None
    ) -> Optional[AffiliatePayout]:
        """
        Create a payout record for an affiliate.
        
        Args:
            affiliate_id: Affiliate UUID
            commission_ids: List of commission IDs to include in payout
            payout_method: paypal, crypto, or bank
            notes: Optional admin notes
        
        Returns:
            Created AffiliatePayout or None if error
        """
        try:
            # Get affiliate
            affiliate_result = await self.db.execute(
                select(Affiliate).where(Affiliate.id == affiliate_id)
            )
            affiliate = affiliate_result.scalar_one_or_none()
            
            if not affiliate:
                logger.error(f"Affiliate not found: {affiliate_id}")
                return None
            
            if not affiliate.payout_email:
                logger.error(f"Affiliate {affiliate_id} has no payout email configured")
                return None
            
            # Get commissions
            commission_uuids = [uuid.UUID(str(cid)) for cid in commission_ids]
            result = await self.db.execute(
                select(AffiliateCommission)
                .where(
                    and_(
                        AffiliateCommission.id.in_(commission_uuids),
                        AffiliateCommission.affiliate_id == affiliate_id,
                        AffiliateCommission.status == CommissionStatus.READY.value,
                    )
                )
            )
            commissions = list(result.scalars().all())
            
            if not commissions:
                logger.error(f"No ready commissions found for payout")
                return None
            
            # Calculate total amount
            total_amount = sum(c.amount for c in commissions)
            
            # Get user for recipient name
            user_result = await self.db.execute(
                select(User).where(User.id == affiliate.user_id)
            )
            user = user_result.scalar_one_or_none()
            recipient_name = user.username if user else None
            
            # Create payout record
            payout = AffiliatePayout(
                id=uuid.uuid4(),
                affiliate_id=affiliate_id,
                amount=total_amount,
                currency="USD",
                payout_method=payout_method,
                recipient_email=affiliate.payout_email,
                recipient_name=recipient_name,
                status=PayoutStatus.PENDING.value,
                notes=notes,
            )
            
            # Associate commissions
            payout.commissions = commissions
            
            self.db.add(payout)
            await self.db.flush()
            
            logger.info(
                f"Created payout {payout.id} for affiliate {affiliate_id}: "
                f"${total_amount} via {payout_method}"
            )
            
            return payout
            
        except Exception as e:
            logger.error(f"Error creating payout: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def process_paypal_payout(
        self,
        payout_id: str
    ) -> Dict[str, Any]:
        """
        Process a PayPal payout.
        
        Uses PayPal Payouts API to send money to affiliate's PayPal email.
        
        Args:
            payout_id: Payout UUID
        
        Returns:
            Dict with success status and details
        """
        try:
            # Get payout
            payout_result = await self.db.execute(
                select(AffiliatePayout).where(AffiliatePayout.id == payout_id)
            )
            payout = payout_result.scalar_one_or_none()
            
            if not payout:
                return {"success": False, "error": "Payout not found"}
            
            if payout.payout_method != PayoutMethod.PAYPAL.value:
                return {"success": False, "error": "Payout method is not PayPal"}
            
            if payout.status != PayoutStatus.PENDING.value:
                return {"success": False, "error": f"Payout status is {payout.status}"}
            
            # Mark as processing
            payout.mark_processing()
            await self.db.flush()
            
            # Get PayPal access token
            access_token = await self.paypal_client.get_access_token()
            if not access_token:
                payout.mark_failed("Failed to get PayPal access token")
                await self.db.commit()
                return {"success": False, "error": "Failed to authenticate with PayPal"}
            
            # Create PayPal payout
            sender_batch_id = f"PG_{str(payout.id).replace('-', '')[:24]}"
            payout_response = await self.paypal_client.create_payout(
                access_token=access_token,
                recipient_email=payout.recipient_email,
                amount=float(payout.amount),
                currency=payout.currency,
                note=f"Affiliate commission payout - {payout.id}",
                sender_batch_id=sender_batch_id,
            )
            
            if payout_response.get("success"):
                # Mark payout as completed
                batch_id = payout_response.get("batch_id")
                payout.mark_completed(
                    provider_payout_id=batch_id,
                    provider_response=json.dumps(payout_response.get("response", {}))
                )

                # Persist tax ledger snapshot fields (PayPal = USD)
                payout.asset_symbol = "USD"
                payout.asset_amount = Decimal(payout.amount)
                payout.asset_chain = None
                payout.transaction_hash = None
                payout.valuation_usd_per_asset = Decimal("1.0")
                payout.valuation_source = "usd"
                payout.valuation_at = payout.completed_at
                payout.valuation_raw = json.dumps({"note": "PayPal USD payout"}) 
                payout.tax_amount_usd = Decimal(payout.amount)
                
                # Mark commissions as paid
                for commission in payout.commissions:
                    commission.mark_paid(
                        payout_id=str(payout.id),
                        notes=f"Paid via PayPal batch {batch_id}"
                    )
                
                # Update affiliate totals
                affiliate_result = await self.db.execute(
                    select(Affiliate).where(Affiliate.id == payout.affiliate_id)
                )
                affiliate = affiliate_result.scalar_one_or_none()
                if affiliate:
                    affiliate.total_commission_paid += payout.amount
                
                await self.db.commit()
                
                logger.info(
                    f"Successfully processed PayPal payout {payout.id}: "
                    f"batch_id={batch_id}"
                )
                
                return {
                    "success": True,
                    "payout_id": str(payout.id),
                    "batch_id": batch_id,
                    "amount": float(payout.amount),
                }
            else:
                error_msg = payout_response.get("error", "Unknown error")
                payout.mark_failed(error_msg)
                await self.db.commit()
                
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"Error processing PayPal payout {payout_id}: {e}", exc_info=True)
            await self.db.rollback()
            
            # Mark payout as failed if it exists
            try:
                payout_result = await self.db.execute(
                    select(AffiliatePayout).where(AffiliatePayout.id == payout_id)
                )
                payout = payout_result.scalar_one_or_none()
                if payout:
                    payout.mark_failed(str(e))
                    await self.db.commit()
            except:
                pass
            
            return {"success": False, "error": str(e)}
    
    async def process_crypto_payout(
        self,
        payout_id: str
    ) -> Dict[str, Any]:
        """
        Process a crypto payout.
        
        Uses crypto_payout_service for implementation.
        
        Args:
            payout_id: Payout UUID
        
        Returns:
            Dict with success status and details
        """
        from app.services.crypto_payout_service import CryptoPayoutService
        from app.services.tax.valuation_service import UsdValuationService
        
        try:
            # Get payout
            payout_result = await self.db.execute(
                select(AffiliatePayout).where(AffiliatePayout.id == payout_id)
            )
            payout = payout_result.scalar_one_or_none()
            
            if not payout:
                return {"success": False, "error": "Payout not found"}
            
            if payout.payout_method != PayoutMethod.CRYPTO.value:
                return {"success": False, "error": "Payout method is not crypto"}
            
            if payout.status != PayoutStatus.PENDING.value:
                return {"success": False, "error": f"Payout status is {payout.status}"}
            
            # Mark as processing (persist before external call)
            payout.mark_processing()
            await self.db.flush()

            # For now, crypto payouts are USDC via Circle.
            chain = payout.asset_chain or "ethereum"
            usdc_amount: Decimal = Decimal(payout.amount)

            # Snapshot USD valuation inputs at payment time for audit trail.
            valuation_service = UsdValuationService(
                external_quotes_enabled=settings.tax_valuation_external_enabled,
                timeout_seconds=settings.tax_valuation_timeout_seconds,
            )
            quote = await valuation_service.quote_usd_per_asset("USDC")

            crypto_service = CryptoPayoutService()
            result = await crypto_service.create_usdc_transfer(
                recipient_address=payout.recipient_email,
                usdc_amount=usdc_amount,
                chain=chain,
                idempotency_key=str(payout.id),
            )
            
            if result.get("success"):
                transfer_id = result.get("transfer_id")
                tx_hash = result.get("transaction_hash")

                # Persist tax ledger snapshot fields (crypto + valuation)
                payout.asset_symbol = "USDC"
                payout.asset_amount = usdc_amount
                payout.asset_chain = chain
                payout.transaction_hash = tx_hash
                payout.valuation_usd_per_asset = quote.usd_per_asset
                payout.valuation_source = quote.source
                payout.valuation_at = quote.as_of
                payout.valuation_raw = json.dumps(quote.raw) if quote.raw is not None else None
                payout.tax_amount_usd = (usdc_amount * quote.usd_per_asset).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                # Mark payout as completed and store provider reference (Circle transfer id)
                payout.mark_completed(
                    provider_payout_id=transfer_id,
                    provider_response=json.dumps(result.get("data", {})),
                )

                # Mark commissions as paid
                for commission in payout.commissions:
                    commission.mark_paid(
                        payout_id=str(payout.id),
                        notes=f"Paid via Circle USDC on {chain}: {tx_hash or transfer_id}"
                    )
                
                # Update affiliate totals
                affiliate_result = await self.db.execute(
                    select(Affiliate).where(Affiliate.id == payout.affiliate_id)
                )
                affiliate = affiliate_result.scalar_one_or_none()
                if affiliate:
                    affiliate.total_commission_paid += payout.amount
                
                await self.db.commit()
                
                logger.info(f"Successfully processed crypto payout {payout.id}")
            
            return result
                
        except Exception as e:
            logger.error(f"Error processing crypto payout {payout_id}: {e}", exc_info=True)
            await self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_payout_history(
        self,
        affiliate_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AffiliatePayout]:
        """Get payout history with optional filters"""
        query = select(AffiliatePayout)
        
        if affiliate_id:
            query = query.where(AffiliatePayout.affiliate_id == affiliate_id)
        
        if status:
            query = query.where(AffiliatePayout.status == status)
        
        query = query.order_by(AffiliatePayout.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_payout_summary(self) -> Dict[str, Any]:
        """Get summary of all payouts"""
        result = await self.db.execute(
            select(
                func.count(AffiliatePayout.id).label("total_payouts"),
                func.sum(AffiliatePayout.amount).label("total_amount"),
                func.count(
                    select(AffiliatePayout.id)
                    .where(AffiliatePayout.status == PayoutStatus.COMPLETED.value)
                    .scalar_subquery()
                ).label("completed_payouts"),
                func.sum(
                    select(AffiliatePayout.amount)
                    .where(AffiliatePayout.status == PayoutStatus.COMPLETED.value)
                    .scalar_subquery()
                ).label("completed_amount"),
            )
        )
        
        row = result.first()
        
        return {
            "total_payouts": row.total_payouts or 0,
            "total_amount": float(row.total_amount or 0),
            "completed_payouts": row.completed_payouts or 0,
            "completed_amount": float(row.completed_amount or 0),
        }


"""
Affiliate Service for managing the affiliate program.

Handles:
- Affiliate registration and management
- Referral link tracking (clicks)
- User referral attribution
- Commission calculation and creation
- Tier management and upgrades
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
import uuid
import logging

from app.models.affiliate import Affiliate
from app.models.affiliate_click import AffiliateClick
from app.models.affiliate_referral import AffiliateReferral
from app.models.affiliate_commission import (
    AffiliateCommission,
    CommissionStatus,
    CommissionSaleType
)
from app.models.user import User
from app.services.affiliate_stats_service import AffiliateStats, AffiliateStatsService

logger = logging.getLogger(__name__)


class AffiliateService:
    """
    Service for managing affiliate program operations.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # AFFILIATE MANAGEMENT
    # =========================================================================
    
    async def create_affiliate(self, user_id: str) -> Optional[Affiliate]:
        """
        Create a new affiliate account for a user.
        
        Returns None if user already has an affiliate account.
        """
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            return None
        
        # Check if already an affiliate
        existing = await self.get_affiliate_by_user_id(user_id)
        if existing:
            logger.warning(f"User {user_id} already has an affiliate account")
            return existing
        
        # Create affiliate with unique referral code
        affiliate = Affiliate.create_with_referral_code(user_uuid)
        
        # Ensure referral code is unique (retry if collision)
        for _ in range(5):
            existing_code = await self.get_affiliate_by_code(affiliate.referral_code)
            if not existing_code:
                break
            affiliate.referral_code = Affiliate.generate_referral_code()
        
        self.db.add(affiliate)
        
        # Update user's affiliate_id reference
        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
        if user:
            user.affiliate_id = affiliate.id
        
        try:
            await self.db.commit()
            await self.db.refresh(affiliate)
            logger.info(f"Created affiliate account for user {user_id}, code: {affiliate.referral_code}")
            return affiliate
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating affiliate for user {user_id}: {e}")
            return None
    
    async def get_affiliate_by_id(self, affiliate_id: str) -> Optional[Affiliate]:
        """Get affiliate by ID"""
        try:
            aff_uuid = uuid.UUID(affiliate_id)
        except ValueError:
            return None
        
        result = await self.db.execute(
            select(Affiliate).where(Affiliate.id == aff_uuid)
        )
        return result.scalar_one_or_none()
    
    async def get_affiliate_by_user_id(self, user_id: str) -> Optional[Affiliate]:
        """Get affiliate by user ID"""
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None
        
        result = await self.db.execute(
            select(Affiliate).where(Affiliate.user_id == user_uuid)
        )
        return result.scalar_one_or_none()
    
    async def get_affiliate_by_code(self, referral_code: str) -> Optional[Affiliate]:
        """Get affiliate by referral code"""
        result = await self.db.execute(
            select(Affiliate).where(Affiliate.referral_code == referral_code.upper())
        )
        return result.scalar_one_or_none()
    
    async def update_payout_info(
        self,
        affiliate_id: str,
        payout_email: str,
        payout_method: str
    ) -> bool:
        """Update affiliate's payout information"""
        affiliate = await self.get_affiliate_by_id(affiliate_id)
        if not affiliate:
            return False
        
        affiliate.payout_email = payout_email
        affiliate.payout_method = payout_method
        
        try:
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating payout info for affiliate {affiliate_id}: {e}")
            return False
    
    # =========================================================================
    # CLICK TRACKING
    # =========================================================================
    
    async def record_click(
        self,
        referral_code: str,
        ip_address: str = None,
        user_agent: str = None,
        referer_url: str = None,
        landing_page: str = None,
        utm_source: str = None,
        utm_medium: str = None,
        utm_campaign: str = None,
    ) -> Optional[AffiliateClick]:
        """
        Record a click on an affiliate's referral link.
        
        Returns the click record for cookie storage.
        """
        affiliate = await self.get_affiliate_by_code(referral_code)
        if not affiliate:
            logger.warning(f"Click recorded for unknown referral code: {referral_code}")
            return None
        
        if not affiliate.is_active:
            logger.warning(f"Click recorded for inactive affiliate: {affiliate.id}")
            return None
        
        click = AffiliateClick(
            id=uuid.uuid4(),
            affiliate_id=affiliate.id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer_url=referer_url,
            landing_page=landing_page,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
        )
        
        self.db.add(click)
        affiliate.increment_click()
        
        try:
            await self.db.commit()
            await self.db.refresh(click)
            logger.info(f"Recorded click for affiliate {affiliate.id}, code: {referral_code}")
            return click
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error recording click: {e}")
            return None
    
    # =========================================================================
    # REFERRAL ATTRIBUTION
    # =========================================================================
    
    async def create_referral(
        self,
        affiliate_id: str,
        referred_user_id: str,
        click_id: str = None,
    ) -> Optional[AffiliateReferral]:
        """
        Create a referral record when a new user signs up through an affiliate link.
        
        Also updates the user's referred_by_affiliate_id field.
        """
        try:
            aff_uuid = uuid.UUID(affiliate_id)
            user_uuid = uuid.UUID(referred_user_id)
            click_uuid = uuid.UUID(click_id) if click_id else None
        except ValueError as e:
            logger.error(f"Invalid UUID format: {e}")
            return None
        
        # Check if referral already exists
        existing = await self.db.execute(
            select(AffiliateReferral).where(
                AffiliateReferral.referred_user_id == user_uuid
            )
        )
        if existing.scalar_one_or_none():
            logger.warning(f"User {referred_user_id} already has a referral record")
            return None
        
        # Get affiliate and verify it's active
        affiliate = await self.get_affiliate_by_id(affiliate_id)
        if not affiliate or not affiliate.is_active:
            logger.warning(f"Cannot create referral - affiliate {affiliate_id} not found or inactive")
            return None
        
        # Create referral
        referral = AffiliateReferral(
            id=uuid.uuid4(),
            affiliate_id=aff_uuid,
            referred_user_id=user_uuid,
            click_id=click_uuid,
        )
        self.db.add(referral)
        
        # Update affiliate stats
        affiliate.increment_referral()
        
        # Update click as converted (if provided)
        if click_uuid:
            click_result = await self.db.execute(
                select(AffiliateClick).where(AffiliateClick.id == click_uuid)
            )
            click = click_result.scalar_one_or_none()
            if click:
                click.mark_converted(user_uuid)
        
        # Update user's referred_by_affiliate_id
        user_result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.referred_by_affiliate_id = aff_uuid
        
        try:
            await self.db.commit()
            await self.db.refresh(referral)
            logger.info(f"Created referral: affiliate {affiliate_id} -> user {referred_user_id}")
            return referral
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating referral: {e}")
            return None
    
    async def attribute_user_to_affiliate(
        self,
        user_id: str,
        referral_code: str,
        click_id: str = None,
    ) -> bool:
        """
        Attribute a user signup to an affiliate by referral code.
        
        This is the main method to call when a user signs up with a referral code
        (from URL param or cookie).
        """
        affiliate = await self.get_affiliate_by_code(referral_code)
        if not affiliate:
            logger.warning(f"Attribution failed - unknown code: {referral_code}")
            return False
        
        referral = await self.create_referral(
            affiliate_id=str(affiliate.id),
            referred_user_id=user_id,
            click_id=click_id,
        )
        
        return referral is not None
    
    # =========================================================================
    # COMMISSION MANAGEMENT
    # =========================================================================
    
    async def calculate_and_create_commission(
        self,
        user_id: str,
        sale_type: str,
        sale_amount: Decimal,
        sale_id: str,
        is_first_subscription: bool = False,
        subscription_plan: str = None,
        credit_pack_id: str = None,
    ) -> Optional[AffiliateCommission]:
        """
        Calculate and create a commission for a referred user's purchase.
        
        Called from payment webhook handlers when a payment is confirmed.
        
        Returns None if:
        - User has no affiliate referral
        - Affiliate is inactive
        """
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None
        
        # Get user's referring affiliate
        user_result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = user_result.scalar_one_or_none()
        
        if not user or not user.referred_by_affiliate_id:
            logger.debug(f"No commission - user {user_id} has no referrer")
            return None
        
        # Get affiliate
        affiliate_result = await self.db.execute(
            select(Affiliate).where(Affiliate.id == user.referred_by_affiliate_id)
        )
        affiliate = affiliate_result.scalar_one_or_none()
        
        if not affiliate or not affiliate.is_active:
            logger.warning(f"No commission - affiliate inactive or not found")
            return None

        # Commission metadata we persist on the commission record
        is_first_subscription_payment = False

        # Calculate commission rate based on sale type and subscription status
        if sale_type == CommissionSaleType.SUBSCRIPTION.value:
            # "First subscription" is defined as the first-ever paid subscription for the
            # referred user (lifetime). Webhooks/providers may label events as "first",
            # but we enforce the invariant here to avoid double-paying the first-sub rate.
            if is_first_subscription:
                prior_subscription_commission = (
                    await self.db.execute(
                        select(AffiliateCommission.id)
                        .where(
                            and_(
                                AffiliateCommission.referred_user_id == user_uuid,
                                AffiliateCommission.sale_type == CommissionSaleType.SUBSCRIPTION.value,
                            )
                        )
                        .limit(1)
                    )
                ).scalar_one_or_none()
                is_first_subscription_payment = prior_subscription_commission is None

            if is_first_subscription_payment:
                commission_rate = affiliate.commission_rate_sub_first
            else:
                commission_rate = affiliate.commission_rate_sub_recurring
        elif sale_type == CommissionSaleType.CREDIT_PACK.value:
            commission_rate = affiliate.commission_rate_credits
        else:
            logger.error(f"Unknown sale type: {sale_type}")
            return None
        
        # Create commission record
        commission = AffiliateCommission.create_commission(
            affiliate_id=affiliate.id,
            referred_user_id=user_uuid,
            sale_id=sale_id,
            sale_type=sale_type,
            base_amount=sale_amount,
            commission_rate=commission_rate,
            is_first_subscription_payment=is_first_subscription_payment,
            subscription_plan=subscription_plan,
            credit_pack_id=credit_pack_id,
        )
        
        self.db.add(commission)
        
        # Update affiliate totals
        affiliate.add_revenue(sale_amount, commission.amount)
        
        # Check for tier upgrade
        tier_upgraded = affiliate.recalculate_tier()
        if tier_upgraded:
            logger.info(f"Affiliate {affiliate.id} upgraded to tier: {affiliate.tier}")
        
        try:
            await self.db.commit()
            await self.db.refresh(commission)
            logger.info(
                f"Created commission: affiliate {affiliate.id}, amount ${commission.amount}, "
                f"sale ${sale_amount}, rate {commission_rate}"
            )
            return commission
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating commission: {e}")
            return None
    
    async def get_affiliate_commissions(
        self,
        affiliate_id: str,
        status: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AffiliateCommission]:
        """Get commissions for an affiliate with optional status filter"""
        try:
            aff_uuid = uuid.UUID(affiliate_id)
        except ValueError:
            return []
        
        query = select(AffiliateCommission).where(
            AffiliateCommission.affiliate_id == aff_uuid
        )
        
        if status:
            query = query.where(AffiliateCommission.status == status)
        
        query = query.order_by(desc(AffiliateCommission.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def process_ready_commissions(self) -> int:
        """
        Process commissions that are ready for payout.
        
        Moves commissions from PENDING to READY status when their
        hold period has passed.
        
        Returns the number of commissions processed.
        """
        now = datetime.now(timezone.utc)
        
        result = await self.db.execute(
            select(AffiliateCommission).where(
                and_(
                    AffiliateCommission.status == CommissionStatus.PENDING.value,
                    AffiliateCommission.ready_at <= now,
                )
            )
        )
        
        processed = 0
        for commission in result.scalars().all():
            commission.mark_ready()
            processed += 1
        
        if processed > 0:
            await self.db.commit()
            logger.info(f"Processed {processed} commissions to READY status")
        
        return processed

    async def get_affiliate_stats(self, affiliate_id: str) -> Optional[AffiliateStats]:
        """Get detailed statistics for an affiliate."""
        return await AffiliateStatsService(self.db).get_affiliate_stats(affiliate_id)

    async def get_affiliate_referrals(
        self,
        affiliate_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get list of referrals for an affiliate with user info."""
        return await AffiliateStatsService(self.db).get_affiliate_referrals(
            affiliate_id=affiliate_id,
            limit=limit,
            offset=offset,
        )
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top affiliates by total referred revenue."""
        return await AffiliateStatsService(self.db).get_leaderboard(limit=limit)

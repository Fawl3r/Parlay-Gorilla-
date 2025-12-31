# Promo Codes Reference

This document contains the list of active promo codes for F3 Parlay Gorilla.

## Active Promo Codes

### Premium Free Month Code
- **Code**: `F3FREEMONTH`
- **Type**: Free Month of Premium
- **Reward**: 30 days of Premium access
- **Max Uses**: 100 total (1 per user)
- **Status**: Active

**Details:**
- Grants 30 days of Premium access when redeemed
- Can be redeemed once per user account
- Stacks with existing premium subscriptions (adds 30 days to current period end)
- Cannot be used if user already has lifetime access

**To Create/Regenerate:**
```bash
python backend/scripts/create_promo_codes.py
```

Or via Admin Panel:
1. Go to Admin Panel → Promo Codes (`/admin/promo-codes`)
2. Create new code with:
   - Reward Type: `premium_month`
   - Code: `F3FREEMONTH`
   - Expires: 1 year from creation date (or as needed)
   - Max Uses Total: 100 (or desired limit)

### Lifetime Membership Code
- **Code**: `F3LIFETIME`
- **Type**: Lifetime Membership Upgrade
- **Reward**: Grants lifetime premium access
- **Max Uses**: Unlimited (for admin use)
- **Status**: Special handling required

**Important Notes:**
- ⚠️ The current promo code system does **not** support `lifetime` as a reward type
- This code requires **manual processing** via script
- Cannot be redeemed through the standard promo code redemption flow
- Use the dedicated script to grant lifetime access

**To Grant Lifetime Access:**
```bash
python backend/scripts/grant_lifetime_membership.py user@example.com
```

**What it does:**
- Creates a lifetime subscription with `is_lifetime=True`
- Sets user plan to `elite`
- Sets `current_period_end` to `None` (no expiration)
- Updates user subscription status to `active`

## How to Use Promo Codes

### For Users
1. Navigate to Billing page (`/billing`)
2. Find the "Promo Code" section
3. Enter the code and click "Redeem"
4. The reward will be applied immediately

### For Admins
1. Create codes via Admin Panel at `/admin/promo-codes`
2. Monitor redemptions and usage
3. Deactivate codes when no longer needed

## Reward Types

Currently supported reward types:
- `premium_month` - Grants 30 days of Premium access
- `credits_3` - Grants 3 AI parlay credits

## Future Enhancements

Consider adding:
- `lifetime` reward type to the `PromoRewardType` enum
- Automatic lifetime subscription creation in `PromoCodeService.redeem()`
- Support for the `F3LIFETIME` code to automatically grant lifetime access

## Quick Reference

| Code | Type | Reward | Status |
|------|------|--------|--------|
| `F3FREEMONTH` | Premium Month | 30 days Premium | ✅ Active |
| `F3LIFETIME` | Lifetime | Lifetime Premium | ⚠️ Manual Only |

## Related Files

- `backend/app/models/promo_code.py` - Promo code model and reward types
- `backend/app/services/promo_codes/promo_code_service.py` - Promo code service logic
- `backend/scripts/create_promo_codes.py` - Script to create standard promo codes
- `backend/scripts/grant_lifetime_membership.py` - Manual lifetime membership grant script
- `frontend/app/admin/promo-codes/page.tsx` - Admin panel for managing codes


# Current Promo Codes - F3 Parlay Gorilla

**Last Updated:** January 2025

This document lists all active and available promo codes for F3 Parlay Gorilla.

---

## Active Promo Codes

### 1. F3FREEMONTH

**Code:** `F3FREEMONTH`  
**Type:** Premium Free Month  
**Reward:** 30 days of Premium (Elite) access  
**Max Uses:** 100 total redemptions (1 per user)  
**Status:** ✅ Active  
**Expiration:** 1 year from creation date

**Details:**
- Grants 30 days of Premium access when redeemed
- Can be redeemed **once per user account**
- Stacks with existing premium subscriptions (adds 30 days to current period end)
- Cannot be used if user already has lifetime access
- Automatically extends subscription period end date

**Redemption:**
- Users can redeem at `/billing` page
- Enter code in "Promo Code" section
- Reward applied immediately upon redemption

**Admin Management:**
- View/Manage via Admin Panel: `/admin/promo-codes`
- Monitor redemptions and usage statistics
- Can deactivate if needed

---

### 2. F3LIFETIME

**Code:** `F3LIFETIME`  
**Type:** Lifetime Membership  
**Reward:** Lifetime Premium (Elite) access  
**Max Uses:** Unlimited (admin use only)  
**Status:** ⚠️ Manual Processing Required

**Important Notes:**
- ⚠️ **NOT** supported through standard promo code redemption system
- Requires **manual processing** via dedicated script
- Cannot be redeemed through the billing page promo code flow
- Reserved for special cases and admin use

**To Grant Lifetime Access:**
```bash
cd backend
python scripts/grant_lifetime_membership.py user@example.com
```

**What the script does:**
- Creates a lifetime subscription with `is_lifetime=True`
- Sets user plan to `elite`
- Sets `current_period_end` to `None` (no expiration)
- Updates user subscription status to `active`

**Future Enhancement:**
- Consider adding `lifetime` as a supported `PromoRewardType`
- Enable automatic lifetime subscription creation in promo redemption flow

---

## Supported Reward Types

The promo code system currently supports the following reward types:

| Reward Type | Code | Description | Days/Credits |
|------------|------|-------------|--------------|
| `premium_month` | `F3FREEMONTH` | 30 days of Premium access | 30 days |
| `credits_3` | (Auto-generated) | 3 AI parlay credits | 3 credits |

**Note:** `lifetime` is not yet a supported reward type in the enum.

---

## How to Use Promo Codes

### For Users

1. Navigate to **Billing page** (`/billing`)
2. Find the **"Promo Code"** section
3. Enter the code (e.g., `F3FREEMONTH`)
4. Click **"Redeem"**
5. The reward will be applied immediately
6. Confirmation message will display the reward details

### For Admins

#### Create New Promo Codes

**Option 1: Via Admin Panel (Recommended)**
1. Go to Admin Panel → Promo Codes (`/admin/promo-codes`)
2. Click "Create New Code"
3. Fill in:
   - **Reward Type:** Select from dropdown (`premium_month` or `credits_3`)
   - **Code:** Enter custom code (e.g., `F3FREEMONTH`) or leave blank for auto-generation
   - **Expires At:** Set expiration date (typically 1 year from creation)
   - **Max Uses Total:** Set limit (e.g., 100)
   - **Notes:** Optional description
4. Click "Create"

**Option 2: Via Script**
```bash
cd backend
python scripts/create_promo_codes.py
```

This script creates the standard `F3FREEMONTH` code with default settings.

#### Monitor Promo Codes

- View all codes at `/admin/promo-codes`
- See redemption counts and usage statistics
- Deactivate codes when no longer needed
- View individual redemption history

---

## Promo Code Rules & Constraints

### Redemption Rules

1. **One-time use per user:** Each user can only redeem a specific code once
2. **Active status required:** Code must be `is_active=True`
3. **Not expired:** Code must not have passed `expires_at` date
4. **Usage limit:** Total redemptions must not exceed `max_uses_total`
5. **Lifetime restriction:** Users with lifetime access cannot redeem premium month codes

### Validation Checks

The system performs the following checks before allowing redemption:
- ✅ Code exists and is active
- ✅ Code has not expired
- ✅ User has not already redeemed this code
- ✅ Total redemptions < max_uses_total
- ✅ User is not already a lifetime member (for premium codes)

---

## Quick Reference Table

| Code | Type | Reward | Max Uses | Status | Redemption Method |
|------|------|--------|----------|--------|-------------------|
| `F3FREEMONTH` | Premium Month | 30 days Premium | 100 total | ✅ Active | Standard (Billing Page) |
| `F3LIFETIME` | Lifetime | Lifetime Premium | Unlimited | ⚠️ Manual | Script Only |

---

## Technical Details

### Database Schema

**PromoCode Table:**
- `id` - UUID primary key
- `code` - Unique code string (e.g., "F3FREEMONTH")
- `reward_type` - Enum: `premium_month` or `credits_3`
- `expires_at` - Expiration datetime (timezone-aware)
- `max_uses_total` - Maximum total redemptions allowed
- `redeemed_count` - Current redemption count (denormalized)
- `is_active` - Active status flag
- `deactivated_at` - Deactivation timestamp (nullable)
- `created_by_user_id` - Admin user who created the code
- `notes` - Optional notes/description
- `created_at` / `updated_at` - Timestamps

**PromoRedemption Table:**
- Tracks individual redemptions
- Enforces one-time use per user via unique constraint
- Links to both `promo_code_id` and `user_id`

### Related Files

**Backend:**
- `backend/app/models/promo_code.py` - Promo code model and reward types enum
- `backend/app/models/promo_redemption.py` - Redemption tracking model
- `backend/app/services/promo_codes/promo_code_service.py` - Service logic for creation/redemption
- `backend/app/services/promo_codes/promo_code_generator.py` - Auto-code generation
- `backend/app/api/routes/promo_codes.py` - Public API endpoints
- `backend/app/api/routes/admin/promo_codes.py` - Admin API endpoints
- `backend/scripts/create_promo_codes.py` - Script to create standard codes
- `backend/scripts/grant_lifetime_membership.py` - Manual lifetime access script

**Frontend:**
- `frontend/app/billing/page.tsx` - User promo code redemption UI
- `frontend/app/admin/promo-codes/page.tsx` - Admin promo code management panel

---

## Future Enhancements

Consider implementing:
- ✅ `lifetime` reward type in `PromoRewardType` enum
- ✅ Automatic lifetime subscription creation in `PromoCodeService.redeem()`
- ✅ Support for `F3LIFETIME` code through standard redemption flow
- ✅ Additional reward types (e.g., `credits_10`, `premium_week`)
- ✅ Time-limited promotional codes (e.g., holiday specials)
- ✅ Referral-based promo codes
- ✅ Bulk code generation for campaigns

---

## Support & Troubleshooting

### Common Issues

**"Code already redeemed"**
- User has already used this code (one-time use per user)

**"Code expired"**
- Code has passed its expiration date
- Admin can create a new code with same value if needed

**"Code not found"**
- Code may be inactive or deactivated
- Check admin panel for code status

**"Maximum uses reached"**
- Code has reached its `max_uses_total` limit
- Admin can create a new code or increase the limit

### Contact

For promo code issues or questions:
- Check Admin Panel: `/admin/promo-codes`
- Review redemption logs in database
- Contact system administrator

---

**Document Version:** 1.0  
**Maintained By:** F3 AI Labs  
**Last Review:** January 2025

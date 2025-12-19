# LemonSqueezy Affiliate System Research

## Executive Summary

LemonSqueezy offers a **built-in affiliate system** that can handle referral tracking, commission calculation, and payouts directly through their platform. This document compares LemonSqueezy's affiliate system with the current custom Parlay Gorilla Affiliate system to help determine the best approach.

---

## Current System: Parlay Gorilla Affiliates

### ✅ What We Have

**Custom-built affiliate system** with full control:

- **Referral Tracking**: Custom referral codes (`?ref=CODE`)
- **Commission Tiers**: Rookie, Pro, Elite, Master (20-35% rates)
- **Commission Types**: 
  - First subscription payment: 20-35%
  - Recurring subscriptions: 0-10% (tier-based)
  - Credit packs: 20-35%
- **Payout System**: PayPal and crypto (Circle API ready)
- **30-Day Hold Period**: Prevents payouts on refunded purchases
- **Full Analytics**: Clicks, referrals, revenue, commissions
- **Admin Dashboard**: Complete management interface
- **Tax Reporting**: 1099-NEC support for US affiliates

### Current Implementation Status

- ✅ Full database models (Affiliate, Commission, Referral, Click, Payout)
- ✅ Commission calculation and tracking
- ✅ Webhook integration (LemonSqueezy payments trigger commissions)
- ✅ PayPal payout integration
- ✅ Crypto payout structure (ready for implementation)
- ✅ Admin dashboard routes
- ✅ Frontend affiliate dashboard

---

## LemonSqueezy's Built-in Affiliate System

### Features

1. **Unlimited Referral Links**
   - Generate multiple affiliate links per affiliate
   - Customizable link parameters
   - Automatic tracking

2. **Real-Time Analytics**
   - Clicks, conversions, earnings
   - Performance dashboards
   - Export capabilities

3. **Flexible Commission Structures**
   - Custom commission rates per product/variant
   - Cookie duration settings
   - Product eligibility controls

4. **Affiliate Management**
   - Onboard affiliates through LemonSqueezy dashboard
   - Provide marketing materials
   - Communication tools

5. **Integrated Payments**
   - Automatic commission payouts
   - Handles payment processing
   - Built-in tax handling

### Limitations & Considerations

1. **No API for Affiliate Management**
   - Must manage affiliates through LemonSqueezy dashboard
   - No programmatic affiliate creation/management
   - Limited customization of affiliate experience

2. **Commission Structure Constraints**
   - Commission rates set per product/variant in LemonSqueezy
   - May not support complex tier-based systems easily
   - Recurring subscription commission handling may be limited

3. **Payout Control**
   - Payouts handled by LemonSqueezy
   - Less control over payout timing/scheduling
   - May not support crypto payouts natively

4. **Integration Complexity**
   - Would need to sync affiliate data between systems
   - Custom referral tracking might conflict
   - Webhook handling for affiliate events

5. **Branding**
   - Affiliate links point to LemonSqueezy checkout
   - Less control over affiliate experience
   - May not match custom affiliate dashboard

---

## Comparison Matrix

| Feature | Custom System | LemonSqueezy |
|---------|--------------|--------------|
| **Referral Tracking** | ✅ Custom codes (`?ref=CODE`) | ✅ Built-in links |
| **Commission Tiers** | ✅ 4 tiers (Rookie→Master) | ⚠️ Per-product rates |
| **Recurring Commissions** | ✅ Tier-based (0-10%) | ⚠️ Limited support |
| **Credit Pack Commissions** | ✅ 20-35% | ✅ If configured |
| **Payout Control** | ✅ Full control (PayPal/crypto) | ⚠️ LemonSqueezy handles |
| **30-Day Hold Period** | ✅ Custom logic | ❓ Unknown |
| **Admin Dashboard** | ✅ Full custom UI | ⚠️ LemonSqueezy dashboard |
| **Affiliate Dashboard** | ✅ Custom branded | ⚠️ LemonSqueezy branded |
| **Tax Reporting** | ✅ 1099-NEC ready | ✅ Built-in |
| **API Access** | ✅ Full API control | ❌ Limited/no API |
| **Crypto Payouts** | ✅ Structure ready | ❌ Not supported |
| **Analytics** | ✅ Custom tracking | ✅ Built-in analytics |
| **Multi-Product Support** | ✅ Flexible | ✅ Yes |
| **Custom Branding** | ✅ Full control | ❌ Limited |

---

## Recommendation: Hybrid Approach

### Option 1: Keep Custom System (Recommended)

**Why:**
- ✅ Full control over commission structure (tiers, rates)
- ✅ Custom affiliate experience and branding
- ✅ Crypto payout support
- ✅ Already fully implemented and working
- ✅ 30-day hold period for refund protection
- ✅ Flexible for future needs

**When to use:**
- You need complex commission structures
- You want full control over affiliate experience
- You need crypto payouts
- You want custom branding

### Option 2: Use LemonSqueezy Affiliates

**Why:**
- ✅ Less maintenance (handled by LemonSqueezy)
- ✅ Built-in analytics and reporting
- ✅ Automatic payout handling
- ✅ Tax reporting included

**When to use:**
- Simple commission structure (flat rates)
- Don't need crypto payouts
- Want to reduce maintenance burden
- Okay with LemonSqueezy branding

### Option 3: Hybrid (Best of Both)

**How it works:**
1. Use **LemonSqueezy affiliates** for simple, standard referrals
2. Keep **custom system** for:
   - Complex tier-based commissions
   - Crypto payouts
   - Custom affiliate dashboard
   - Special promotions/campaigns

**Implementation:**
- Track referrals in both systems
- Use custom system for complex cases
- Use LemonSqueezy for standard affiliates
- Sync data between systems if needed

---

## Technical Integration Considerations

### If Using LemonSqueezy Affiliates

1. **Referral Tracking**
   - LemonSqueezy uses `?aff=` parameter in checkout URLs
   - Would need to detect and sync with custom system
   - May conflict with existing `?ref=` tracking

2. **Webhook Integration**
   - LemonSqueezy sends affiliate-related webhooks
   - Would need to handle `affiliate_commission_created` events
   - Sync commission data to custom system if using hybrid

3. **Checkout URL Modification**
   - Add affiliate parameter to LemonSqueezy checkout URLs
   - Format: `https://checkout.lemonsqueezy.com/checkout/buy/{variant_id}?aff={affiliate_id}`

4. **Commission Attribution**
   - LemonSqueezy tracks which affiliate referred the sale
   - Commission calculated automatically
   - Payout handled by LemonSqueezy

### Current Webhook Handler

The current system already handles LemonSqueezy webhooks:
- `subscription_created`
- `subscription_updated`
- `subscription_cancelled`
- `payment_success`
- `order_created`

**Current Affiliate Integration:**
- ✅ Custom affiliate commissions are calculated when LemonSqueezy payments are confirmed
- ✅ Webhook handlers call `_handle_affiliate_commission()` for:
  - First subscription payments
  - Recurring subscription payments
  - Credit pack purchases
- ✅ Uses custom referral tracking (`?ref=CODE`) stored in user's `referred_by_affiliate_id`

**If Using LemonSqueezy Affiliates:**
- Would need to detect affiliate from LemonSqueezy checkout (`?aff=ID`)
- Would need to handle `affiliate_commission_created` webhook (if available)
- Would need to sync LemonSqueezy affiliate IDs with custom system
- May need to modify checkout URL generation to include `?aff=` parameter

---

## Cost Analysis

### Custom System
- **Development**: ✅ Already complete
- **Maintenance**: Ongoing (minimal)
- **Payout Processing**: PayPal fees (~2.9% + $0.30) or crypto gas fees
- **Infrastructure**: Existing database/storage

### LemonSqueezy Affiliates
- **Setup**: Free (included with LemonSqueezy)
- **Transaction Fees**: Same as regular LemonSqueezy fees
- **Payout Fees**: Handled by LemonSqueezy (may have fees)
- **Maintenance**: Minimal (handled by LemonSqueezy)

---

## Migration Path (If Switching)

### Step 1: Enable LemonSqueezy Affiliates
1. Go to LemonSqueezy dashboard
2. Enable affiliate program
3. Set commission rates per product/variant
4. Configure payout settings

### Step 2: Update Checkout URLs
- Modify checkout creation to include affiliate parameter
- Detect affiliate from custom system
- Map custom affiliate IDs to LemonSqueezy affiliate IDs

### Step 3: Webhook Integration
- Add `affiliate_commission_created` webhook handler
- Sync commission data to custom system (if keeping for analytics)
- Or fully migrate to LemonSqueezy tracking

### Step 4: Affiliate Migration
- Export existing affiliates
- Import to LemonSqueezy (if possible)
- Or maintain both systems

### Step 5: Frontend Updates
- Update affiliate dashboard to show LemonSqueezy data
- Or redirect to LemonSqueezy affiliate portal
- Update referral link generation

---

## Decision Framework

### Choose Custom System If:
- ✅ You need tier-based commissions (Rookie→Master)
- ✅ You want recurring subscription commissions (0-10%)
- ✅ You need crypto payouts
- ✅ You want full control over affiliate experience
- ✅ You need custom branding
- ✅ You want 30-day hold periods

### Choose LemonSqueezy If:
- ✅ You want simple, flat commission rates
- ✅ You want to reduce maintenance
- ✅ You don't need crypto payouts
- ✅ You're okay with LemonSqueezy branding
- ✅ You want built-in tax reporting

### Choose Hybrid If:
- ✅ You want both simple and complex commission structures
- ✅ You want to test LemonSqueezy while keeping custom system
- ✅ You have different affiliate types (standard vs. premium)

---

## Next Steps

1. **Evaluate Current Needs**
   - Review current affiliate program performance
   - Assess commission structure requirements
   - Determine payout needs (crypto vs. PayPal only)

2. **Test LemonSqueezy Affiliates** (Optional)
   - Enable in LemonSqueezy dashboard
   - Create test affiliate
   - Test referral flow
   - Compare with custom system

3. **Decision Point**
   - Keep custom system (recommended for current setup)
   - Migrate to LemonSqueezy (if requirements match)
   - Implement hybrid (if both needed)

4. **Implementation** (If switching)
   - Follow migration path above
   - Update webhook handlers
   - Modify checkout URLs
   - Update frontend

---

## Resources

- [LemonSqueezy Affiliates Documentation](https://docs.lemonsqueezy.com/help/affiliates)
- [LemonSqueezy API Documentation](https://docs.lemonsqueezy.com/api)
- [Current Affiliate Implementation](./AFFILIATE_PAYOUTS_IMPLEMENTATION.md)
- [LemonSqueezy Dashboard](https://app.lemonsqueezy.com)

---

## Conclusion

**Recommendation: Keep the custom affiliate system**

The current custom system provides:
- ✅ More flexibility (tier-based commissions, recurring rates)
- ✅ Full control (branding, experience, payouts)
- ✅ Crypto support (important for modern affiliates)
- ✅ Already fully implemented and working
- ✅ Better suited for complex commission structures

LemonSqueezy's affiliate system is better suited for:
- Simple, flat commission structures
- Businesses that want minimal maintenance
- Standard affiliate programs without special requirements

Since you already have a fully functional custom system with advanced features (tiers, recurring commissions, crypto payouts), **keeping the custom system is the recommended approach**.

However, you could use LemonSqueezy affiliates as a **backup or alternative** for affiliates who prefer simpler tracking, or for specific campaigns where LemonSqueezy's built-in system is sufficient.


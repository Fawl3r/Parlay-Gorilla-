# Affiliate Payout System Implementation

## Overview

Complete affiliate payout system with PayPal and crypto support. The system automatically tracks commissions, processes them when ready, and provides admin tools for payout management.

## Features Implemented

### ✅ PayPal Payouts
- Full PayPal Payouts API integration
- Batch payout support
- Automatic payment processing
- Error handling and retry logic

### ✅ Crypto Payouts (Structure Ready)
- Service structure created
- Implementation guide included
- Ready for Circle API or other provider integration

### ✅ Commission Processing
- Automatic status transitions (PENDING → READY → PAID)
- 30-day hold period enforcement
- Scheduled job to process ready commissions daily

### ✅ Admin Dashboard
- View ready commissions
- Create payouts manually
- Process payouts (PayPal/crypto)
- View payout history
- Automatic batch processing

## Setup Instructions

### 1. PayPal Configuration

Add to your `.env` file:

```bash
# PayPal Payouts API (for affiliate payouts)
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret

# Environment (production uses api-m.paypal.com, sandbox uses api-m.sandbox.paypal.com)
ENVIRONMENT=production  # or development for sandbox
```

**Getting PayPal Credentials:**
1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/)
2. Create a new app
3. Get Client ID and Secret
4. Enable "Payouts" feature in your PayPal Business account
5. For production, complete business verification

### 2. Database Migration

The new `affiliate_payouts` table needs to be created. Run migrations:

```bash
cd backend
alembic revision --autogenerate -m "add_affiliate_payouts_table"
alembic upgrade head
```

### 3. Admin Routes

All payout management is available at:
- `GET /api/admin/payouts/ready-commissions` - View ready commissions
- `POST /api/admin/payouts/create` - Create a payout
- `POST /api/admin/payouts/process` - Process a payout
- `GET /api/admin/payouts` - List all payouts
- `GET /api/admin/payouts/{id}` - Get payout details
- `GET /api/admin/payouts/summary` - Payout statistics
- `POST /api/admin/payouts/process-ready` - Auto-process all ready commissions

## How It Works

### Commission Lifecycle

1. **PENDING**: Commission created when referred user makes purchase
   - 30-day hold period before becoming ready
   - Prevents payouts on refunded purchases

2. **READY**: Hold period expired, eligible for payout
   - Automatically moved to READY by scheduled job (daily at 4 AM)
   - Can be manually processed via admin dashboard

3. **PAID**: Commission has been paid out
   - Linked to payout record
   - Affiliate totals updated

### Payout Process

1. **Create Payout**: Admin selects commissions to pay
   - Minimum amount: $10 (configurable)
   - Requires affiliate payout email configured

2. **Process Payout**: Actually send the money
   - PayPal: Uses PayPal Payouts API
   - Crypto: Uses crypto_payout_service (to be implemented)

3. **Tracking**: Full history of all payouts
   - Status tracking (pending, processing, completed, failed)
   - Provider transaction IDs
   - Error logging

## Crypto Payout Implementation

### Difficulty Assessment

**EASY (1-2 days):**
- Circle API integration (recommended)
- Wyre API integration
- Coinbase Commerce (if they support payouts)

**MEDIUM (3-5 days):**
- Direct blockchain integration
- Multi-chain support
- Gas fee optimization

**HARD (1-2 weeks):**
- Full wallet infrastructure
- Smart contract integration
- Advanced batching and optimization

### Recommended: Circle API

1. **Sign up**: [Circle.com](https://circle.com)
2. **Get API credentials**: API key, wallet ID
3. **Add to settings**:
   ```python
   circle_api_key: Optional[str] = None
   circle_api_secret: Optional[str] = None
   circle_wallet_id: Optional[str] = None
   ```
4. **Implement**: See `backend/app/services/crypto_payout_service.py` for structure

### Implementation Steps

1. Choose provider (Circle recommended)
2. Get API credentials
3. Implement `_get_circle_access_token()` in `crypto_payout_service.py`
4. Implement `_create_circle_payout()` in `crypto_payout_service.py`
5. Update `process_crypto_payout()` to use these methods
6. Test in sandbox/testnet first
7. Add credentials to `.env`
8. Test with small amounts

## Scheduled Jobs

The system includes a scheduled job that runs daily at 4:00 AM:
- Processes commissions from PENDING → READY when hold period expires
- Logs results for monitoring

## Testing

### Test PayPal Payouts

1. Use PayPal sandbox credentials
2. Create test affiliate with PayPal email
3. Create test commissions
4. Manually set `ready_at` to past date
5. Process via admin dashboard
6. Verify in PayPal sandbox account

### Test Crypto Payouts

1. Implement crypto service (see guide above)
2. Use testnet addresses
3. Test with small amounts
4. Verify transaction on blockchain explorer

## Security Considerations

1. **API Keys**: Store securely in environment variables
2. **Webhooks**: PayPal can send webhook callbacks for payout status
3. **Rate Limiting**: Admin routes are rate-limited
4. **Audit Trail**: All payouts are logged with full details
5. **Minimum Amounts**: Prevents micro-payouts (default $10)

## Monitoring

- Check scheduled job logs for commission processing
- Monitor payout success/failure rates
- Track payout amounts and frequency
- Review error logs for failed payouts

## Future Enhancements

- [ ] PayPal webhook integration for payout status
- [ ] Automatic retry for failed payouts
- [ ] Multi-currency support
- [ ] Payout scheduling (e.g., monthly)
- [ ] Affiliate self-service payout requests
- [ ] Tax form generation (1099-NEC for US affiliates)

## Files Created/Modified

### New Files
- `backend/app/models/affiliate_payout.py` - Payout model
- `backend/app/services/payout_service.py` - PayPal payout service
- `backend/app/services/crypto_payout_service.py` - Crypto payout service (structure)
- `backend/app/api/routes/admin/payouts.py` - Admin payout routes

### Modified Files
- `backend/app/core/config.py` - Added PayPal config
- `backend/app/models/affiliate.py` - Added payouts relationship
- `backend/app/models/affiliate_commission.py` - Added payouts relationship
- `backend/app/models/__init__.py` - Exported new models
- `backend/app/services/scheduler.py` - Added commission processing job
- `backend/app/api/routes/admin/__init__.py` - Added payouts router

## Support

For issues or questions:
1. Check PayPal API documentation
2. Review error logs in admin dashboard
3. Test in sandbox environment first
4. Verify affiliate payout email is correct


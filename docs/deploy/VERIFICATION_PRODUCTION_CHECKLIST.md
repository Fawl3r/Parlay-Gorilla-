# Verification Records — Production Readiness Checklist

## ✅ Completed

- [x] Sui Move package published to mainnet
- [x] Package ID obtained and verified: `0xa93e3d74da1ecc6ef6fe331237f352946ff42567cbab6080c983fe489ff21574`
- [x] Test proof created successfully on mainnet
- [x] Database migration created (`026_add_verification_records.py`)
- [x] Backend API routes implemented
- [x] Worker implementation complete
- [x] Frontend UI updated with explorer links
- [x] Render deployment configuration updated
- [x] Environment variables documented

## ⚠️ Pre-Production Steps

### 1. Database Migration
- [ ] Run migration on production database:
  ```bash
  alembic upgrade head
  ```
- [ ] Verify `verification_records` table exists with correct schema

### 2. Render Environment Variables
Set these in the **verification worker** service on Render:

- [ ] `SUI_RPC_URL` = `https://fullnode.mainnet.sui.io:443`
- [ ] `SUI_PRIVATE_KEY` = `suiprivkey1qqtp62xx7nw390qtqwp0nx9ecjaju6tq8mwes4yrhe8f35ne6zc8jha6cfd`
- [ ] `SUI_PACKAGE_ID` = `0xa93e3d74da1ecc6ef6fe331237f352946ff42567cbab6080c983fe489ff21574`
- [ ] `SUI_MODULE` = `parlay_proof` (already set in render.yaml)
- [ ] `SUI_FUNCTION` = `create_proof` (already set in render.yaml)
- [ ] `DATABASE_URL` = (from Render PostgreSQL service)
- [ ] `REDIS_URL` = (from Render Redis service)
- [ ] `VERIFICATION_QUEUE_KEY` = `parlay_gorilla:queue:verify_saved_parlay` (already set)
- [ ] `VERIFICATION_MAX_ATTEMPTS` = `5` (already set)

### 3. Package Immutability ✅ COMPLETED
The package has been made immutable:

- [x] UpgradeCap object ID: `0xc1c19e4c5e40541f5b0c2953f2353866a20703a0e8af4333a411c545cb753bf4` (deleted)
- [x] Package made immutable
- [x] Transaction: `HLdpzNvESLQGcCN9o9DZ2tvGGPgj1etYDrvC4KsRhGhB`
- [x] Package is now immutable and cannot be upgraded

### 4. Worker Deployment
- [ ] Deploy verification worker service on Render
- [ ] Verify worker starts successfully
- [ ] Check worker logs for connection to Sui RPC
- [ ] Verify worker can consume from Redis queue

### 5. Backend Configuration
- [ ] Verify `verification_enabled=true` in backend config
- [ ] Verify `verification_network=mainnet` in backend config
- [ ] Test verification queue endpoint: `POST /api/parlays/{id}/verification/queue`

### 6. Frontend Configuration
- [ ] Verify explorer links work correctly
- [ ] Test verification flow end-to-end with a premium user
- [ ] Verify verification record page displays correctly

### 7. Testing
- [ ] Run smoke test: `python scripts/smoke_test_verification.py`
- [ ] Test with premium user account
- [ ] Verify proof appears on Sui Explorer
- [ ] Test retry mechanism for failed verifications
- [ ] Test quota/credit consumption logic

### 8. Monitoring
- [ ] Set up alerts for worker failures
- [ ] Monitor Sui transaction costs
- [ ] Track verification success/failure rates
- [ ] Monitor gas costs (target: <$0.01 per proof)

### 9. Security
- [ ] Verify `SUI_PRIVATE_KEY` is stored securely (Render secrets)
- [ ] Verify private key is NOT in code or logs
- [ ] Review rate limiting on verification endpoints
- [ ] Verify premium user checks are working

### 10. Documentation
- [ ] Update user-facing docs (if needed)
- [ ] Document verification limits for premium users
- [ ] Document credit overage costs

## ✅ Completed Cleanup

1. **✅ Removed old Solana config** - `solana_cluster` and `solscan_base_url` removed from `backend/app/core/config.py`
2. **✅ Removed SolscanUrlBuilder usage** - Legacy Solana explorer code removed from `backend/app/api/routes/saved_parlays.py`
3. **Note**: `premium_inscriptions_per_month`, `inscription_cost_usd`, and `credits_cost_inscription` are still in config but are now used for verification records (legacy naming, but functionality is correct)

## 📝 Notes

- The package is published and working on mainnet
- Test proof created successfully: `DjUL4Uik3GTjxTHeDcZyBVrHTby3Eqgm2uNmRmSykvqa`
- Proof object: `0xcb464082944700066837d594dce9ba50d5b9a6dbe4c1e722f8bbf15a4e0e1236`
- Package can be made immutable (optional but recommended for production)

## 🎯 Ready for Production?

**Status: Almost Ready** ✅

The system is functionally complete and tested. Before going live:

1. ✅ Set environment variables in Render
2. ✅ Run database migration
3. ✅ Deploy worker service
4. ⚠️ Clean up old Solana/inscription config (non-blocking)
5. ⚠️ Make package immutable (optional but recommended)

Once these are done, the system is ready for production use.


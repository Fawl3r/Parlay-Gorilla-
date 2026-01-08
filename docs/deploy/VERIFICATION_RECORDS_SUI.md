# Verification Records — Sui Package Publish & Configuration (Internal)

This document is for operators/developers. It is **not user-facing**.

## What you are publishing

Move package: `sui/parlay_proof`

- Module: `parlay_gorilla::parlay_proof`
- Entry function: `create_proof(data_hash: vector<u8>, created_at: u64, ctx: &mut TxContext)`
- Object type: `parlay_gorilla::parlay_proof::Proof`
- Storage policy: **hash-only**, fixed-length 32-byte SHA-256, and **frozen at creation** (immutable).

## Network

Production target: **mainnet**.

## Publish steps

### 1) Ensure Sui CLI is installed and configured

- Confirm you can run:
  - `sui --version`
  - `sui client envs`
- Switch to mainnet (command may vary by CLI version):
  - `sui client switch --env mainnet`

### 2) Create or import the platform signing address

This address is used by the **verification worker** to pay gas and sign transactions.

- Create a new address (example; command may vary):
  - `sui client new-address ed25519`
- Or import an existing key into your key store.

**Security note:** Store the private key in your secrets manager and inject it only into the worker runtime.

### 3) Build the package

From repo root:

```bash
cd sui/parlay_proof
sui move build
```

### 4) Publish the package

```bash
cd sui/parlay_proof
sui client publish --gas-budget 200000000
```

Record the **Package ID** from the publish output. You'll use it as `SUI_PACKAGE_ID` for the verification worker.

**Published Package ID (mainnet):**
```
0xa93e3d74da1ecc6ef6fe331237f352946ff42567cbab6080c983fe489ff21574
```

**Publish Transaction:**
- Digest: `Gk5Gc5z3BiNJjGbHbmNDBdznuC1h7tfdoDyjQaUZje5k`
- Network: mainnet
- Status: ✅ Published and verified

### 5) Make the package non-upgradeable ✅ COMPLETED

The publish flow typically returns an **upgrade capability** object. To match "no admin control / no upgrades", the package has been made immutable.

**Immutable Transaction:**
- Digest: `HLdpzNvESLQGcCN9o9DZ2tvGGPgj1etYDrvC4KsRhGhB`
- UpgradeCap Object ID: `0xc1c19e4c5e40541f5b0c2953f2353866a20703a0e8af4333a411c545cb753bf4` (deleted)
- Status: ✅ Package is now immutable and cannot be upgraded

## Worker configuration

Set these environment variables on the **verification worker** service (Render worker):

- `SUI_RPC_URL`: mainnet RPC endpoint
- `SUI_PRIVATE_KEY`: platform key (never expose to the backend or frontend)
- `SUI_PACKAGE_ID`: published package id from Step 4 (mainnet: `0xa93e3d74da1ecc6ef6fe331237f352946ff42567cbab6080c983fe489ff21574`)
- `SUI_MODULE`: `parlay_proof`
- `SUI_FUNCTION`: `create_proof`

The worker will:
- compute SHA-256 hash bytes
- submit a transaction calling `create_proof`
- extract `tx_digest` and the created `Proof` object id from transaction effects
- store those identifiers in Postgres



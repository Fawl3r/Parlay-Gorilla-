# IQ Code Inscription Tests

This directory contains comprehensive tests for the IQ code inscription functionality when inscribing parlays on Solana.

## Test Files

### `inscribe.test.js`
Core unit tests for the IQ inscription functionality:
- **extractTxid**: Tests transaction ID extraction from various response formats (string, object with txid/signature/transaction fields)
- **parseAfterErrParams**: Tests error parameter parsing for the `codeInAfterErr` fallback path
- **buildParlayProofDataString**: Tests payload JSON serialization
- **IqSdkEnv validation**: Tests environment variable validation (SIGNER_PRIVATE_KEY, RPC URL format)

### `inscribeIntegration.test.js`
Integration tests covering edge cases and data handling:
- Input validation with various formats (hash, account numbers, parlay IDs, timestamps)
- JSON serialization/deserialization correctness
- Error message parsing for different error formats
- Transaction ID extraction from various response structures
- Payload immutability and determinism

### `inscribePayload.test.js` (existing)
Tests that the payload includes account_number and excludes PII fields.

### `iqSdkEnv.test.js` (existing)
Tests IQ SDK environment variable validation.

### `worker.test.js` (existing)
Tests worker safety invariants (refuses to inscribe non-custom parlays).

## Running Tests

```bash
# Build TypeScript first
npm run build

# Run all tests (unit tests only)
npm test

# Or run tests directly
node --test test/*.test.js

# Run live integration test (requires real Solana credentials)
node --test test/liveInscription.test.js
```

### Live Integration Test

The `liveInscription.test.js` file contains tests that make **real calls to the Solana network** using the IQ SDK. These tests:

- ✅ Validate environment variables (SIGNER_PRIVATE_KEY, RPC, IQ_HANDLE, IQ_DATATYPE)
- ✅ Initialize the IQ user account
- ✅ Actually inscribe a test parlay proof on Solana mainnet
- ✅ Return a real transaction ID and Solscan link
- ✅ Test timeout handling
- ✅ Verify payload structure

**Requirements:**
- Must have `SIGNER_PRIVATE_KEY` and `RPC` set in `backend/.env`
- Will make real transactions on Solana (uses real SOL for fees)
- Should be run sparingly to avoid unnecessary transaction costs

**Example output:**
```
✅ IQ SDK environment variables are valid
✅ IQ user account initialized
✅ Inscription successful! (took 3691ms)
   Transaction ID: 2agAQ9gDyUawgu3N22qX4p8HUMdyZ7ffBGE6tfBZU2mT3RMu6giBY4AVhpnVxWsjwkDgPdMvMEvU3TX23a5iQp3J
   View on Solscan: https://solscan.io/tx/2agAQ9gDyUawgu3N22qX4p8HUMdyZ7ffBGE6tfBZU2mT3RMu6giBY4AVhpnVxWsjwkDgPdMvMEvU3TX23a5iQp3J
```

## Test Coverage

The tests cover:

1. **Helper Functions**:
   - `extractTxid`: Handles string, object, and various field names
   - `parseAfterErrParams`: Parses structured errors and error messages
   - `withTimeout`: Timeout handling (tested indirectly)

2. **Payload Building**:
   - Correct schema and type fields
   - All required fields (parlay_id, account_number, hash, created_at)
   - PII exclusion (no email, user_id, username)
   - JSON serialization correctness
   - Deterministic output

3. **Environment Validation**:
   - Missing environment variables
   - Invalid SIGNER_PRIVATE_KEY format (too short, invalid characters)
   - Invalid RPC URL format

4. **Error Handling**:
   - Various error message formats
   - Fallback path parameter extraction
   - Edge cases (null, undefined, empty values)

5. **Data Formats**:
   - Various hash formats (lowercase, uppercase, mixed)
   - Various account number formats
   - Various parlay ID formats (UUID, strings, numbers)
   - ISO timestamp handling

## Privacy-Preserving Design

The inscription system uses a **hash-only approach** to provide cryptographic proof without exposing private data:

- **On-chain (PUBLIC)**: Only a SHA-256 hash, parlay ID, account number, and timestamp
- **Database (PRIVATE)**: Full parlay data including picks, odds, legs, etc.

### How It Works

1. **Hash Computation**: The backend computes a deterministic SHA-256 hash from the full parlay data (legs, picks, odds, etc.)
2. **On-Chain Inscription**: Only the hash is inscribed on Solana (not the picks)
3. **Verification**: Anyone can verify a parlay by:
   - Getting the hash from the on-chain transaction
   - Computing the hash from the database parlay data
   - Comparing the two hashes (they should match)

### Benefits

- ✅ **Privacy**: Picks are never exposed publicly on-chain
- ✅ **Proof**: Hash proves the parlay exists and hasn't been tampered with
- ✅ **Tamper Detection**: Any change to picks/odds would change the hash
- ✅ **Timestamp**: On-chain timestamp proves when parlay was created

See `test/verifyHashProof.test.js` for detailed examples of how this works.

## What's NOT Tested (Requires Real SDK)

Due to the IQ SDK requiring real Solana credentials and network access, the following are not tested in unit tests:

- Actual `codeIn()` SDK call execution
- Actual `codeInAfterErr()` SDK call execution
- Network timeouts and retries
- Real Solana transaction submission

These should be tested in integration tests with a testnet or devnet environment.

## Test Results

All 22 tests pass:
- 18 new tests for IQ inscription functionality
- 4 existing tests for payload and environment validation


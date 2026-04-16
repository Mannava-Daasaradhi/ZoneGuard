# Feature 04 — ZeroKnow KYC: Change Log & Integration Guide

**Feature:** Zero-Knowledge Proof Identity Layer (ZeroKnow KYC)  
**Status:** Complete — additive only, no existing files modified  
**Author:** Feature 04 session  
**Date:** 2026-04-16  

---

## Overview

ZeroKnow KYC adds a privacy-preserving identity verification layer using
Circom circuits and Groth16 proofs on the BN254 curve.

**Core guarantee:** the server verifies that a prover knows a valid Amazon
Flex Rider ID *without ever receiving, processing, or storing the ID itself.*
Only three values are stored per verified identity:

| Stored | Not Stored |
|--------|-----------|
| `riderIDHash` — Poseidon(riderIDField) | Rider ID (plain-text) |
| `nullifier` — Poseidon(riderIDField, salt) | `riderIDField` (encoded integer) |
| `proofTimestamp` — UTC datetime | `salt` |
| | The proof itself (π_A, π_B, π_C) |

---

## Files Added

```
ZoneGuard/
├── .env.feature-04.example               ← All FEATURE04_* env vars documented
├── zk_circuits/
│   ├── package.json                      ← npm dependencies + build scripts
│   ├── flex_rider_proof.circom           ← Circom 2.1.6 circuit (main circuit)
│   └── scripts/
│       └── generate_proof.js             ← Client-side proof generation (snarkjs)
└── backend/
    ├── features/
    │   └── feature_04/
    │       ├── __init__.py               ← Exports router for main.py integration
    │       ├── models.py                 ← ZKProof SQLAlchemy model (own Base)
    │       ├── zk_verifier.py            ← Python Groth16 verifier (py_ecc)
    │       ├── zk_router.py              ← FastAPI router (POST /api/v1/zk/*)
    │       └── CHANGES.md                ← This file
    └── db/migrations/versions/
        └── 004_zk_kyc.py                ← Alembic migration (additive only)
```

**Files NOT modified:** `backend/main.py`, `backend/api/router.py`,
`backend/models/zones.py`, any existing auth files, any other feature directory.

---

## Integration Steps

### Step 1 — Install Python dependency

```bash
# In the backend virtualenv / Docker image:
pip install py_ecc>=6.0.0
```

Add to `backend/requirements.txt`:
```
py_ecc>=6.0.0
```

### Step 2 — Register the router in `backend/main.py`

Add **two lines** to `backend/main.py` (no other changes needed):

```python
# At the top, with the other router imports:
from features.feature_04.zk_router import router as zk_router

# After the existing app.include_router(...) calls:
app.include_router(zk_router)
```

The new endpoint will then appear at `POST /api/v1/zk/verify-rider` and
`GET /api/v1/zk/status/{rider_id_hash}`, and in the `/docs` Swagger UI
under the **zk-kyc** tag.

Also update the root endpoint's `endpoints` dict for discoverability:

```python
"endpoints": {
    ...existing entries...,
    "zk_kyc": "/api/v1/zk",   # ← add this line
},
```

### Step 3 — Run the Alembic migration

```bash
cd backend
alembic upgrade head
```

This applies `004_zk_kyc.py`, which creates the `zk_proofs` table.
It chains from `003_eshram_kyc` and is fully reversible with `alembic downgrade 003_eshram_kyc`.

> **Development shortcut:** The router calls `ZKBase.metadata.create_all()`
> on each request if the table doesn't exist, so the migration is optional
> for local development.

### Step 4 — Build the ZK circuit (one-time trusted setup)

```bash
cd zk_circuits

# Install Node.js dependencies
npm install

# Install circom compiler globally (requires Rust)
cargo install circom

# Compile the circuit to R1CS + WASM
npm run build:circuit

# Download the Powers of Tau file (Hermez perpetual ceremony, ~55 MB)
curl -o pot12_final.ptau "$FEATURE04_PTAU_URL"

# Phase 2 trusted setup (generates the proving key)
npm run setup:phase2
npm run setup:phase2:contribute

# Export the verification key for the Python verifier
npm run export:vkey
# → Writes: build/verification_key.json

# Optional: export a Solidity verifier (for on-chain use)
npm run export:solidity
```

Set `FEATURE04_ZK_VKEY_PATH` in your `.env` to the absolute path of
`zk_circuits/build/verification_key.json`.

### Step 5 — Set environment variables

```bash
cp .env.feature-04.example .env.feature-04
# Edit FEATURE04_ZK_VKEY_PATH to the absolute path of verification_key.json
# All other defaults are suitable for local development
```

---

## API Reference

### `POST /api/v1/zk/verify-rider`

Verify a Groth16 ZK proof for a Flex Rider identity.

**Request body:**
```json
{
  "proof": {
    "pi_a": ["<x>", "<y>", "1"],
    "pi_b": [["<x0>", "<x1>"], ["<y0>", "<y1>"], ["1", "0"]],
    "pi_c": ["<x>", "<y>", "1"],
    "protocol": "groth16",
    "curve": "bn128"
  },
  "publicSignals": [
    "<riderIDHash as decimal string>",
    "<nullifier as decimal string>",
    "65536"
  ]
}
```

**Success response (HTTP 200):**
```json
{
  "zkProofId":      "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "riderIDHash":    "0x1a2b3c...",
  "nullifier":      "0xdeadbeef...",
  "proofTimestamp": "2026-04-16T10:30:00+00:00"
}
```

**Error responses:**

| HTTP | `error` field | Cause |
|------|--------------|-------|
| 400 | `invalid_proof` | Proof fails Groth16 verification |
| 400 | (Pydantic) | Malformed request body |
| 409 | `duplicate_nullifier` | Same identity already verified |
| 500 | `db_error` | Database commit failure |

---

### `GET /api/v1/zk/status/{rider_id_hash}`

Check whether a `riderIDHash` has a verified proof on file.

**Success response (HTTP 200):**
```json
{
  "zkProofId":      "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "riderIDHash":    "0x1a2b3c...",
  "nullifier":      "0xdeadbeef...",
  "proofTimestamp": "2026-04-16T10:30:00+00:00",
  "consumed":       false,
  "revoked":        false,
  "zkVerified":     true
}
```

**404** if no proof exists for the given hash.

---

## Connecting to the Rider Onboarding Flow

The ZeroKnow KYC endpoint is designed to slot into the existing rider
onboarding flow **without modifying any existing files**.  Here is the
recommended integration pattern:

### Pattern: ZK-first onboarding

```
Client                          ZK Endpoint              Riders Endpoint
  │                                  │                        │
  │── generate_proof.js ──────────▶  │                        │
  │   (local, Rider ID never sent)   │                        │
  │                                  │                        │
  │── POST /api/v1/zk/verify-rider ─▶│                        │
  │   {proof, publicSignals}         │── verify Groth16 ───▶  │
  │                                  │── store {hash,null} ─▶ │
  │◀─ {zkProofId, riderIDHash} ──────│                        │
  │                                  │                        │
  │── POST /api/v1/riders/register ─────────────────────────▶ │
  │   {rider_id, name, ...,          │                        │
  │    zk_proof_id: zkProofId}       │                        │
  │                                  │                        │
  │                  (riders endpoint calls GET /api/v1/zk/status/{riderIDHash}
  │                   to confirm zkVerified=true before completing registration)
```

### Linking a ZK proof to a Rider record

To mark a rider as ZK-KYC verified without storing their Rider ID,
the `riders` router can:

1. Accept an optional `zk_proof_id` in the register/KYC payload.
2. Call `GET /api/v1/zk/status/{riderIDHash}` internally (or query the
   `zk_proofs` table directly) to confirm `zkVerified=true`.
3. Set `rider.kyc_verified = True` if the proof is valid and not consumed.
4. Mark the proof as consumed: `UPDATE zk_proofs SET consumed=true WHERE id=?`.

This keeps the Rider ID entirely client-side while giving the server
cryptographic assurance of identity validity.

**Example addition to `backend/schemas/rider.py`** (new optional field only):
```python
class RiderRegister(BaseModel):
    ...existing fields...
    zk_proof_id: Optional[str] = None   # UUID from POST /api/v1/zk/verify-rider
```

No changes to `backend/models/rider.py` are required — `kyc_verified`
already exists on the `Rider` model and can be set to `True` upon
successful ZK proof linkage.

---

## Security Considerations

### Nullifier deduplication
Each unique `(riderIDField, salt)` pair produces a unique nullifier.
The server enforces uniqueness at the DB level (`UNIQUE INDEX ix_zk_proofs_nullifier`).
A rider cannot verify twice with the same salt; choosing a different salt
produces a different nullifier (and a different, unlinked proof record).

### Replay attacks
The nullifier prevents replay: submitting the same `{proof, publicSignals}`
twice will be rejected with HTTP 409 on the second attempt.

### Entropy constraint
The circuit enforces `riderIDField > MIN_ENTROPY` (default 65536).
This prevents degenerate IDs (empty string, "0", "1") from generating
valid proofs, providing a weak format sanity check at the ZK layer.

### Verification key custody
The `verification_key.json` must be treated as public but immutable.
If the trusted setup is compromised, a new ceremony must be run and the
`FEATURE04_ZK_VKEY_PATH` updated.  Old proofs remain valid against the
old key; the DB nullifier table prevents re-submission under the new key
for already-verified identities.

### Pure-Python pairing performance
The `py_ecc` BN254 pairing takes ~1–3 seconds in pure Python per proof.
For production throughput, consider:
- Running a snarkjs Node.js microservice as a subprocess verifier.
- Using `rapidsnark` (C++) as a gRPC sidecar.
- Caching verification results (the nullifier uniqueness check already
  prevents redundant verifications for duplicate submissions).

---

## Testing

### Unit test the verifier

```python
# tests/feature_04/test_zk_verifier.py

from features.feature_04.zk_verifier import validate_public_signals

def test_valid_signals():
    validate_public_signals(["12345", "67890", "65536"], min_entropy=65536)

def test_wrong_min_entropy():
    with pytest.raises(ValueError, match="minEntropy"):
        validate_public_signals(["12345", "67890", "99999"], min_entropy=65536)

def test_wrong_count():
    with pytest.raises(ValueError, match="3 public signals"):
        validate_public_signals(["a", "b"], min_entropy=65536)
```

### End-to-end test with a real proof

```bash
cd zk_circuits
node scripts/generate_proof.js --riderId "AMZFLEX-BLR-04821" --verify

# Then POST the output to the local API:
curl -X POST http://localhost:8000/api/v1/zk/verify-rider \
  -H "Content-Type: application/json" \
  -d @output/api_payload.json
```

---

## Env Vars Quick Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FEATURE04_DATABASE_URL` | (shared `DATABASE_URL`) | PostgreSQL URL for `zk_proofs` table |
| `FEATURE04_DEBUG` | `false` | SQLAlchemy verbose logging |
| `FEATURE04_ZK_VKEY_PATH` | `<repo>/zk_circuits/build/verification_key.json` | Path to verification key |
| `FEATURE04_ZK_MIN_ENTROPY` | `65536` | Minimum Rider ID entropy enforced by circuit |
| `FEATURE04_ZK_NULLIFIER_TTL_DAYS` | `365` | Nullifier retention period |
| `FEATURE04_PTAU_URL` | Hermez S3 URL | Powers of Tau download URL |
| `FEATURE04_PTAU_PATH` | `zk_circuits/pot12_final.ptau` | Local .ptau path |
| `FEATURE04_CIRCUIT_WASM_PATH` | `zk_circuits/build/...wasm` | Circuit WASM path |
| `FEATURE04_CIRCUIT_ZKEY_PATH` | `zk_circuits/build/...zkey` | Final .zkey path |
| `FEATURE04_RATE_LIMIT_PER_MIN` | `10` | API rate limit (proofs/min/IP) |
| `FEATURE04_ALLOW_DEV_BYPASS` | `false` | Dev mode pairing bypass (**never true in prod**) |

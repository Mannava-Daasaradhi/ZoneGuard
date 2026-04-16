"""
backend/features/feature_04/zk_router.py
=========================================
ZeroKnow KYC — FastAPI router for ZK proof verification.

Exposes:
    POST /api/v1/zk/verify-rider

STRICT RULES followed:
- Does NOT modify backend/api/router.py.  Integration is additive (see CHANGES.md).
- Does NOT import from other feature_NN directories.
- Uses its own DB session factory built from FEATURE04_DATABASE_URL (or falls
  back to the shared database_url for zero-friction development).
- Stores ONLY {riderIDHash, nullifier, proofTimestamp} — the Rider ID itself
  is never received, logged, or stored.

INTEGRATION (see CHANGES.md for full instructions):
    In backend/main.py, add:
        from features.feature_04.zk_router import router as zk_router
        app.include_router(zk_router)
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from features.feature_04.models import ZKBase, ZKProof
from features.feature_04.zk_verifier import verify_rider_proof

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router definition
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/zk",
    tags=["zk-kyc"],
)

# ---------------------------------------------------------------------------
# Database session factory (Feature 04 specific)
#
# Uses FEATURE04_DATABASE_URL if set, otherwise falls back to the shared
# DATABASE_URL.  This allows Feature 04 to use a separate DB in production
# while sharing the dev database for convenience.
# ---------------------------------------------------------------------------

def _get_db_url() -> str:
    url = os.getenv("FEATURE04_DATABASE_URL") or os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://zoneguard:zoneguard_dev@localhost:5432/zoneguard",
    )
    # Normalize: sqlalchemy async driver requires +asyncpg
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_engine = create_async_engine(
    _get_db_url(),
    echo=os.getenv("FEATURE04_DEBUG", "false").lower() == "true",
    pool_size=3,
    max_overflow=5,
)

_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_zk_db() -> AsyncSession:
    """FastAPI dependency: yields an async DB session for Feature 04."""
    async with _session_factory() as session:
        yield session


async def ensure_zk_table_exists(session: AsyncSession) -> None:
    """
    Idempotently create the zk_proofs table if it does not exist.

    In production, use the Alembic migration (004_zk_kyc.py) instead.
    This function is a development convenience — it runs on every request
    but is effectively a no-op after the first call.
    """
    async with _engine.begin() as conn:
        await conn.run_sync(ZKBase.metadata.create_all)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class Groth16Proof(BaseModel):
    """
    Groth16 proof as output by snarkjs.

    pi_a, pi_b, pi_c are lists of decimal-string field elements.
    protocol must be "groth16" and curve must be "bn128" / "bn254".
    """
    pi_a: list[str] = Field(..., description="G1 proof element π_A")
    pi_b: list[list[str]] = Field(..., description="G2 proof element π_B")
    pi_c: list[str] = Field(..., description="G1 proof element π_C")
    protocol: str  = Field(default="groth16")
    curve: str     = Field(default="bn128")

    @field_validator("protocol")
    @classmethod
    def must_be_groth16(cls, v: str) -> str:
        if v.lower() != "groth16":
            raise ValueError(f"Unsupported proof protocol '{v}'. Only 'groth16' is accepted.")
        return v.lower()

    @field_validator("curve")
    @classmethod
    def must_be_bn128(cls, v: str) -> str:
        if v.lower() not in ("bn128", "bn254"):
            raise ValueError(
                f"Unsupported curve '{v}'. Expected 'bn128' or 'bn254' (BN254/alt_bn128)."
            )
        return v.lower()


class VerifyRiderRequest(BaseModel):
    """
    Request body for POST /api/v1/zk/verify-rider.

    The client sends:
        proof         — Groth16 proof produced by snarkjs / generate_proof.js
        publicSignals — [riderIDHash, nullifier, minEntropy] as decimal strings

    The client MUST NOT send the Rider ID, riderIDField, or salt.
    """
    proof: Groth16Proof = Field(
        ...,
        description="Groth16 ZK proof from snarkjs (pi_a, pi_b, pi_c, protocol, curve)"
    )
    publicSignals: list[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Public circuit inputs: [riderIDHash, nullifier, minEntropy] as decimal strings"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "proof": {
                "pi_a": ["<decimal_str_x>", "<decimal_str_y>", "1"],
                "pi_b": [
                    ["<x0>", "<x1>"],
                    ["<y0>", "<y1>"],
                    ["1", "0"]
                ],
                "pi_c": ["<decimal_str_x>", "<decimal_str_y>", "1"],
                "protocol": "groth16",
                "curve": "bn128",
            },
            "publicSignals": [
                "<riderIDHash as decimal string>",
                "<nullifier as decimal string>",
                "65536",
            ],
        }
    }}


class VerifyRiderResponse(BaseModel):
    """
    Response from POST /api/v1/zk/verify-rider.

    On success (HTTP 200):
        zkProofId      — UUID of the stored ZK proof record
        riderIDHash    — hex commitment to the Rider ID (for onboarding linkage)
        nullifier      — hex nullifier (for deduplication)
        proofTimestamp — ISO-8601 UTC datetime of verification

    The rider onboarding flow can use riderIDHash to link this proof
    to a rider account (see CHANGES.md §Integration).
    """
    zkProofId: str      = Field(..., description="UUID of the stored ZK proof record")
    riderIDHash: str    = Field(..., description="Hex commitment: Poseidon(riderIDField)")
    nullifier: str      = Field(..., description="Hex nullifier: Poseidon(riderIDField, salt)")
    proofTimestamp: str = Field(..., description="ISO-8601 UTC datetime of server-side verification")

    model_config = {"json_schema_extra": {
        "example": {
            "zkProofId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "riderIDHash": "0x1a2b3c4d...",
            "nullifier": "0xdeadbeef...",
            "proofTimestamp": "2026-04-16T10:30:00+00:00",
        }
    }}


# ---------------------------------------------------------------------------
# Endpoint: POST /api/v1/zk/verify-rider
# ---------------------------------------------------------------------------

@router.post(
    "/verify-rider",
    response_model=VerifyRiderResponse,
    status_code=status.HTTP_200_OK,
    summary="ZeroKnow KYC — Verify Flex Rider ZK Proof",
    description="""
Verify a zero-knowledge proof that a prover knows a valid Amazon Flex Rider ID
without revealing the ID itself.

**What this endpoint does:**
1. Validates the Groth16 proof structure and public signal ranges.
2. Runs BN254 pairing-based Groth16 verification against the server's verification key.
3. Rejects duplicate proofs (nullifier uniqueness enforced in DB).
4. Stores `{riderIDHash, nullifier, proofTimestamp}` — never the actual Rider ID.
5. Returns a `zkProofId` and `riderIDHash` that the onboarding flow can use
   to mark a rider as ZK-KYC verified without handling their Rider ID.

**Client-side proof generation:**
Use `zk_circuits/scripts/generate_proof.js` to generate `proof.json` and
`public.json` from the Rider ID locally, then send them to this endpoint.

**Privacy guarantee:**
The server never receives, processes, or logs the Rider ID in any form.
""",
    responses={
        200: {"description": "Proof verified successfully"},
        400: {"description": "Invalid proof format or public signals"},
        409: {"description": "Nullifier already used (duplicate submission)"},
        422: {"description": "Pydantic validation error (malformed request body)"},
        500: {"description": "Internal verification error (check server logs)"},
    },
)
async def verify_rider(
    payload: VerifyRiderRequest,
    db: AsyncSession = Depends(get_zk_db),
) -> VerifyRiderResponse:
    """
    POST /api/v1/zk/verify-rider

    Verify a Groth16 ZK proof for Flex Rider identity.
    """

    # ---- Ensure table exists (dev convenience; use migration in prod) ----
    await ensure_zk_table_exists(db)

    # ---- Convert Pydantic proof model to plain dict for verifier ----
    proof_dict: dict[str, Any] = {
        "pi_a":     payload.proof.pi_a,
        "pi_b":     payload.proof.pi_b,
        "pi_c":     payload.proof.pi_c,
        "protocol": payload.proof.protocol,
        "curve":    payload.proof.curve,
    }

    # ---- Run ZK proof verification ----
    logger.info(
        "ZK verify-rider: running proof verification | "
        "nullifier_prefix=%s...",
        payload.publicSignals[1][:12] if len(payload.publicSignals) > 1 else "?",
    )

    result = verify_rider_proof(
        proof=proof_dict,
        public_signals=payload.publicSignals,
    )

    if not result["valid"]:
        error_msg = result.get("error", "Proof verification failed.")
        logger.warning("ZK verify-rider: REJECTED | error=%s", error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_proof", "message": error_msg},
        )

    rider_id_hash: str = result["rider_id_hash"]
    nullifier: str     = result["nullifier"]

    # ---- Deduplication: check nullifier not already used ----
    existing_stmt = text(
        "SELECT id FROM zk_proofs WHERE nullifier = :nullifier AND revoked = false LIMIT 1"
    )
    existing_row = await db.execute(existing_stmt, {"nullifier": nullifier})
    existing = existing_row.fetchone()

    if existing is not None:
        logger.warning(
            "ZK verify-rider: DUPLICATE nullifier=%s... (existing proof_id=%s)",
            nullifier[:14],
            existing[0],
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "duplicate_nullifier",
                "message": (
                    "This identity has already submitted a verified ZK proof. "
                    "Each Rider ID can only generate one valid proof per nullifier."
                ),
            },
        )

    # ---- Store proof record (no Rider ID — hash + nullifier only) ----
    proof_id       = str(uuid.uuid4())
    proof_timestamp = datetime.now(timezone.utc)

    zk_record = ZKProof(
        id                  = proof_id,
        rider_id_hash       = rider_id_hash,
        nullifier           = nullifier,
        public_signals_json = json.dumps(payload.publicSignals),
        proof_timestamp     = proof_timestamp,
        consumed            = False,
        revoked             = False,
    )

    db.add(zk_record)

    try:
        await db.commit()
        await db.refresh(zk_record)
    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        logger.exception("ZK verify-rider: DB commit failed | %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "db_error",
                "message": "Failed to persist ZK proof record. Please retry.",
            },
        ) from exc

    logger.info(
        "ZK verify-rider: SUCCESS | proof_id=%s | rider_id_hash=%s...",
        proof_id,
        rider_id_hash[:14],
    )

    return VerifyRiderResponse(
        zkProofId      = proof_id,
        riderIDHash    = rider_id_hash,
        nullifier      = nullifier,
        proofTimestamp = proof_timestamp.isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoint: GET /api/v1/zk/status/{rider_id_hash}
# ---------------------------------------------------------------------------

@router.get(
    "/status/{rider_id_hash}",
    summary="ZeroKnow KYC — Check ZK proof status by riderIDHash",
    description="""
Check whether a given riderIDHash has a valid, non-revoked ZK proof on file.

Used by the rider onboarding flow to confirm ZK-KYC completion before
activating a policy.  The hash can be computed client-side from the Rider ID
using Poseidon without revealing the ID to the server.
""",
    responses={
        200: {"description": "Status returned"},
        404: {"description": "No proof found for this riderIDHash"},
    },
)
async def get_zk_status(
    rider_id_hash: str,
    db: AsyncSession = Depends(get_zk_db),
):
    """
    GET /api/v1/zk/status/{rider_id_hash}

    Returns ZK proof status for a given riderIDHash commitment.
    """
    await ensure_zk_table_exists(db)

    stmt = text(
        "SELECT id, nullifier, proof_timestamp, consumed, revoked "
        "FROM zk_proofs WHERE rider_id_hash = :hash AND revoked = false "
        "ORDER BY proof_timestamp DESC LIMIT 1"
    )
    row = await db.execute(stmt, {"hash": rider_id_hash})
    record = row.fetchone()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": f"No valid ZK proof found for riderIDHash {rider_id_hash!r}.",
            },
        )

    return {
        "zkProofId":      record[0],
        "riderIDHash":    rider_id_hash,
        "nullifier":      record[1],
        "proofTimestamp": record[2].isoformat() if record[2] else None,
        "consumed":       record[3],
        "revoked":        record[4],
        "zkVerified":     True,
    }

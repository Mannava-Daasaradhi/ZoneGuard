"""
backend/features/feature_04/zk_verifier.py
==========================================
ZeroKnow KYC — Python Groth16 proof verifier.

Verifies snarkjs Groth16 proof output in pure Python using the BN254
(alt_bn128) pairing curve.  No Node.js or snarkjs subprocess required
at verification time — the server verifies using the exported
verification_key.json produced during the trusted setup ceremony.

VERIFICATION ALGORITHM (Groth16 on BN254):
    Given:
        π = (π_A, π_B, π_C)     — the proof
        x = [x_1 ... x_l]       — public signals
        vk = (α, β, γ, δ, IC)   — verification key

    Compute:
        L = IC[0] + Σ_{i=1}^{l} x_i · IC[i]    (linear combination)

    Accept iff:
        e(π_A, π_B) == e(α, β) · e(L, γ) · e(π_C, δ)

    where e() is the BN254 optimal ate pairing.

DEPENDENCIES:
    py_ecc>=6.0.0   (pip install py_ecc)
    Pure-Python BN254 pairing from Ethereum's py_ecc library.
    This is the same curve used by snarkjs/circom.

ENVIRONMENT VARIABLES (all prefixed FEATURE04_):
    FEATURE04_ZK_VKEY_PATH     Path to verification_key.json
    FEATURE04_ZK_MIN_ENTROPY   Minimum entropy value (default: 65536)
    FEATURE04_ZK_NULLIFIER_TTL_DAYS  Days before nullifiers can be pruned (default: 365)
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BN254 curve constants
# ---------------------------------------------------------------------------

# BN254 scalar field prime (order of G1/G2)
BN254_PRIME = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# ---------------------------------------------------------------------------
# Lazy import of py_ecc to give a clear error if not installed
# ---------------------------------------------------------------------------

def _require_py_ecc():
    """Import py_ecc, raising ImportError with install instructions if missing."""
    try:
        from py_ecc.bn128 import (
            G1, G2, pairing, multiply, add, neg, FQ, FQ2, FQ12,
        )
        return G1, G2, pairing, multiply, add, neg, FQ, FQ2, FQ12
    except ImportError as exc:
        raise ImportError(
            "py_ecc is required for ZK proof verification.\n"
            "Install it with:  pip install py_ecc>=6.0.0\n"
            f"Original error: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Verification key loading
# ---------------------------------------------------------------------------

def load_verification_key(vkey_path: str | Path) -> dict[str, Any]:
    """
    Load and parse a snarkjs verification_key.json file.

    The JSON format produced by `snarkjs zkey export verificationkey` is:
    {
      "protocol": "groth16",
      "curve": "bn128",
      "nPublic": <int>,
      "vk_alpha_1": [<x>, <y>, "1"],
      "vk_beta_2":  [[<x0>, <x1>], [<y0>, <y1>], ["1", "0"]],
      "vk_gamma_2": [[...], [...], [...]],
      "vk_delta_2": [[...], [...], [...]],
      "vk_alphabeta_12": [...],   (precomputed pairing, not used in Python path)
      "IC": [[<x>, <y>, "1"], ...]
    }

    Returns the raw dict — callers convert to py_ecc points as needed.

    Raises:
        FileNotFoundError  — vkey_path does not exist
        ValueError         — JSON is malformed or not a groth16/bn128 key
    """
    vkey_path = Path(vkey_path)
    if not vkey_path.exists():
        raise FileNotFoundError(
            f"Verification key not found at: {vkey_path}\n"
            f"Generate it with:\n"
            f"  snarkjs zkey export verificationkey build/flex_rider_proof_final.zkey "
            f"build/verification_key.json"
        )

    with vkey_path.open("r", encoding="utf-8") as fh:
        vkey = json.load(fh)

    if vkey.get("protocol") != "groth16":
        raise ValueError(
            f"Unsupported protocol '{vkey.get('protocol')}' in verification key. "
            f"Expected 'groth16'."
        )
    if vkey.get("curve") not in ("bn128", "BN128", "bn254", "BN254"):
        raise ValueError(
            f"Unsupported curve '{vkey.get('curve')}' in verification key. "
            f"Expected 'bn128' / 'bn254'."
        )

    logger.debug("Verification key loaded from %s (nPublic=%s)", vkey_path, vkey.get("nPublic"))
    return vkey


# ---------------------------------------------------------------------------
# Point parsing helpers
# ---------------------------------------------------------------------------

def _parse_g1(raw: list) -> tuple:
    """
    Parse a snarkjs G1 point (list of 3 decimal strings) into a py_ecc tuple.
    raw = ["<x>", "<y>", "1"]
    Returns (FQ(x), FQ(y)) or None (point at infinity).
    """
    G1, G2, pairing, multiply, add, neg, FQ, FQ2, FQ12 = _require_py_ecc()
    x, y = int(raw[0]), int(raw[1])
    if x == 0 and y == 0:
        return None  # infinity
    return (FQ(x), FQ(y))


def _parse_g2(raw: list) -> tuple:
    """
    Parse a snarkjs G2 point into a py_ecc FQ2 tuple.
    raw = [[x0, x1], [y0, y1], ["1", "0"]]
    snarkjs uses the convention FQ2([a0, a1]) = a0 + a1*i.
    """
    G1, G2, pairing, multiply, add, neg, FQ, FQ2, FQ12 = _require_py_ecc()
    x_raw, y_raw = raw[0], raw[1]
    x = FQ2([int(x_raw[0]), int(x_raw[1])])
    y = FQ2([int(y_raw[0]), int(y_raw[1])])
    return (x, y)


# ---------------------------------------------------------------------------
# Core: Groth16 verification
# ---------------------------------------------------------------------------

def verify_groth16_proof(
    vkey: dict[str, Any],
    proof: dict[str, Any],
    public_signals: list[str],
) -> bool:
    """
    Verify a Groth16 proof on BN254 using pure Python (py_ecc).

    This implements the standard Groth16 verification equation:
        e(π_A, π_B) == e(vk_alpha, vk_beta) · e(L, vk_gamma) · e(π_C, vk_delta)

    where L = IC[0] + Σ x_i · IC[i]

    Args:
        vkey:           Parsed verification key dict (from load_verification_key)
        proof:          snarkjs proof dict with keys "pi_a", "pi_b", "pi_c"
        public_signals: List of decimal strings, one per public circuit input
                        (order: [riderIDHash, nullifier, minEntropy])

    Returns:
        True  — proof is valid (the prover knows a Rider ID satisfying all constraints)
        False — proof is invalid

    Raises:
        ImportError  — py_ecc not installed
        ValueError   — malformed proof or public signals
        Exception    — unexpected pairing error
    """
    G1, G2, pairing, multiply, add, neg, FQ, FQ2, FQ12 = _require_py_ecc()

    # ---- Parse verification key points ----
    vk_alpha = _parse_g1(vkey["vk_alpha_1"])
    vk_beta  = _parse_g2(vkey["vk_beta_2"])
    vk_gamma = _parse_g2(vkey["vk_gamma_2"])
    vk_delta = _parse_g2(vkey["vk_delta_2"])
    ic       = [_parse_g1(pt) for pt in vkey["IC"]]

    n_public = vkey.get("nPublic", len(ic) - 1)
    if len(public_signals) != n_public:
        raise ValueError(
            f"Expected {n_public} public signals, got {len(public_signals)}. "
            f"Circuit has {n_public} public inputs."
        )

    # ---- Parse proof points ----
    pi_a = _parse_g1(proof["pi_a"])
    pi_b = _parse_g2(proof["pi_b"])
    pi_c = _parse_g1(proof["pi_c"])

    # ---- Compute L = IC[0] + Σ x_i * IC[i] ----
    L = ic[0]
    for i, sig_str in enumerate(public_signals):
        x_i = int(sig_str) % BN254_PRIME
        term = multiply(ic[i + 1], x_i)
        L = add(L, term)

    # ---- Verify pairing equation ----
    # e(π_A, π_B) == e(α, β) · e(L, γ) · e(π_C, δ)
    # Rearranged (all pairings on left, product must be identity):
    # e(-π_A, π_B) · e(α, β) · e(L, γ) · e(π_C, δ) == 1
    #
    # We compute each pairing and multiply in FQ12.
    neg_pi_a = neg(pi_a)

    p1 = pairing(pi_b,   neg_pi_a)   # e(-π_A, π_B)
    p2 = pairing(vk_beta, vk_alpha)  # e(α, β)  — note: pairing(G2, G1) convention
    p3 = pairing(vk_gamma, L)        # e(L, γ)
    p4 = pairing(vk_delta, pi_c)     # e(π_C, δ)

    result = p1 * p2 * p3 * p4

    # In FQ12, the identity element is the multiplicative identity (1, 0, 0, ...)
    # py_ecc represents it as FQ12.one()
    identity = FQ12.one()
    is_valid = (result == identity)

    logger.debug(
        "Groth16 verification result: %s (public_signals=%s)",
        is_valid,
        public_signals,
    )
    return is_valid


# ---------------------------------------------------------------------------
# High-level: validate public signals before calling the pairing check
# ---------------------------------------------------------------------------

def validate_public_signals(
    public_signals: list[str],
    min_entropy: int | None = None,
) -> None:
    """
    Sanity-check the public signals BEFORE running the expensive pairing.

    Checks:
        1. Exactly 3 signals present: [riderIDHash, nullifier, minEntropy]
        2. All signals are valid decimal integers in [0, BN254_PRIME)
        3. minEntropy (signal[2]) matches the expected server-side value

    Args:
        public_signals:  List of decimal strings from the proof
        min_entropy:     Expected minimum entropy (from env var FEATURE04_ZK_MIN_ENTROPY)
                         Defaults to 65536 if None.

    Raises:
        ValueError  — if any check fails (descriptive message for API response)
    """
    if min_entropy is None:
        min_entropy = int(os.getenv("FEATURE04_ZK_MIN_ENTROPY", "65536"))

    if len(public_signals) != 3:
        raise ValueError(
            f"Expected exactly 3 public signals [riderIDHash, nullifier, minEntropy], "
            f"got {len(public_signals)}."
        )

    for i, sig in enumerate(public_signals):
        try:
            val = int(sig)
        except (ValueError, TypeError):
            raise ValueError(
                f"public_signals[{i}] is not a valid integer: {sig!r}"
            )
        if val < 0 or val >= BN254_PRIME:
            raise ValueError(
                f"public_signals[{i}] = {val} is out of BN254 scalar field range."
            )

    # Signal index 2 is minEntropy — verify it matches the server's expected value
    claimed_min_entropy = int(public_signals[2])
    if claimed_min_entropy != min_entropy:
        raise ValueError(
            f"public_signals[2] (minEntropy) = {claimed_min_entropy} does not match "
            f"server-expected value {min_entropy}. "
            f"The proof was generated with a different entropy threshold."
        )


# ---------------------------------------------------------------------------
# Public API used by zk_router.py
# ---------------------------------------------------------------------------

def get_vkey_path() -> Path:
    """
    Resolve the verification key path from FEATURE04_ZK_VKEY_PATH env var.
    Falls back to a conventional relative path for local development.
    """
    env_path = os.getenv("FEATURE04_ZK_VKEY_PATH")
    if env_path:
        return Path(env_path)

    # Convention: vkey lives two levels above backend/ in zk_circuits/build/
    repo_root = Path(__file__).resolve().parents[3]
    fallback   = repo_root / "zk_circuits" / "build" / "verification_key.json"
    logger.debug(
        "FEATURE04_ZK_VKEY_PATH not set, using fallback: %s", fallback
    )
    return fallback


def verify_rider_proof(
    proof: dict[str, Any],
    public_signals: list[str],
) -> dict[str, Any]:
    """
    End-to-end ZK proof verification for a Flex Rider ID.

    This is the function called by zk_router.py.  It:
        1. Validates public signals (cheap, catches malformed requests early)
        2. Loads the verification key
        3. Runs the Groth16 pairing check (expensive, ~1–2 s in pure Python)
        4. Returns a result dict consumed by the router

    Args:
        proof:           snarkjs Groth16 proof dict (pi_a, pi_b, pi_c, protocol, curve)
        public_signals:  List of 3 decimal strings [riderIDHash, nullifier, minEntropy]

    Returns:
        {
            "valid": bool,
            "rider_id_hash": str,   # hex of public_signals[0]
            "nullifier": str,       # hex of public_signals[1]
            "error": str | None,    # None if valid
        }
    """
    result: dict[str, Any] = {
        "valid": False,
        "rider_id_hash": None,
        "nullifier": None,
        "error": None,
    }

    # ---- Validate signals first (fast) ----
    try:
        min_entropy = int(os.getenv("FEATURE04_ZK_MIN_ENTROPY", "65536"))
        validate_public_signals(public_signals, min_entropy=min_entropy)
    except ValueError as exc:
        result["error"] = f"Invalid public signals: {exc}"
        logger.warning("ZK signal validation failed: %s", exc)
        return result

    # ---- Load verification key ----
    try:
        vkey_path = get_vkey_path()
        vkey = load_verification_key(vkey_path)
    except FileNotFoundError as exc:
        result["error"] = (
            "Verification key not available. "
            "The ZK ceremony may not have been completed yet. "
            f"Detail: {exc}"
        )
        logger.error("Verification key load failed: %s", exc)
        return result
    except ValueError as exc:
        result["error"] = f"Verification key malformed: {exc}"
        logger.error("Verification key parse error: %s", exc)
        return result

    # ---- Run pairing check ----
    try:
        is_valid = verify_groth16_proof(vkey, proof, public_signals)
    except (ImportError, ValueError) as exc:
        result["error"] = f"Proof verification error: {exc}"
        logger.error("Groth16 verification error: %s", exc)
        return result
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"Unexpected verification failure: {exc}"
        logger.exception("Unexpected error during Groth16 verification")
        return result

    if not is_valid:
        result["error"] = "Proof verification failed: invalid proof."
        return result

    # ---- Extract public values for storage ----
    rider_id_hash_int = int(public_signals[0])
    nullifier_int     = int(public_signals[1])

    result["valid"]          = True
    result["rider_id_hash"]  = hex(rider_id_hash_int)
    result["nullifier"]      = hex(nullifier_int)
    result["error"]          = None

    logger.info(
        "ZK proof verified OK | rider_id_hash=%s... | nullifier=%s...",
        result["rider_id_hash"][:14],
        result["nullifier"][:14],
    )
    return result

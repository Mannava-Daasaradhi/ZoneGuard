"""
FraudShield v2 — Federated Client.

Each city (Bengaluru, Mumbai, Hyderabad, …) runs one FederatedFraudClient
on its own server. The client:
  1. Trains a local IsolationForest on its city's claim data.
  2. Serialises the model into a flat weight vector (contamination float +
     the decision_function offset array from the fitted estimators).
  3. Sends ONLY those weights to the central FederatedFraudServer.
  4. Receives the globally aggregated weights back and updates its local model.

Raw rider GPS, timestamps, and activity data NEVER leave the city.
DPDP Act 2023 compliant by design.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Feature order must be consistent across all clients
FEATURE_NAMES = [
    "claim_hour",
    "tenure_weeks",
    "zone_inactivity_pct",
    "claim_velocity_7d",
    "zone_claim_rate_deviation",
    "distance_from_centroid_km",
    "s1_value",
    "days_since_policy_start",
]

# IsolationForest hyperparameters — fixed across all clients for aggregation
N_ESTIMATORS = 50        # kept small for fast demo inference
MAX_SAMPLES = "auto"
CONTAMINATION = 0.08     # ~8% expected fraud rate across gig worker base
RANDOM_STATE = 42


def generate_synthetic_city_data(
    city_name: str,
    n_samples: int = 300,
    fraud_fraction: float = 0.08,
    seed: int = 0,
) -> np.ndarray:
    """
    Generate synthetic claim feature data for a simulated city.
    In production this would be the city's real historical claim records.

    Genuine claims cluster around typical working-hour, mid-tenure,
    high-zone-inactivity patterns.  Fraudulent claims skew toward
    new-policy, low-inactivity, off-hours patterns.

    Returns an (n_samples, 8) float array — one row per historical claim.
    """
    rng = np.random.default_rng(seed)

    n_fraud = int(n_samples * fraud_fraction)
    n_genuine = n_samples - n_fraud

    # Genuine claim distribution
    genuine = np.column_stack([
        rng.integers(6, 22, n_genuine),            # claim_hour: working hours
        rng.integers(4, 104, n_genuine),            # tenure_weeks: established riders
        rng.uniform(40, 90, n_genuine),             # zone_inactivity_pct: high during real events
        rng.integers(0, 2, n_genuine),              # claim_velocity_7d: low
        rng.uniform(0.5, 1.5, n_genuine),           # zone_claim_rate_deviation: near normal
        rng.uniform(0.5, 3.0, n_genuine),           # distance_from_centroid_km: in-zone
        rng.uniform(55, 120, n_genuine),            # s1_value: high during real events
        rng.integers(3, 90, n_genuine),             # days_since_policy_start: established
    ]).astype(float)

    # Fraudulent claim distribution (anomalous patterns)
    fraud = np.column_stack([
        rng.choice([*range(0, 5), *range(23, 24)], n_fraud),  # off-hours
        rng.integers(0, 3, n_fraud),               # tenure_weeks: brand new
        rng.uniform(5, 25, n_fraud),               # zone_inactivity_pct: low (others working)
        rng.integers(3, 8, n_fraud),               # claim_velocity_7d: high velocity
        rng.uniform(2.0, 5.0, n_fraud),            # zone_claim_rate_deviation: spiky
        rng.uniform(5.0, 15.0, n_fraud),           # distance_from_centroid_km: far out of zone
        rng.uniform(5, 30, n_fraud),               # s1_value: low (no real event)
        rng.integers(0, 2, n_fraud),               # days_since_policy_start: brand new policy
    ]).astype(float)

    data = np.vstack([genuine, fraud])

    # Add city-specific noise to simulate different data distributions
    city_seed = sum(ord(c) for c in city_name)
    noise_rng = np.random.default_rng(city_seed)
    data += noise_rng.normal(0, 0.5, data.shape)
    data = np.clip(data, 0, None)   # no negatives

    return data


class FederatedFraudClient:
    """
    One per city.  Owns a local IsolationForest trained on that city's data.
    Communicates only weight vectors to the server.
    """

    def __init__(self, city_id: str, local_data: Optional[np.ndarray] = None):
        self.city_id = city_id
        self._n_training_samples = 0
        self.model = IsolationForest(
            n_estimators=N_ESTIMATORS,
            max_samples=MAX_SAMPLES,
            contamination=CONTAMINATION,
            random_state=RANDOM_STATE,
        )
        self._trained = False

        if local_data is not None:
            self.fit(local_data)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(self, X: np.ndarray) -> None:
        """Train the local model on this city's data."""
        if X.shape[0] < 10:
            logger.warning(f"[{self.city_id}] Too few samples ({X.shape[0]}) to train. Skipping.")
            return
        self.model.fit(X)
        self._trained = True
        self._n_training_samples = int(X.shape[0]) 
        logger.info(f"[{self.city_id}] Local model trained on {X.shape[0]} samples.")

    # ------------------------------------------------------------------
    # Weight serialisation  (IsolationForest → flat numpy array)
    # ------------------------------------------------------------------

    def get_weights(self) -> Tuple[np.ndarray, int]:
        """
        Serialise the local model into a flat weight vector.

        We extract the `offset_` array from each fitted base estimator
        (ExtraTreeRegressor) — these are the anomaly score offsets that
        encode the learned decision boundary.

        Returns (weight_vector, n_training_samples).
        """
        if not self._trained:
            raise RuntimeError(f"[{self.city_id}] Model not trained yet.")

        offsets = np.array([
            est.tree_.threshold.mean()
            for est in self.model.estimators_
        ])
        # Append global offset_ as the final element
        weights = np.append(offsets, self.model.offset_)
        return weights, self._n_training_samples

    def set_weights(self, weights: np.ndarray) -> None:
        """
        Apply aggregated weights from the server.
        Updates the estimator offsets and global offset_.
        """
        if not self._trained:
            logger.warning(f"[{self.city_id}] Applying weights to untrained model — fitting on dummy data first.")
            dummy = generate_synthetic_city_data(self.city_id, n_samples=50)
            self.fit(dummy)

        estimator_offsets = weights[:-1]
        global_offset = weights[-1]

        for i, est in enumerate(self.model.estimators_):
            if i < len(estimator_offsets):
                # Shift all leaf thresholds by the delta from global average
                delta = estimator_offsets[i] - est.tree_.threshold.mean()
                est.tree_.threshold[:] = np.clip(
                    est.tree_.threshold + delta, -np.inf, np.inf
                )

        self.model.offset_ = float(global_offset)
        logger.info(f"[{self.city_id}] Weights updated from global model.")

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_fraud_score(self, features: List[float]) -> dict:
        """
        Score a single claim using the locally-held (globally-informed) model.

        Returns a dict compatible with fraud_shield.calculate_fraud_score output.
        """
        if not self._trained:
            raise RuntimeError(f"[{self.city_id}] Model not trained.")

        X = np.array(features, dtype=float).reshape(1, -1)
        raw_score = self.model.score_samples(X)[0]

        # IsolationForest: more negative = more anomalous
        # Normalise to [0, 1] where 1 = most anomalous
        normalised = float(np.clip((raw_score - (-0.8)) / (0.2 - (-0.8)), 0, 1))
        fraud_score = round(1.0 - normalised, 3)   # invert: high = anomalous

        if fraud_score > 0.85:
            risk_level = "hold"
        elif fraud_score > 0.65:
            risk_level = "review"
        else:
            risk_level = "low"

        return {
            "score": fraud_score,
            "risk_level": risk_level,
            "model": "federated_isolation_forest",
            "city_id": self.city_id,
            "features": dict(zip(FEATURE_NAMES, features)),
        }

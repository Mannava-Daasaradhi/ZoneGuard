"""
FraudShield v2 — Federated Learning Architecture.

Implements FedAvg (McMahan et al., 2017) manually using scikit-learn
IsolationForest, without requiring a Flower network server.

In production, each "client" would be a city-level deployment running
on its own infrastructure. Model GRADIENTS (weight arrays) are shared
with the central server — raw rider GPS and activity data NEVER leaves
the city cluster. This satisfies India's DPDP Act 2023 data minimisation.

For the hackathon demo, all clients run in the same process to simulate
the federated round — the aggregation logic is identical to production.
"""

from .client import FederatedFraudClient, generate_synthetic_city_data
from .server import FederatedFraudServer, run_federated_round

__all__ = [
    "FederatedFraudClient",
    "FederatedFraudServer",
    "generate_synthetic_city_data",
    "run_federated_round",
]

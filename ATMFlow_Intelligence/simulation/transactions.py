"""
Transaction definitions and stochastic service-time models.
SPMS Course: Solving Problems Using Modelling and Simulation (NEC00091)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
import numpy as np


class TransactionType(str, Enum):
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    BALANCE_ENQUIRY = "BALANCE_ENQUIRY"


@dataclass
class TransactionProfile:
    """
    Stochastic distribution parameters for a transaction category.
    Service times are modelled with either:
      - 'lognormal' (realistic human interaction: right-skewed, positive support)
      - 'exponential' (memoryless theoretical benchmark)
      - 'normal' (truncated positive normal)
    """
    tx_type: TransactionType
    distribution: str  # 'lognormal', 'exponential', 'normal'
    mean_seconds: float
    std_seconds: float
    min_seconds: float = 15.0
    probability: float = 0.3333

    def sample_service_time(self, rng: np.random.Generator) -> float:
        """Draw a realistic non-negative service duration from distribution."""
        if self.distribution == "exponential":
            val = rng.exponential(scale=self.mean_seconds)
        elif self.distribution == "lognormal":
            # Convert normal mean and variance to log-normal mu and sigma
            m = self.mean_seconds
            v = self.std_seconds ** 2
            mu = np.log(m**2 / np.sqrt(v + m**2))
            sigma = np.sqrt(np.log(1.0 + (v / (m**2))))
            val = rng.lognormal(mean=mu, sigma=sigma)
        elif self.distribution == "normal":
            val = rng.normal(loc=self.mean_seconds, scale=self.std_seconds)
        else:
            val = rng.exponential(scale=self.mean_seconds)

        return float(max(self.min_seconds, val))


class TransactionManager:
    """Manages transaction mix and service time sampling."""

    DEFAULT_PROFILES: Dict[TransactionType, TransactionProfile] = {
        TransactionType.CASH_WITHDRAWAL: TransactionProfile(
            tx_type=TransactionType.CASH_WITHDRAWAL,
            distribution="lognormal",
            mean_seconds=110.0,
            std_seconds=35.0,
            min_seconds=30.0,
            probability=0.60
        ),
        TransactionType.CASH_DEPOSIT: TransactionProfile(
            tx_type=TransactionType.CASH_DEPOSIT,
            distribution="lognormal",
            mean_seconds=170.0,
            std_seconds=50.0,
            min_seconds=45.0,
            probability=0.25
        ),
        TransactionType.BALANCE_ENQUIRY: TransactionProfile(
            tx_type=TransactionType.BALANCE_ENQUIRY,
            distribution="lognormal",
            mean_seconds=45.0,
            std_seconds=15.0,
            min_seconds=15.0,
            probability=0.15
        ),
    }

    def __init__(self, profiles: Optional[Dict[TransactionType, TransactionProfile]] = None):
        self.profiles = profiles or self.DEFAULT_PROFILES
        # Normalize probabilities
        total_p = sum(p.probability for p in self.profiles.values())
        self.types = list(self.profiles.keys())
        self.probabilities = [self.profiles[t].probability / total_p for t in self.types]

    def sample_transaction_type(self, rng: np.random.Generator) -> TransactionType:
        """Choose transaction category according to categorical probability distribution."""
        choice = rng.choice(len(self.types), p=self.probabilities)
        return self.types[choice]

    def sample_service_time(self, tx_type: TransactionType, rng: np.random.Generator) -> float:
        """Sample duration in seconds for given transaction type."""
        profile = self.profiles[tx_type]
        return profile.sample_service_time(rng)

    def get_weighted_average_service_time(self) -> float:
        """Calculate analytical mean service time E[S] across all transaction types."""
        return sum(self.profiles[t].mean_seconds * p for t, p in zip(self.types, self.probabilities))

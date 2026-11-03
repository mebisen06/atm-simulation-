"""
Stochastic Customer Arrival Processes.
Includes Homogeneous Poisson, Non-Homogeneous Poisson (NHPP with Peak Hours), and Surges.
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class ArrivalProcess(ABC):
    """Abstract base for stochastic arrival processes."""

    @abstractmethod
    def next_interarrival_time(self, current_time: float, rng: np.random.Generator) -> float:
        """Calculate time until the subsequent customer arrives."""
        pass


class HomogeneousPoissonArrival(ArrivalProcess):
    """
    Stationary Poisson process with constant arrival intensity lambda.
    Inter-arrival times are independent and identically distributed (i.i.d.) Exponential(lambda).
    """

    def __init__(self, arrival_rate_per_minute: float):
        """
        :param arrival_rate_per_minute: Lambda (customers per minute).
        """
        if arrival_rate_per_minute <= 0:
            raise ValueError("Arrival rate must be strictly positive.")
        self.rate_per_minute = arrival_rate_per_minute
        self.rate_per_second = arrival_rate_per_minute / 60.0

    def next_interarrival_time(self, current_time: float, rng: np.random.Generator) -> float:
        # Scale for exponential distribution in seconds = 1 / lambda
        mean_interarrival_seconds = 1.0 / self.rate_per_second
        return float(rng.exponential(scale=mean_interarrival_seconds))


class PeakHourPoissonArrival(ArrivalProcess):
    """
    Non-Homogeneous Poisson Process (NHPP).
    Arrival intensity lambda(t) varies sinusoidally or in piecewise steps during peak banking hours.
    Uses Lewis-Shedler thinning algorithm.
    """

    def __init__(
        self,
        base_rate_per_minute: float,
        peak_multiplier: float = 2.5,
        peak_start_minute: float = 60.0,
        peak_end_minute: float = 120.0
    ):
        self.base_rate = base_rate_per_minute / 60.0
        self.peak_rate = (base_rate_per_minute * peak_multiplier) / 60.0
        self.peak_start_sec = peak_start_minute * 60.0
        self.peak_end_sec = peak_end_minute * 60.0
        self.max_rate = self.peak_rate

    def rate_at(self, t: float) -> float:
        """Intensity function lambda(t)."""
        if self.peak_start_sec <= t <= self.peak_end_sec:
            # Smooth bell curve transition inside peak window
            mid = (self.peak_start_sec + self.peak_end_sec) / 2.0
            half_width = (self.peak_end_sec - self.peak_start_sec) / 2.0
            rel = (t - mid) / half_width
            intensity_factor = np.exp(-0.5 * (rel * 2.5) ** 2)
            return self.base_rate + (self.peak_rate - self.base_rate) * intensity_factor
        return self.base_rate

    def next_interarrival_time(self, current_time: float, rng: np.random.Generator) -> float:
        """Thinning algorithm for NHPP."""
        t = current_time
        while True:
            # Generate potential arrival using max bound lambda_max
            w = rng.exponential(scale=1.0 / self.max_rate)
            t += w
            u = rng.uniform(0.0, 1.0)
            if u <= self.rate_at(t) / self.max_rate:
                return float(t - current_time)


class SurgeArrivalProcess(ArrivalProcess):
    """
    Combines normal traffic with an abrupt customer surge window.
    Simulates flash events (e.g. salary deposit day or lunch-break crowd).
    """

    def __init__(
        self,
        base_rate_per_minute: float,
        surge_rate_per_minute: float,
        surge_start_sec: float,
        surge_duration_sec: float
    ):
        self.base_rate_per_sec = base_rate_per_minute / 60.0
        self.surge_rate_per_sec = surge_rate_per_minute / 60.0
        self.surge_start_sec = surge_start_sec
        self.surge_end_sec = surge_start_sec + surge_duration_sec

    def next_interarrival_time(self, current_time: float, rng: np.random.Generator) -> float:
        rate = (
            self.surge_rate_per_sec
            if self.surge_start_sec <= current_time <= self.surge_end_sec
            else self.base_rate_per_sec
        )
        return float(rng.exponential(scale=1.0 / rate))

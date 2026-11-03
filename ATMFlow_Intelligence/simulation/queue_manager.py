"""
Queue Management Policies and Time-Weighted Queue Analytics.
Supports Pooled FIFO (M/M/c single-line architecture) and Shortest Queue (multi-line architecture).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import simpy
from .customer import Customer
from .atm import ATM, ATMStatus


class QueueManager(ABC):
    """Abstract base for ATM queue scheduling policies."""

    def __init__(self, env: simpy.Environment, atms: List[ATM]):
        self.env = env
        self.atms = atms
        self.queue_history: List[Tuple[float, int]] = [(0.0, 0)]
        self._last_event_time: float = 0.0
        self._current_queue_len: int = 0
        self._area_under_queue_curve: float = 0.0

    @abstractmethod
    def assign_customer(self, customer: Customer) -> simpy.events.Event:
        """Assign customer to an ATM according to the queue policy."""
        pass

    def record_queue_length_change(self, delta: int):
        """Update instantaneous queue length and calculate integral for time-weighted average."""
        now = self.env.now
        time_delta = now - self._last_event_time
        if time_delta > 0:
            self._area_under_queue_curve += self._current_queue_len * time_delta

        self._current_queue_len = max(0, self._current_queue_len + delta)
        self._last_event_time = now
        self.queue_history.append((round(now, 2), self._current_queue_len))

    def get_time_weighted_average_queue_length(self, total_simulation_time: float) -> float:
        """
        Calculates time-weighted average queue length:
        L_q = (1 / T) * integral_0^T L_q(t) dt
        """
        if total_simulation_time <= 0:
            return 0.0
        final_area = self._area_under_queue_curve
        remaining_time = total_simulation_time - self._last_event_time
        if remaining_time > 0:
            final_area += self._current_queue_len * remaining_time
        return final_area / total_simulation_time

    @property
    def current_length(self) -> int:
        return self._current_queue_len


class PooledFIFOQueueManager(QueueManager):
    """
    Unified Single Queue (Pooled FIFO / Multi-Server M/M/c architecture).
    Customers wait in a single serpentine queue and are dispatched to the next idle ATM.
    Uses a shared SimPy Resource with capacity = number of operational ATMs, or round-robin requests.
    """

    def __init__(self, env: simpy.Environment, atms: List[ATM]):
        super().__init__(env, atms)
        # Store customers waiting in the pooled queue
        self.waiting_customers: List[Customer] = []

    def select_available_atm(self) -> Optional[ATM]:
        """Find an idle and operational ATM."""
        for atm in self.atms:
            if atm.status == ATMStatus.IDLE and len(atm.resource.users) == 0:
                return atm
        return None

    def assign_customer(self, customer: Customer):
        """Assign customer according to policy."""
        pass


class PooledFIFOQueueManager(QueueManager):
    """
    Unified Single Queue (Pooled FIFO / Multi-Server M/M/c architecture).
    Customers wait in a single serpentine queue and are dispatched to the next idle ATM.
    """

    def __init__(self, env: simpy.Environment, atms: List[ATM]):
        super().__init__(env, atms)
        self.waiting_customers: List[Customer] = []

    def assign_customer(self, customer: Customer):
        """Enqueue customer in pooled line."""
        self.waiting_customers.append(customer)

    def select_available_atm(self) -> Optional[ATM]:
        """Find an idle and operational ATM."""
        for atm in self.atms:
            if atm.status == ATMStatus.IDLE and len(atm.resource.users) == 0:
                return atm
        return None


class ShortestQueueManager(QueueManager):
    """
    Dedicated Multi-Queue Architecture.
    Each ATM has its own dedicated physical line.
    Arriving customers inspect all available lines and join the ATM with the minimum queue count.
    """

    def __init__(self, env: simpy.Environment, atms: List[ATM]):
        super().__init__(env, atms)
        self.atm_queues: Dict[str, List[Customer]] = {atm.atm_id: [] for atm in atms}

    def assign_customer(self, customer: Customer):
        """Assigns customer to shortest ATM queue."""
        chosen_atm = self.select_shortest_atm()
        customer.assigned_atm_id = chosen_atm.atm_id
        self.atm_queues[chosen_atm.atm_id].append(customer)
        return chosen_atm

    def select_shortest_atm(self) -> ATM:
        """Select operational ATM with fewest customers waiting in line."""
        available = [atm for atm in self.atms if atm.status not in (ATMStatus.FAILED, ATMStatus.OFFLINE)]
        if not available:
            return self.atms[0]
        return min(available, key=lambda atm: len(self.atm_queues[atm.atm_id]) + len(atm.resource.users))

"""
Customer entity for Discrete Event Simulation.
Tracking individual customer lifecycle from arrival to departure.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from .transactions import TransactionType


class CustomerStatus(str, Enum):
    ARRIVED = "ARRIVED"
    QUEUED = "QUEUED"
    IN_SERVICE = "IN_SERVICE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    FAILED_OUT_OF_CASH = "FAILED_OUT_OF_CASH"
    FAILED_ATM_BREAKDOWN = "FAILED_ATM_BREAKDOWN"


@dataclass
class Customer:
    """
    Represents an individual customer in the ATM simulation.
    Captures end-to-end discrete-event timeline timestamps.
    """
    customer_id: int
    arrival_time: float
    transaction_type: TransactionType
    requested_amount: float = 0.0  # For cash withdrawal / deposit
    patience_limit: Optional[float] = None  # Reneging threshold in seconds

    # Lifecycle state
    status: CustomerStatus = CustomerStatus.ARRIVED
    assigned_atm_id: Optional[str] = None
    queue_entry_time: float = 0.0
    service_start_time: Optional[float] = None
    service_duration: float = 0.0
    completion_time: Optional[float] = None
    reneg_time: Optional[float] = None

    @property
    def waiting_time(self) -> float:
        """Time spent waiting in queue prior to receiving service or reneging."""
        if self.service_start_time is not None:
            return max(0.0, self.service_start_time - self.queue_entry_time)
        elif self.reneg_time is not None:
            return max(0.0, self.reneg_time - self.queue_entry_time)
        return 0.0

    @property
    def system_time(self) -> float:
        """Total time spent in system (waiting time + service time)."""
        if self.completion_time is not None:
            return max(0.0, self.completion_time - self.arrival_time)
        elif self.reneg_time is not None:
            return max(0.0, self.reneg_time - self.arrival_time)
        return 0.0

    @property
    def is_completed(self) -> bool:
        return self.status == CustomerStatus.COMPLETED

    @property
    def is_abandoned(self) -> bool:
        return self.status == CustomerStatus.ABANDONED

    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "arrival_time": round(self.arrival_time, 2),
            "transaction_type": self.transaction_type.value,
            "assigned_atm_id": self.assigned_atm_id,
            "waiting_time": round(self.waiting_time, 2),
            "service_duration": round(self.service_duration, 2),
            "system_time": round(self.system_time, 2),
            "status": self.status.value,
            "requested_amount": self.requested_amount,
            "abandoned": self.is_abandoned,
        }

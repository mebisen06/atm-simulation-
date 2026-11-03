"""
ATM Unit Resource and State Management.
Handles physical ATM resources, operational state transitions, and utilization logging.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple
import simpy
from .customer import Customer


class ATMStatus(str, Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    FAILED = "FAILED"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_CASH = "OUT_OF_CASH"
    OFFLINE = "OFFLINE"


class ATM:
    """
    Simulated ATM unit wrapping a SimPy single-capacity Resource.
    Logs instantaneous state changes for timeline and utilization analytics.
    """

    def __init__(
        self,
        env: simpy.Environment,
        atm_id: str,
        initial_cash: float = 500000.0,
        speed_multiplier: float = 1.0,
    ):
        self.env = env
        self.atm_id = atm_id
        self.initial_cash = initial_cash
        self.cash_balance = initial_cash
        self.speed_multiplier = max(0.2, speed_multiplier)  # Service acceleration / slowdown

        # SimPy Resource representing server capacity (1 customer at a time)
        self.resource = simpy.Resource(env, capacity=1)

        # Operational status
        self._status = ATMStatus.IDLE
        self.current_customer: Optional[Customer] = None

        # Cumulative statistics
        self.total_customers_served = 0
        self.total_busy_time = 0.0
        self.last_status_change_time = 0.0

        # State history for visualization: list of (timestamp, status)
        self.state_history: List[Tuple[float, str]] = [(0.0, ATMStatus.IDLE.value)]
        # Cash history: list of (timestamp, balance)
        self.cash_history: List[Tuple[float, float]] = [(0.0, initial_cash)]

    @property
    def status(self) -> ATMStatus:
        return self._status

    def set_status(self, new_status: ATMStatus):
        """Transition ATM operational state and update cumulative busy/idle time."""
        if new_status == self._status:
            return

        now = self.env.now
        time_in_prev_state = now - self.last_status_change_time

        if self._status == ATMStatus.BUSY:
            self.total_busy_time += time_in_prev_state

        self._status = new_status
        self.last_status_change_time = now
        self.state_history.append((round(now, 2), new_status.value))

    def start_service(self, customer: Customer):
        """Mark ATM as busy serving a customer."""
        self.current_customer = customer
        self.set_status(ATMStatus.BUSY)

    def finish_service(self):
        """Release customer and return to idle (or out of cash / maintenance)."""
        self.total_customers_served += 1
        self.current_customer = None
        if self.cash_balance <= 0:
            self.set_status(ATMStatus.OUT_OF_CASH)
        else:
            self.set_status(ATMStatus.IDLE)

    def deduct_cash(self, amount: float) -> bool:
        """Deduct dispensed cash if sufficient inventory exists."""
        if amount <= 0:
            return True
        if self.cash_balance >= amount:
            self.cash_balance -= amount
            self.cash_history.append((round(self.env.now, 2), self.cash_balance))
            return True
        else:
            self.set_status(ATMStatus.OUT_OF_CASH)
            return False

    def replenish_cash(self, amount: float):
        """Replenish ATM vault with fresh cash."""
        self.cash_balance += amount
        self.cash_history.append((round(self.env.now, 2), self.cash_balance))
        if self._status == ATMStatus.OUT_OF_CASH:
            self.set_status(ATMStatus.IDLE)

    def get_utilization(self, total_simulation_time: float) -> float:
        """Calculate server utilization rho = busy_time / total_time."""
        if total_simulation_time <= 0:
            return 0.0
        # Account for time in busy state up to the end of simulation
        busy = self.total_busy_time
        if self._status == ATMStatus.BUSY:
            busy += (self.env.now - self.last_status_change_time)
        return min(1.0, max(0.0, busy / total_simulation_time))

    def to_dict(self, total_sim_time: float) -> dict:
        return {
            "atm_id": self.atm_id,
            "status": self.status.value,
            "cash_balance": self.cash_balance,
            "total_customers_served": self.total_customers_served,
            "total_busy_time": round(self.total_busy_time, 2),
            "utilization": round(self.get_utilization(total_sim_time), 4),
            "current_customer_id": self.current_customer.customer_id if self.current_customer else None,
        }

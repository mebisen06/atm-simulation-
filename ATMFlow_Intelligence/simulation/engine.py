"""
ATMFlow Intelligence - Discrete Event Simulation Engine
Core SimPy Orchestrator for ATM Network Queue Simulation.
SPMS Course: Solving Problems Using Modelling and Simulation (NEC00091)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
import simpy

from .customer import Customer, CustomerStatus
from .transactions import TransactionType, TransactionManager
from .arrivals import ArrivalProcess, HomogeneousPoissonArrival, PeakHourPoissonArrival, SurgeArrivalProcess
from .atm import ATM, ATMStatus
from .queue_manager import PooledFIFOQueueManager, ShortestQueueManager


@dataclass
class SimulationConfig:
    """Simulation run parameters."""
    random_seed: int = 42
    sim_duration_seconds: float = 3600.0  # 1 hour standard run
    num_atms: int = 3
    arrival_rate_per_min: float = 1.0     # 60 customers / hr
    arrival_process_type: str = "homogeneous"  # 'homogeneous', 'peak_hour', 'surge'
    queue_policy_type: str = "pooled_fifo"     # 'pooled_fifo', 'shortest_queue'
    customer_patience_mean: Optional[float] = None  # Reneging threshold in seconds, None = infinite
    initial_cash_per_atm: float = 500000.0
    atm_speeds: Optional[List[float]] = None
    transaction_manager: Optional[TransactionManager] = None


@dataclass
class SimulationResult:
    """Structured statistical results and time-series outputs from a completed simulation run."""
    config: SimulationConfig
    total_customers_arrived: int
    completed_customers: int
    abandoned_customers: int
    failed_customers: int
    waiting_at_end: int
    in_service_at_end: int
    average_waiting_time_sec: float
    max_waiting_time_sec: float
    p95_waiting_time_sec: float
    average_service_time_sec: float
    average_system_time_sec: float
    time_weighted_queue_length: float
    average_atm_utilization: float
    throughput_per_hour: float
    atm_metrics: List[Dict[str, Any]]
    littles_law_verification: Dict[str, float]
    queue_history: List[List[float]]       # [[time, len], ...]
    customer_records: List[Dict[str, Any]]
    events_log: List[Dict[str, Any]]

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "total_arrived": self.total_customers_arrived,
            "completed": self.completed_customers,
            "abandoned": self.abandoned_customers,
            "failed": self.failed_customers,
            "waiting_at_end": self.waiting_at_end,
            "in_service_at_end": self.in_service_at_end,
            "completion_rate_pct": round(
                (self.completed_customers / self.total_customers_arrived * 100.0)
                if self.total_customers_arrived > 0 else 0.0, 2
            ),
            "avg_waiting_time_sec": round(self.average_waiting_time_sec, 2),
            "max_waiting_time_sec": round(self.max_waiting_time_sec, 2),
            "p95_waiting_time_sec": round(self.p95_waiting_time_sec, 2),
            "avg_service_time_sec": round(self.average_service_time_sec, 2),
            "avg_system_time_sec": round(self.average_system_time_sec, 2),
            "time_weighted_queue_length": round(self.time_weighted_queue_length, 3),
            "average_atm_utilization": round(self.average_atm_utilization, 4),
            "throughput_per_hour": round(self.throughput_per_hour, 2),
            "littles_law": self.littles_law_verification,
        }


class SimulationEngine:
    """
    SimPy-based Discrete Event Simulation Engine.
    Simulates complete customer journey:
    Arrival -> Queue Formation -> ATM Allocation -> Transaction -> Departure / Reneging.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.rng = np.random.default_rng(config.random_seed)
        self.env = simpy.Environment()

        # Initialize Transaction Manager
        self.tx_manager = config.transaction_manager or TransactionManager()

        # Initialize ATMs
        speeds = config.atm_speeds or [1.0] * config.num_atms
        self.atms: List[ATM] = [
            ATM(
                env=self.env,
                atm_id=f"ATM-{i+1:02d}",
                initial_cash=config.initial_cash_per_atm,
                speed_multiplier=speeds[i] if i < len(speeds) else 1.0,
            )
            for i in range(config.num_atms)
        ]

        # Initialize Queue Manager
        if config.queue_policy_type == "shortest_queue":
            self.queue_manager = ShortestQueueManager(self.env, self.atms)
        else:
            self.queue_manager = PooledFIFOQueueManager(self.env, self.atms)

        # Multi-server pooled resource for Pooled FIFO
        self.pooled_resource = simpy.Resource(self.env, capacity=self.config.num_atms)

        # Initialize Arrival Process
        if config.arrival_process_type == "peak_hour":
            self.arrival_process: ArrivalProcess = PeakHourPoissonArrival(
                base_rate_per_minute=config.arrival_rate_per_min,
                peak_multiplier=2.5,
                peak_start_minute=config.sim_duration_seconds / 120.0,
                peak_end_minute=config.sim_duration_seconds / 60.0 * 0.8
            )
        elif config.arrival_process_type == "surge":
            self.arrival_process = SurgeArrivalProcess(
                base_rate_per_minute=config.arrival_rate_per_min,
                surge_rate_per_minute=config.arrival_rate_per_min * 3.5,
                surge_start_sec=config.sim_duration_seconds * 0.35,
                surge_duration_sec=min(600.0, config.sim_duration_seconds * 0.25)
            )
        else:
            self.arrival_process = HomogeneousPoissonArrival(
                arrival_rate_per_minute=config.arrival_rate_per_min
            )

        # State tracking collections
        self.customers: List[Customer] = []
        self.events_log: List[Dict[str, Any]] = []

    def _log_event(self, event_type: str, customer_id: int, atm_id: Optional[str] = None, details: str = ""):
        self.events_log.append({
            "timestamp": round(self.env.now, 2),
            "customer_id": customer_id,
            "event": event_type,
            "atm_id": atm_id,
            "queue_len": self.queue_manager.current_length,
            "details": details,
        })

    def customer_process_pooled(self, customer: Customer):
        """Lifecycle of a customer under a Pooled FIFO Queue."""
        # 1. Enqueue
        customer.status = CustomerStatus.QUEUED
        customer.queue_entry_time = self.env.now
        self.queue_manager.record_queue_length_change(+1)
        self._log_event("JOINED_QUEUE", customer.customer_id, details=f"Tx: {customer.transaction_type.value}")

        # Determine patience limit if configured
        patience = customer.patience_limit

        req = self.pooled_resource.request()

        if patience is not None:
            # Customer reneges if wait time exceeds patience limit
            results = yield req | self.env.timeout(patience)
            if req not in results:
                # Customer reneged
                self.queue_manager.record_queue_length_change(-1)
                customer.status = CustomerStatus.ABANDONED
                customer.reneg_time = self.env.now
                self._log_event("RENEGED", customer.customer_id, details=f"Waited {round(customer.waiting_time, 1)}s")
                req.cancel()
                return
        else:
            yield req

        # 2. Dequeue and claim an idle ATM
        self.queue_manager.record_queue_length_change(-1)
        customer.service_start_time = self.env.now
        customer.status = CustomerStatus.IN_SERVICE

        # Find which physical ATM is idle
        assigned_atm: Optional[ATM] = None
        for atm in self.atms:
            if atm.status == ATMStatus.IDLE:
                assigned_atm = atm
                break
        if assigned_atm is None:
            # Fallback to least busy ATM
            assigned_atm = min(self.atms, key=lambda a: a.total_busy_time)

        customer.assigned_atm_id = assigned_atm.atm_id
        assigned_atm.start_service(customer)

        self._log_event("SERVICE_STARTED", customer.customer_id, assigned_atm.atm_id,
                        f"Wait time: {round(customer.waiting_time, 1)}s")

        # 3. Process Transaction
        raw_service_time = self.tx_manager.sample_service_time(customer.transaction_type, self.rng)
        adjusted_service_time = raw_service_time / assigned_atm.speed_multiplier
        customer.service_duration = adjusted_service_time

        # Check cash availability if withdrawal
        if customer.transaction_type == TransactionType.CASH_WITHDRAWAL:
            if not assigned_atm.deduct_cash(customer.requested_amount):
                # Out of cash failure
                customer.status = CustomerStatus.FAILED_OUT_OF_CASH
                customer.completion_time = self.env.now
                assigned_atm.finish_service()
                self.pooled_resource.release(req)
                self._log_event("FAILED_OUT_OF_CASH", customer.customer_id, assigned_atm.atm_id)
                return

        # Simulate service execution
        yield self.env.timeout(adjusted_service_time)

        # 4. Completion & Departure
        customer.completion_time = self.env.now
        customer.status = CustomerStatus.COMPLETED
        assigned_atm.finish_service()
        self.pooled_resource.release(req)

        self._log_event("SERVICE_COMPLETED", customer.customer_id, assigned_atm.atm_id,
                        f"Duration: {round(adjusted_service_time, 1)}s")

    def customer_process_dedicated(self, customer: Customer):
        """Lifecycle of a customer choosing the shortest dedicated ATM line."""
        # Inspect and select shortest queue
        shortest_atm = self.queue_manager.select_shortest_atm()
        customer.assigned_atm_id = shortest_atm.atm_id

        # 1. Enqueue
        customer.status = CustomerStatus.QUEUED
        customer.queue_entry_time = self.env.now
        self.queue_manager.atm_queues[shortest_atm.atm_id].append(customer)
        self.queue_manager.record_queue_length_change(+1)
        self._log_event("JOINED_ATM_QUEUE", customer.customer_id, shortest_atm.atm_id)

        patience = customer.patience_limit
        req = shortest_atm.resource.request()

        if patience is not None:
            results = yield req | self.env.timeout(patience)
            if req not in results:
                # Reneging
                self.queue_manager.record_queue_length_change(-1)
                self.queue_manager.atm_queues[shortest_atm.atm_id].remove(customer)
                customer.status = CustomerStatus.ABANDONED
                customer.reneg_time = self.env.now
                self._log_event("RENEGED", customer.customer_id, shortest_atm.atm_id)
                req.cancel()
                return
        else:
            yield req

        # 2. Start Service
        self.queue_manager.record_queue_length_change(-1)
        if customer in self.queue_manager.atm_queues[shortest_atm.atm_id]:
            self.queue_manager.atm_queues[shortest_atm.atm_id].remove(customer)

        customer.service_start_time = self.env.now
        customer.status = CustomerStatus.IN_SERVICE
        shortest_atm.start_service(customer)

        self._log_event("SERVICE_STARTED", customer.customer_id, shortest_atm.atm_id,
                        f"Wait time: {round(customer.waiting_time, 1)}s")

        # 3. Transaction Execution
        raw_service_time = self.tx_manager.sample_service_time(customer.transaction_type, self.rng)
        adjusted_service_time = raw_service_time / shortest_atm.speed_multiplier
        customer.service_duration = adjusted_service_time

        if customer.transaction_type == TransactionType.CASH_WITHDRAWAL:
            if not shortest_atm.deduct_cash(customer.requested_amount):
                customer.status = CustomerStatus.FAILED_OUT_OF_CASH
                customer.completion_time = self.env.now
                shortest_atm.finish_service()
                shortest_atm.resource.release(req)
                self._log_event("FAILED_OUT_OF_CASH", customer.customer_id, shortest_atm.atm_id)
                return

        yield self.env.timeout(adjusted_service_time)

        # 4. Completion
        customer.completion_time = self.env.now
        customer.status = CustomerStatus.COMPLETED
        shortest_atm.finish_service()
        shortest_atm.resource.release(req)

        self._log_event("SERVICE_COMPLETED", customer.customer_id, shortest_atm.atm_id,
                        f"Duration: {round(adjusted_service_time, 1)}s")

    def customer_arrival_generator(self):
        """SimPy process generating arriving customers over the simulation horizon."""
        cust_id = 1
        while self.env.now < self.config.sim_duration_seconds:
            interarrival = self.arrival_process.next_interarrival_time(self.env.now, self.rng)
            yield self.env.timeout(interarrival)

            if self.env.now > self.config.sim_duration_seconds:
                break

            # Assign transaction type
            tx_type = self.tx_manager.sample_transaction_type(self.rng)

            # Assign withdrawal amount if cash withdrawal
            withdrawal_amount = 0.0
            if tx_type == TransactionType.CASH_WITHDRAWAL:
                # Common ATM amounts: 500, 1000, 2000, 5000, 10000
                withdrawal_amount = float(self.rng.choice([500, 1000, 2000, 2500, 5000, 10000]))

            # Sample customer patience if enabled
            patience = None
            if self.config.customer_patience_mean is not None:
                patience = float(self.rng.exponential(scale=self.config.customer_patience_mean))

            customer = Customer(
                customer_id=cust_id,
                arrival_time=self.env.now,
                transaction_type=tx_type,
                requested_amount=withdrawal_amount,
                patience_limit=patience,
            )
            self.customers.append(customer)
            self._log_event("ARRIVED", customer.customer_id, details=f"Type: {tx_type.value}")

            # Fork customer lifecycle process
            if self.config.queue_policy_type == "shortest_queue":
                self.env.process(self.customer_process_dedicated(customer))
            else:
                self.env.process(self.customer_process_pooled(customer))

            cust_id += 1

    def run(self) -> SimulationResult:
        """Execute discrete event simulation up to sim_duration_seconds."""
        # Register arrival generator process
        self.env.process(self.customer_arrival_generator())

        # Run SimPy simulation
        self.env.run(until=self.config.sim_duration_seconds)

        # Collect metrics
        completed = [c for c in self.customers if c.status == CustomerStatus.COMPLETED]
        abandoned = [c for c in self.customers if c.status == CustomerStatus.ABANDONED]
        failed = [c for c in self.customers if c.status.value.startswith("FAILED")]
        in_service_at_end = [c for c in self.customers if c.status == CustomerStatus.IN_SERVICE]
        waiting_at_end = [c for c in self.customers if c.status in (CustomerStatus.QUEUED, CustomerStatus.ARRIVED)]

        waiting_times = [c.waiting_time for c in completed] or [0.0]
        service_times = [c.service_duration for c in completed] or [0.0]
        system_times = [c.system_time for c in completed] or [0.0]

        avg_waiting = float(np.mean(waiting_times))
        max_waiting = float(np.max(waiting_times))
        p95_waiting = float(np.percentile(waiting_times, 95))
        avg_service = float(np.mean(service_times))
        avg_system = float(np.mean(system_times))

        time_weighted_lq = self.queue_manager.get_time_weighted_average_queue_length(self.config.sim_duration_seconds)

        # ATM-wise utilization
        atm_metrics = [atm.to_dict(self.config.sim_duration_seconds) for atm in self.atms]
        avg_utilization = float(np.mean([m["utilization"] for m in atm_metrics]))

        # Throughput
        hours = self.config.sim_duration_seconds / 3600.0
        throughput = len(completed) / hours if hours > 0 else 0.0

        # Little's Law verification:
        # Effective arrival rate lambda_eff = completed / duration
        lambda_eff_sec = len(completed) / self.config.sim_duration_seconds if self.config.sim_duration_seconds > 0 else 0.0
        littles_lq_theoretical = lambda_eff_sec * avg_waiting
        littles_l_theoretical = lambda_eff_sec * avg_system
        relative_lq_error = (
            abs(time_weighted_lq - littles_lq_theoretical) / max(0.01, time_weighted_lq)
        )

        littles_law = {
            "lambda_effective_per_sec": round(lambda_eff_sec, 5),
            "simulated_time_weighted_Lq": round(time_weighted_lq, 3),
            "theoretical_littles_Lq": round(littles_lq_theoretical, 3),
            "theoretical_littles_L": round(littles_l_theoretical, 3),
            "relative_error": round(relative_lq_error, 4),
        }

        return SimulationResult(
            config=self.config,
            total_customers_arrived=len(self.customers),
            completed_customers=len(completed),
            abandoned_customers=len(abandoned),
            failed_customers=len(failed),
            waiting_at_end=len(waiting_at_end),
            in_service_at_end=len(in_service_at_end),
            average_waiting_time_sec=avg_waiting,
            max_waiting_time_sec=max_waiting,
            p95_waiting_time_sec=p95_waiting,
            average_service_time_sec=avg_service,
            average_system_time_sec=avg_system,
            time_weighted_queue_length=time_weighted_lq,
            average_atm_utilization=avg_utilization,
            throughput_per_hour=throughput,
            atm_metrics=atm_metrics,
            littles_law_verification=littles_law,
            queue_history=[[t, q] for t, q in self.queue_manager.queue_history],
            customer_records=[c.to_dict() for c in self.customers],
            events_log=self.events_log,
        )

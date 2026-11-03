"""
Comprehensive Pytest Test Suite for ATMFlow Intelligence
SPMS Course: Solving Problems Using Modelling and Simulation (NEC00091)
"""

import pytest
import numpy as np
from simulation.customer import CustomerStatus
from simulation.transactions import TransactionType, TransactionManager
from simulation.arrivals import HomogeneousPoissonArrival, PeakHourPoissonArrival
from simulation.engine import SimulationEngine, SimulationConfig
from analytics.queue_theory import MMCQueueModel


def test_customer_generation_and_accounting():
    """Verify customer generation and strict conservation of total arrived customers."""
    config = SimulationConfig(random_seed=42, sim_duration_seconds=3600, num_atms=3, arrival_rate_per_min=1.5)
    engine = SimulationEngine(config)
    res = engine.run()

    assert res.total_customers_arrived > 0
    assert len(engine.customers) == res.total_customers_arrived

    # Sum of all outcomes
    completed = res.completed_customers
    abandoned = res.abandoned_customers
    failed = res.failed_customers
    in_system = sum(1 for c in engine.customers if c.status in (CustomerStatus.QUEUED, CustomerStatus.IN_SERVICE, CustomerStatus.ARRIVED))

    accounted_total = completed + abandoned + failed + in_system
    assert res.total_customers_arrived == accounted_total


def test_fifo_service_ordering():
    """Verify that in Pooled FIFO, customers start service in arrival order."""
    config = SimulationConfig(random_seed=12, sim_duration_seconds=1800, num_atms=1, arrival_rate_per_min=2.0)
    engine = SimulationEngine(config)
    res = engine.run()

    completed_custs = [c for c in engine.customers if c.service_start_time is not None]
    for i in range(len(completed_custs) - 1):
        # Arrival time order must match service start time order
        assert completed_custs[i].arrival_time <= completed_custs[i + 1].arrival_time
        assert completed_custs[i].service_start_time <= completed_custs[i + 1].service_start_time


def test_multiple_atms_parallel_operation():
    """Verify multiple ATMs serve customers concurrently."""
    config = SimulationConfig(random_seed=77, sim_duration_seconds=3600, num_atms=4, arrival_rate_per_min=2.5)
    engine = SimulationEngine(config)
    res = engine.run()

    assert len(res.atm_metrics) == 4
    for atm in res.atm_metrics:
        assert atm["total_customers_served"] > 0
        assert atm["utilization"] >= 0.0 and atm["utilization"] <= 1.0


def test_waiting_time_non_negativity():
    """Verify waiting times and service times are strictly non-negative."""
    config = SimulationConfig(random_seed=101, sim_duration_seconds=1800, num_atms=2, arrival_rate_per_min=1.2)
    engine = SimulationEngine(config)
    res = engine.run()

    for c in engine.customers:
        assert c.waiting_time >= 0.0
        if c.is_completed:
            assert c.service_duration > 0.0
            assert c.system_time >= c.service_duration - 1e-5


def test_atm_utilization_bounds():
    """Verify overall network ATM utilization remains in valid range [0.0, 1.0]."""
    config = SimulationConfig(random_seed=88, sim_duration_seconds=3600, num_atms=3, arrival_rate_per_min=1.8)
    engine = SimulationEngine(config)
    res = engine.run()

    assert 0.0 <= res.average_atm_utilization <= 1.0


def test_reproducibility_with_seed():
    """Verify identical random seeds produce identical simulation outputs."""
    config1 = SimulationConfig(random_seed=555, sim_duration_seconds=1800, num_atms=2, arrival_rate_per_min=1.5)
    config2 = SimulationConfig(random_seed=555, sim_duration_seconds=1800, num_atms=2, arrival_rate_per_min=1.5)

    res1 = SimulationEngine(config1).run()
    res2 = SimulationEngine(config2).run()

    assert res1.total_customers_arrived == res2.total_customers_arrived
    assert res1.completed_customers == res2.completed_customers
    assert abs(res1.average_waiting_time_sec - res2.average_waiting_time_sec) < 1e-4


def test_capacity_increase_reduces_waiting_time():
    """Verify that adding ATMs reduces or maintains average customer queue waiting time."""
    config_1atm = SimulationConfig(random_seed=42, sim_duration_seconds=3600, num_atms=1, arrival_rate_per_min=1.0)
    config_3atms = SimulationConfig(random_seed=42, sim_duration_seconds=3600, num_atms=3, arrival_rate_per_min=1.0)

    res_1atm = SimulationEngine(config_1atm).run()
    res_3atms = SimulationEngine(config_3atms).run()

    assert res_3atms.average_waiting_time_sec < res_1atm.average_waiting_time_sec


def test_littles_law_consistency():
    """Verify Little's Law relationship (Lq ≈ lambda_eff * Wq)."""
    config = SimulationConfig(random_seed=999, sim_duration_seconds=7200, num_atms=3, arrival_rate_per_min=1.2)
    res = SimulationEngine(config).run()

    lq_sim = res.time_weighted_queue_length
    lq_theo = res.littles_law_verification["theoretical_littles_Lq"]
    # Relative error should be small
    assert abs(lq_sim - lq_theo) < 1.5


def test_mmc_queueing_theory_calculator():
    """Verify M/M/c analytical formula calculations."""
    # M/M/1 example: λ = 0.5 cust/min, μ = 1.0 cust/min, c = 1
    result = MMCQueueModel.calculate(arrival_rate_lambda=0.5, service_rate_mu=1.0, num_servers_c=1)

    assert result.is_stable is True
    assert abs(result.server_utilization_rho - 0.5) < 1e-4
    assert abs(result.avg_queue_length_lq - 0.5) < 1e-4  # Lq = ρ^2 / (1-ρ) = 0.25 / 0.5 = 0.5
    assert abs(result.avg_waiting_time_wq - 1.0) < 1e-4  # Wq = Lq / λ = 0.5 / 0.5 = 1.0 min

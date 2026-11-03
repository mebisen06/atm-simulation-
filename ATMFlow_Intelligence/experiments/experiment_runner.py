"""
Experiment Runner Module for ATMFlow Intelligence
SPMS Course: Solving Problems Using Modelling and Simulation (NEC00091)
"""

from typing import Dict, List, Any
import pandas as pd
from simulation.engine import SimulationEngine, SimulationConfig
from simulation.transactions import TransactionManager, TransactionProfile, TransactionType


class ExperimentRunner:
    """Executes structured multi-scenario simulation experiments for performance comparison."""

    @staticmethod
    def run_experiment_1_atm_count(
        sim_duration_seconds: float = 7200.0,
        arrival_rate_per_min: float = 1.5,
        random_seed: int = 42,
        atm_counts: List[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Experiment 1: Effect of ATM Count on Queue Performance.
        Evaluates system performance across different ATM capacities (e.g. 1, 2, 3, 4, 5 ATMs).
        """
        if atm_counts is None:
            atm_counts = [1, 2, 3, 4, 5]

        results = []
        for count in atm_counts:
            config = SimulationConfig(
                random_seed=random_seed,
                sim_duration_seconds=sim_duration_seconds,
                num_atms=count,
                arrival_rate_per_min=arrival_rate_per_min,
                queue_policy_type="pooled_fifo",
                arrival_process_type="homogeneous"
            )
            engine = SimulationEngine(config)
            res = engine.run()
            results.append({
                "atm_count": count,
                "total_arrived": res.total_customers_arrived,
                "completed": res.completed_customers,
                "abandoned": res.abandoned_customers,
                "avg_waiting_time_min": round(res.average_waiting_time_sec / 60.0, 2),
                "p95_waiting_time_min": round(res.p95_waiting_time_sec / 60.0, 2),
                "max_waiting_time_min": round(res.max_waiting_time_sec / 60.0, 2),
                "avg_queue_length": round(res.time_weighted_queue_length, 2),
                "avg_atm_utilization_pct": round(res.average_atm_utilization * 100.0, 2),
                "throughput_per_hr": round(res.throughput_per_hour, 1),
            })
        return results

    @staticmethod
    def run_experiment_2_arrival_rate(
        sim_duration_seconds: float = 7200.0,
        num_atms: int = 3,
        random_seed: int = 42,
        traffic_scenarios: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Experiment 2: Effect of Customer Arrival Rate (Traffic Intensity).
        Evaluates system performance across Low, Medium, and High traffic intensity.
        """
        if traffic_scenarios is None:
            traffic_scenarios = {
                "Low Traffic (0.5 cust/min)": 0.5,
                "Medium Traffic (1.5 cust/min)": 1.5,
                "High Traffic (3.0 cust/min)": 3.0,
                "Surge Spike Traffic (4.5 cust/min)": 4.5,
            }

        results = []
        for name, rate in traffic_scenarios.items():
            config = SimulationConfig(
                random_seed=random_seed,
                sim_duration_seconds=sim_duration_seconds,
                num_atms=num_atms,
                arrival_rate_per_min=rate,
                queue_policy_type="pooled_fifo",
                arrival_process_type="homogeneous"
            )
            engine = SimulationEngine(config)
            res = engine.run()
            results.append({
                "scenario_name": name,
                "arrival_rate_per_min": rate,
                "total_arrived": res.total_customers_arrived,
                "completed": res.completed_customers,
                "avg_waiting_time_min": round(res.average_waiting_time_sec / 60.0, 2),
                "p95_waiting_time_min": round(res.p95_waiting_time_sec / 60.0, 2),
                "avg_queue_length": round(res.time_weighted_queue_length, 2),
                "avg_atm_utilization_pct": round(res.average_atm_utilization * 100.0, 2),
                "throughput_per_hr": round(res.throughput_per_hour, 1),
            })
        return results

    @staticmethod
    def run_experiment_3_service_time(
        sim_duration_seconds: float = 7200.0,
        num_atms: int = 3,
        arrival_rate_per_min: float = 1.5,
        random_seed: int = 42
    ) -> List[Dict[str, Any]]:
        """
        Experiment 3: Effect of Transaction Service Duration / Machine Speed.
        Evaluates system performance across Fast, Standard, and Slow ATM transaction speeds.
        """
        speed_scenarios = {
            "Fast Service (0.6x duration)": [1.667] * num_atms,
            "Standard Service (1.0x duration)": [1.0] * num_atms,
            "Slow Service (1.5x duration)": [0.667] * num_atms,
        }

        results = []
        for name, speeds in speed_scenarios.items():
            config = SimulationConfig(
                random_seed=random_seed,
                sim_duration_seconds=sim_duration_seconds,
                num_atms=num_atms,
                arrival_rate_per_min=arrival_rate_per_min,
                queue_policy_type="pooled_fifo",
                atm_speeds=speeds
            )
            engine = SimulationEngine(config)
            res = engine.run()
            results.append({
                "service_scenario": name,
                "avg_service_time_sec": round(res.average_service_time_sec, 1),
                "completed": res.completed_customers,
                "avg_waiting_time_min": round(res.average_waiting_time_sec / 60.0, 2),
                "p95_waiting_time_min": round(res.p95_waiting_time_sec / 60.0, 2),
                "avg_queue_length": round(res.time_weighted_queue_length, 2),
                "avg_atm_utilization_pct": round(res.average_atm_utilization * 100.0, 2),
                "throughput_per_hr": round(res.throughput_per_hour, 1),
            })
        return results

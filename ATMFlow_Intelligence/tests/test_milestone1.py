"""
Unit and Integration Test Suite for Milestone 1
ATMFlow Intelligence - Core Discrete Event Simulation Engine
SPMS Course: Solving Problems Using Modelling and Simulation (NEC00091)
"""

import unittest
import numpy as np
from simulation.customer import CustomerStatus
from simulation.transactions import TransactionType, TransactionManager
from simulation.arrivals import HomogeneousPoissonArrival, PeakHourPoissonArrival
from simulation.engine import SimulationEngine, SimulationConfig


class TestMilestone1SimulationEngine(unittest.TestCase):
    """Rigorous verification of Milestone 1 simulation mechanics."""

    def test_reproducibility_with_seed(self):
        """Verify that identical random seeds produce identical simulation traces."""
        config1 = SimulationConfig(random_seed=123, sim_duration_seconds=1800, num_atms=2, arrival_rate_per_min=1.5)
        config2 = SimulationConfig(random_seed=123, sim_duration_seconds=1800, num_atms=2, arrival_rate_per_min=1.5)

        engine1 = SimulationEngine(config1)
        res1 = engine1.run()

        engine2 = SimulationEngine(config2)
        res2 = engine2.run()

        self.assertEqual(res1.total_customers_arrived, res2.total_customers_arrived)
        self.assertEqual(res1.completed_customers, res2.completed_customers)
        self.assertAlmostEqual(res1.average_waiting_time_sec, res2.average_waiting_time_sec, places=4)
        self.assertAlmostEqual(res1.average_atm_utilization, res2.average_atm_utilization, places=4)
        print("✓ Test Reproducibility passed: Identical traces generated.")

    def test_customer_conservation(self):
        """Verify that every arrived customer is accounted for without duplication."""
        config = SimulationConfig(random_seed=42, sim_duration_seconds=2400, num_atms=3, arrival_rate_per_min=2.0)
        engine = SimulationEngine(config)
        res = engine.run()

        total_arrived = len(engine.customers)
        self.assertEqual(total_arrived, res.total_customers_arrived)

        # Count by terminal / intermediate state
        completed = sum(1 for c in engine.customers if c.status == CustomerStatus.COMPLETED)
        abandoned = sum(1 for c in engine.customers if c.status == CustomerStatus.ABANDONED)
        failed = sum(1 for c in engine.customers if c.status.value.startswith("FAILED"))
        in_system = sum(1 for c in engine.customers if c.status in (CustomerStatus.QUEUED, CustomerStatus.IN_SERVICE, CustomerStatus.ARRIVED))

        accounted_total = completed + abandoned + failed + in_system
        self.assertEqual(total_arrived, accounted_total)
        self.assertEqual(completed, res.completed_customers)
        print(f"✓ Test Customer Conservation passed: {total_arrived} customers perfectly accounted for.")

    def test_non_negative_timings(self):
        """Ensure no negative waiting times, service times, or queue lengths."""
        config = SimulationConfig(random_seed=99, sim_duration_seconds=1800, num_atms=2, arrival_rate_per_min=1.8)
        engine = SimulationEngine(config)
        res = engine.run()

        for c in engine.customers:
            self.assertGreaterEqual(c.waiting_time, 0.0)
            if c.is_completed:
                self.assertGreater(c.service_duration, 0.0)
                self.assertGreaterEqual(c.system_time, c.service_duration)

        for timestamp, q_len in res.queue_history:
            self.assertGreaterEqual(q_len, 0)

        print("✓ Test Timing Non-Negativity passed: All wait/service/queue metrics strictly non-negative.")

    def test_atm_utilization_bounds(self):
        """Verify individual and network ATM utilization stays strictly within [0.0, 1.0]."""
        config = SimulationConfig(random_seed=77, sim_duration_seconds=3600, num_atms=4, arrival_rate_per_min=2.2)
        engine = SimulationEngine(config)
        res = engine.run()

        self.assertGreaterEqual(res.average_atm_utilization, 0.0)
        self.assertLessEqual(res.average_atm_utilization, 1.0)

        for atm_info in res.atm_metrics:
            rho = atm_info["utilization"]
            self.assertGreaterEqual(rho, 0.0)
            self.assertLessEqual(rho, 1.0)
            self.assertGreaterEqual(atm_info["total_customers_served"], 0)

        print(f"✓ Test ATM Utilization Bounds passed: Network rho = {res.average_atm_utilization:.4f} in [0, 1].")

    def test_shortest_queue_policy(self):
        """Verify dedicated multi-queue policy functions properly."""
        config = SimulationConfig(
            random_seed=55,
            sim_duration_seconds=1800,
            num_atms=3,
            arrival_rate_per_min=2.0,
            queue_policy_type="shortest_queue"
        )
        engine = SimulationEngine(config)
        res = engine.run()

        self.assertGreater(res.total_customers_arrived, 0)
        self.assertGreater(res.completed_customers, 0)
        print(f"✓ Test Shortest Queue Policy passed: Completed {res.completed_customers}/{res.total_customers_arrived} customers.")

    def test_customer_reneging_patience(self):
        """Verify that finite customer patience triggers reneging when queues are overloaded."""
        config = SimulationConfig(
            random_seed=11,
            sim_duration_seconds=3600,
            num_atms=1,  # Single ATM with heavy load to cause queue buildup
            arrival_rate_per_min=3.0,
            customer_patience_mean=60.0  # Impatient customers: leaves after ~60s wait
        )
        engine = SimulationEngine(config)
        res = engine.run()

        self.assertGreater(res.abandoned_customers, 0)
        self.assertGreater(res.completed_customers, 0)
        print(f"✓ Test Reneging / Abandonment passed: {res.abandoned_customers} customers reneged due to queue delays.")

    def test_littles_law_order_of_magnitude(self):
        """
        Verify Little's Law relationship:
        L_q approx lambda_effective * W_q
        """
        config = SimulationConfig(random_seed=888, sim_duration_seconds=7200, num_atms=3, arrival_rate_per_min=1.2)
        engine = SimulationEngine(config)
        res = engine.run()

        sim_lq = res.time_weighted_queue_length
        theo_lq = res.littles_law_verification["theoretical_littles_Lq"]
        print(f"  Little's Law Check: Simulated Lq={sim_lq:.3f}, Theoretical lambda*Wq={theo_lq:.3f}")
        # Both should match reasonably well on a stationary run
        diff = abs(sim_lq - theo_lq)
        self.assertLess(diff, 1.5, f"Little's Law deviation too large: {diff}")
        print("✓ Test Little's Law passed: Simulated Lq aligns with lambda_eff * Wq.")


if __name__ == "__main__":
    unittest.main()

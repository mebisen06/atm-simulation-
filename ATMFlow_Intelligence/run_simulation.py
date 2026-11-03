#!/usr/bin/env python3
"""
ATMFlow Intelligence - Execution Runner
SPMS Course: Solving Problems Using Modelling and Simulation (NEC00091)
Team: Meet Bisen (BTCD25O1081), Moully Acharya (BTCD25O1084), Nishita Narwal (BTCD25O1088)

Executes a full simulation run using SimPy, validates Little's Law, and prints formatted output.
"""

import os
import json
import argparse
from simulation.engine import SimulationEngine, SimulationConfig
from simulation.transactions import TransactionType
from analytics.metrics import MetricsCalculator


def main():
    parser = argparse.ArgumentParser(description="ATMFlow Intelligence - Simulation Runner")
    parser.add_argument("--atms", type=int, default=3, help="Number of ATMs (1-20)")
    parser.add_argument("--duration", type=float, default=7200.0, help="Simulation duration in seconds (default 7200s = 2hr)")
    parser.add_argument("--rate", type=float, default=1.5, help="Customer arrival rate in customers/min (default 1.5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--policy", type=str, default="pooled_fifo", choices=["pooled_fifo", "shortest_queue"], help="Queue policy")
    parser.add_argument("--arrival", type=str, default="homogeneous", choices=["homogeneous", "peak_hour", "surge"], help="Arrival process")
    parser.add_argument("--patience", type=float, default=None, help="Mean customer patience in seconds (None for infinite)")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("   ATMFlow Intelligence: Advanced ATM Network Simulation System")
    print("   Course: Solving Problems Using Modelling and Simulation (NEC00091)")
    print("   Team: Meet Bisen | Moully Acharya | Nishita Narwal")
    print("=" * 70)

    config = SimulationConfig(
        random_seed=args.seed,
        sim_duration_seconds=args.duration,
        num_atms=args.atms,
        arrival_rate_per_min=args.rate,
        arrival_process_type=args.arrival,
        queue_policy_type=args.policy,
        customer_patience_mean=args.patience,
    )

    print(f"\n[INIT] Initializing SimPy engine with {config.num_atms} ATMs, policy='{config.queue_policy_type}'")
    print(f"[INIT] Arrival process: {config.arrival_process_type} at {config.arrival_rate_per_min} cust/min")
    print(f"[RUN]  Executing simulation for {config.sim_duration_seconds / 60:.1f} simulated minutes (Seed={config.random_seed})...")

    engine = SimulationEngine(config)
    result = engine.run()

    print("[DONE] Simulation run completed successfully!\n")

    # Overview Table
    summary = result.to_summary_dict()
    rows = [
        ("Total Customers Arrived", summary["total_arrived"]),
        ("Completed Transactions", summary["completed"]),
        ("Abandoned Customers (Reneged)", summary["abandoned"]),
        ("Failed Transactions (Out of Cash)", summary["failed"]),
        ("Completion Rate (%)", f"{summary['completion_rate_pct']}%"),
        ("Average Queue Waiting Time (Wq)", f"{summary['avg_waiting_time_sec']} sec ({summary['avg_waiting_time_sec']/60:.2f} min)"),
        ("95th Percentile Waiting Time (P95)", f"{summary['p95_waiting_time_sec']} sec ({summary['p95_waiting_time_sec']/60:.2f} min)"),
        ("Max Customer Waiting Time", f"{summary['max_waiting_time_sec']} sec"),
        ("Average Service Duration (E[S])", f"{summary['avg_service_time_sec']} sec"),
        ("Average System Time (W = Wq + S)", f"{summary['avg_system_time_sec']} sec"),
        ("Time-Weighted Queue Length (Lq)", f"{summary['time_weighted_queue_length']} customers"),
        ("Average Network ATM Utilization (rho)", f"{summary['average_atm_utilization']*100:.2f}%"),
        ("System Throughput", f"{summary['throughput_per_hour']} customers/hr"),
    ]
    print(MetricsCalculator.format_ascii_table("EXECUTIVE SIMULATION PERFORMANCE SUMMARY", rows))

    # ATM-wise table
    print("\n=== INDIVIDUAL ATM UTILIZATION & PERFORMANCE ===")
    print(f"{'ATM ID':<10} | {'Status':<10} | {'Served':<8} | {'Busy Time (s)':<14} | {'Utilization':<12} | {'Cash Left':<12}")
    print("-" * 75)
    for atm in result.atm_metrics:
        print(f"{atm['atm_id']:<10} | {atm['status']:<10} | {atm['total_customers_served']:<8} | {atm['total_busy_time']:<14.1f} | {atm['utilization']*100:>10.2f}% | ₹{atm['cash_balance']:>10,.0f}")
    print("-" * 75)

    # Little's Law Verification
    ll = summary["littles_law"]
    ll_rows = [
        ("Effective Arrival Rate (lambda_eff)", f"{ll['lambda_effective_per_sec']:.5f} cust/sec ({ll['lambda_effective_per_sec']*3600:.1f}/hr)"),
        ("Simulated Time-Weighted Lq", f"{ll['simulated_time_weighted_Lq']:.3f}"),
        ("Theoretical Little's Lq = lambda * Wq", f"{ll['theoretical_littles_Lq']:.3f}"),
        ("Relative Error |Lq - lambda*Wq| / Lq", f"{ll['relative_error']*100:.2f}%"),
        ("Theoretical System Occupancy L = lambda * W", f"{ll['theoretical_littles_L']:.3f}"),
    ]
    print(MetricsCalculator.format_ascii_table("MATHEMATICAL QUEUEING VALIDATION (LITTLE'S LAW)", ll_rows))

    # Save to data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(script_dir, "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "simulation_results.json")
    with open(out_file, "w") as f:
        json.dump({
            "summary": summary,
            "atm_metrics": result.atm_metrics,
            "queue_history": result.queue_history,
            "sample_customers": result.customer_records[:20],
            "total_events_logged": len(result.events_log),
        }, f, indent=2)
    # Also save to root data dir if different
    root_data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(root_data_dir, exist_ok=True)
    with open(os.path.join(root_data_dir, "simulation_results.json"), "w") as f:
        json.dump({
            "summary": summary,
            "atm_metrics": result.atm_metrics,
            "queue_history": result.queue_history,
            "sample_customers": result.customer_records[:20],
            "total_events_logged": len(result.events_log),
        }, f, indent=2)
    print(f"\n[EXPORT] Full simulation dataset written to: {out_file}")


if __name__ == "__main__":
    main()

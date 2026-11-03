#!/usr/bin/env python3
"""
ATMFlow Intelligence — ATM Transaction & Queue Simulation
Course: Solving Problems Using Modelling and Simulation (SPMS • NEC00091)
Team: Meet Bisen (BTCD25O1081) | Moully Acharya (BTCD25O1084) | Nishita Narwal (BTCD25O1088)

Terminal-Based Simulation Application using SimPy, NumPy, Pandas & Matplotlib.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
# Use non-interactive backend for server environment
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Insert current path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ATMFlow_Intelligence"))

from simulation.engine import SimulationEngine, SimulationConfig, SimulationResult
from simulation.customer import CustomerStatus
from simulation.transactions import TransactionType, TransactionManager
from analytics.metrics import MetricsCalculator
from experiments.experiment_runner import ExperimentRunner


# Global in-memory storage for last simulation run and experiment data
latest_simulation_result: SimulationResult = None
latest_experiment_results: list = None


def clear_screen():
    """Optional console clear for clean terminal output."""
    pass


def print_banner():
    """Display terminal menu header."""
    print("\n" + "=" * 42)
    print("       ATMFlow Intelligence")
    print(" ATM Transaction & Queue Simulation")
    print("=" * 42)


def get_user_input_with_default(prompt: str, default_val, val_type=float):
    """Prompt user for input with default fallback and type validation."""
    while True:
        user_str = input(f"{prompt} [default {default_val}]: ").strip()
        if not user_str:
            return default_val
        try:
            val = val_type(user_str)
            if val <= 0 and val_type in (int, float):
                print("❌ Value must be strictly positive. Please try again.")
                continue
            return val
        except ValueError:
            print(f"❌ Invalid input. Expected {val_type.__name__}. Please try again.")


def run_new_simulation_menu():
    """Menu Option 1: Prompts inputs and executes genuine SimPy simulation."""
    global latest_simulation_result
    print("\n--- RUN NEW SIMULATION ---")
    
    num_atms = get_user_input_with_default("Enter Number of ATMs (1-10)", 3, int)
    duration_mins = get_user_input_with_default("Enter Simulation Duration in minutes", 120.0, float)
    arrival_rate = get_user_input_with_default("Enter Customer Arrival Rate (per minute)", 1.5, float)
    seed = get_user_input_with_default("Enter Random Seed", 42, int)

    print(f"\n[EXEC] Executing SimPy Engine: {num_atms} ATMs, {duration_mins} mins, λ={arrival_rate}/min, Seed={seed}...")

    config = SimulationConfig(
        random_seed=seed,
        sim_duration_seconds=duration_mins * 60.0,
        num_atms=num_atms,
        arrival_rate_per_min=arrival_rate,
        queue_policy_type="pooled_fifo",
        arrival_process_type="homogeneous"
    )

    engine = SimulationEngine(config)
    result = engine.run()
    latest_simulation_result = result

    # Save to results JSON
    os.makedirs("results", exist_ok=True)
    with open("results/simulation_results.json", "w") as f:
        json.dump({
            "summary": result.to_summary_dict(),
            "atm_metrics": result.atm_metrics,
            "sample_customers": result.customer_records[:50],
        }, f, indent=2)

    print("✅ Simulation execution completed successfully!\n")
    display_simulation_results(result)


def display_simulation_results(result: SimulationResult):
    """Prints formatted ASCII summary tables for a SimulationResult."""
    summary = result.to_summary_dict()

    print("\n=== EXECUTIVE SIMULATION PERFORMANCE SUMMARY ===")
    print("-" * 55)
    print(f"{'Total Customers Arrived':<35}: {summary['total_arrived']:>16}")
    print(f"{'Total Customers Completed':<35}: {summary['completed']:>16}")
    print(f"{'Customers Waiting in Queue at End':<35}: {summary['waiting_at_end']:>16}")
    print(f"{'Customers In Service at End':<35}: {summary['in_service_at_end']:>16}")
    print(f"{'Abandoned Customers (Reneged)':<35}: {summary['abandoned']:>16}")
    print(f"{'Completion Rate (%)':<35}: {summary['completion_rate_pct']:>15}%")
    print(f"{'Average Queue Waiting Time (Wq)':<35}: {summary['avg_waiting_time_sec']/60.0:>12.2f} min")
    print(f"{'95th Percentile Waiting Time (P95)':<35}: {summary['p95_waiting_time_sec']/60.0:>12.2f} min")
    print(f"{'Max Customer Waiting Time':<35}: {summary['max_waiting_time_sec']/60.0:>12.2f} min")
    print(f"{'Average Service Duration (E[S])':<35}: {summary['avg_service_time_sec']:>12.1f} sec")
    print(f"{'Time-Weighted Queue Length (Lq)':<35}: {summary['time_weighted_queue_length']:>16.3f}")
    print(f"{'Average Network ATM Utilization':<35}: {summary['average_atm_utilization']*100.0:>15.2f}%")
    print(f"{'System Throughput':<35}: {summary['throughput_per_hour']:>12.1f} cust/hr")
    print("-" * 55)

    # Customer Conservation Check
    accounting_check = summary['completed'] + summary['waiting_at_end'] + summary['in_service_at_end'] + summary['abandoned'] + summary['failed']
    print(f"🔒 Customer Conservation Check: Arrived ({summary['total_arrived']}) == Accounted ({accounting_check}) -> {'PASSED ✅' if summary['total_arrived'] == accounting_check else 'FAILED ❌'}")

    # Per-ATM Statistics
    print("\n=== INDIVIDUAL ATM UTILIZATION & PERFORMANCE ===")
    print(f"{'ATM ID':<10} | {'Status':<10} | {'Served':<8} | {'Busy Duration':<14} | {'Utilization':<12} | {'Cash Left':<12}")
    print("-" * 75)
    for atm in result.atm_metrics:
        busy_min = atm['total_busy_time'] / 60.0
        util_pct = atm['utilization'] * 100.0
        print(f"{atm['atm_id']:<10} | {atm['status']:<10} | {atm['total_customers_served']:<8} | {busy_min:>10.1f} min | {util_pct:>10.2f}% | ₹{atm['cash_balance']:>10,.0f}")
    print("-" * 75)


def view_last_simulation_results():
    """Menu Option 2: View results of last executed simulation."""
    global latest_simulation_result
    if latest_simulation_result is None:
        print("\n❌ No simulation has been executed yet.")
        return
    display_simulation_results(latest_simulation_result)


def view_customer_event_log():
    """Menu Option 3: View customer event log table."""
    global latest_simulation_result
    if latest_simulation_result is None:
        print("\n❌ No simulation has been executed yet.")
        return

    records = latest_simulation_result.customer_records
    print(f"\n=== CUSTOMER EVENT LOG ({len(records)} Total Customers) ===")
    
    # Prompt how many records to display
    show_count = 20
    if len(records) > 20:
        ans = input("Display all records or first 20? (type 'all' or press Enter for 20): ").strip().lower()
        if ans == 'all':
            show_count = len(records)

    print(f"{'ID':<6} | {'Arrival (m)':<11} | {'Transaction':<16} | {'Wait (s)':<9} | {'ATM Assigned':<12} | {'Status':<12}")
    print("-" * 78)
    for c in records[:show_count]:
        arr_m = round(c['arrival_time'] / 60.0, 2)
        tx = c['transaction_type']
        wait_s = c['waiting_time']
        atm = c['assigned_atm_id'] or "N/A"
        status = c['status']
        print(f"{c['customer_id']:<6} | {arr_m:<11.2f} | {tx:<16} | {wait_s:<9.1f} | {atm:<12} | {status:<12}")
    print("-" * 78)


def run_atm_comparison_experiment():
    """Menu Option 4: Compare 1, 2, 3, 4, and 5 ATMs on fair workload."""
    global latest_experiment_results
    print("\n--- ATM COMPARISON EXPERIMENT (1 to 5 ATMs) ---")
    print("Running simulations across 1, 2, 3, 4, 5 ATMs with synchronized workload...")

    duration_mins = 120.0
    arrival_rate = 1.5
    seed = 42

    atm_counts = [1, 2, 3, 4, 5]
    results = []

    for count in atm_counts:
        config = SimulationConfig(
            random_seed=seed,
            sim_duration_seconds=duration_mins * 60.0,
            num_atms=count,
            arrival_rate_per_min=arrival_rate,
            queue_policy_type="pooled_fifo"
        )
        engine = SimulationEngine(config)
        res = engine.run()
        results.append({
            "atm_count": count,
            "total_arrived": res.total_customers_arrived,
            "completed": res.completed_customers,
            "avg_waiting_time_min": round(res.average_waiting_time_sec / 60.0, 2),
            "avg_queue_length": round(res.time_weighted_queue_length, 2),
            "avg_atm_utilization_pct": round(res.average_atm_utilization * 100.0, 2),
            "throughput_per_hr": round(res.throughput_per_hour, 1),
        })

    latest_experiment_results = results

    # Print Comparison Table
    print("\n=== ATM CONFIGURATION COMPARISON TABLE ===")
    print(f"{'ATM Count':<10} | {'Completed':<10} | {'Avg Wait Time (min)':<20} | {'Avg Queue Length':<18} | {'ATM Utilization':<16}")
    print("-" * 82)
    for r in results:
        print(f"{r['atm_count']:<10} | {r['completed']:<10} | {r['avg_waiting_time_min']:<20.2f} | {r['avg_queue_length']:<18.2f} | {r['avg_atm_utilization_pct']:>14.2f}%")
    print("-" * 82)

    # Generate Matplotlib chart
    try:
        os.makedirs("results", exist_ok=True)
        counts = [r["atm_count"] for r in results]
        waits = [r["avg_waiting_time_min"] for r in results]
        utils = [r["avg_atm_utilization_pct"] for r in results]
        queues = [r["avg_queue_length"] for r in results]

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.5))

        ax1.plot(counts, waits, 'o-', color='#0284c7', linewidth=2, markersize=8)
        ax1.set_title("ATM Count vs Average Wait Time (min)")
        ax1.set_xlabel("Number of ATMs")
        ax1.set_ylabel("Wait Time (Minutes)")
        ax1.grid(True, linestyle='--', alpha=0.5)

        ax2.plot(counts, queues, 's-', color='#f59e0b', linewidth=2, markersize=8)
        ax2.set_title("ATM Count vs Average Queue Length")
        ax2.set_xlabel("Number of ATMs")
        ax2.set_ylabel("Queue Length (Customers)")
        ax2.grid(True, linestyle='--', alpha=0.5)

        ax3.plot(counts, utils, 'd-', color='#10b981', linewidth=2, markersize=8)
        ax3.set_title("ATM Count vs Server Utilization (%)")
        ax3.set_xlabel("Number of ATMs")
        ax3.set_ylabel("Utilization (%)")
        ax3.grid(True, linestyle='--', alpha=0.5)

        plt.tight_layout()
        plt.savefig("experiment_chart.png", dpi=150)
        plt.savefig("results/experiment_chart.png", dpi=150)
        plt.close()
        print("✅ Matplotlib experiment chart generated and saved to: experiment_chart.png")
    except Exception as e:
        print(f"⚠️ Could not save matplotlib chart: {e}")


def export_results_to_csv():
    """Menu Option 5: Export actual simulation & experiment data to CSV files."""
    global latest_simulation_result, latest_experiment_results

    if latest_simulation_result is None:
        print("\n❌ No simulation has been executed yet.")
        return

    os.makedirs("results", exist_ok=True)

    # 1. Export customers.csv
    df_cust = pd.DataFrame(latest_simulation_result.customer_records)
    df_cust.to_csv("results/customers.csv", index=False)
    df_cust.to_csv("customers.csv", index=False)

    # 2. Export atm_statistics.csv
    df_atms = pd.DataFrame(latest_simulation_result.atm_metrics)
    df_atms.to_csv("results/atm_statistics.csv", index=False)
    df_atms.to_csv("atm_statistics.csv", index=False)

    # 3. Export simulation_summary.csv
    summary_dict = latest_simulation_result.to_summary_dict()
    # Flatten littles law
    for k, v in summary_dict.get("littles_law", {}).items():
        summary_dict[f"littles_law_{k}"] = v
    summary_dict.pop("littles_law", None)
    
    df_summary = pd.DataFrame([summary_dict])
    df_summary.to_csv("results/simulation_summary.csv", index=False)
    df_summary.to_csv("simulation_summary.csv", index=False)

    # 4. Export experiment_results.csv
    if latest_experiment_results is not None:
        df_exp = pd.DataFrame(latest_experiment_results)
    else:
        # Run quick experiment if not yet executed
        df_exp = pd.DataFrame(ExperimentRunner.run_experiment_1_atm_count())

    df_exp.to_csv("results/experiment_results.csv", index=False)
    df_exp.to_csv("experiment_results.csv", index=False)

    print("\n✅ Simulation results successfully exported to CSV files:")
    print("  • customers.csv (Detailed customer lifecycle records)")
    print("  • atm_statistics.csv (Individual ATM utilization & busy times)")
    print("  • simulation_summary.csv (Overall system performance summary)")
    print("  • experiment_results.csv (ATM capacity comparison results)")


def main():
    """Main CLI Menu Loop."""
    while True:
        print_banner()
        print("1. Run New Simulation")
        print("2. View Last Simulation Results")
        print("3. View Customer Event Log")
        print("4. Run ATM Comparison Experiment")
        print("5. Export Results to CSV")
        print("6. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            run_new_simulation_menu()
        elif choice == "2":
            view_last_simulation_results()
        elif choice == "3":
            view_customer_event_log()
        elif choice == "4":
            run_atm_comparison_experiment()
        elif choice == "5":
            export_results_to_csv()
        elif choice == "6":
            print("\nExiting ATMFlow Intelligence. Goodbye! 👋\n")
            sys.exit(0)
        else:
            print("❌ Invalid option. Please enter a number between 1 and 6.")


if __name__ == "__main__":
    main()

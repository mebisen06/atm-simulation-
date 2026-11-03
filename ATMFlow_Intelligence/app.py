"""
ATMFlow Intelligence — Streamlit Interactive Operations Dashboard
Course: Solving Problems Using Modelling and Simulation (SPMS • NEC00091)
Team: Meet Bisen | Moully Acharya | Nishita Narwal
"""

import sys
import os
import io
import math
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as shadow_go
import plotly.graph_objects as go
import streamlit as st

# Add parent directory to path to enable local module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.engine import SimulationEngine, SimulationConfig, SimulationResult
from simulation.transactions import TransactionType, TransactionManager
from analytics.metrics import MetricsCalculator
from analytics.queue_theory import MMCQueueModel
from experiments.experiment_runner import ExperimentRunner


# Page Configuration
st.set_page_config(
    page_title="ATMFlow Intelligence — ATM Network Simulation",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main {
        background-color: #090d16;
        color: #f1f5f9;
    }
    .stMetric {
        background-color: #0f172a;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #1e293b;
    }
    .stButton>button {
        background-color: #0284c7;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0369a1;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar Navigation
st.sidebar.title("🏦 ATMFlow Intelligence")
st.sidebar.caption("SPMS Project • NEC00091")

page = st.sidebar.radio(
    "Navigation Menu",
    [
        "Page 1: Project Overview",
        "Page 2: Simulation Control",
        "Page 3: ATM Network Status",
        "Page 4: Queue Analytics",
        "Page 5: Experimentation Lab",
        "Page 6: Mathematical Model",
        "Page 7: Results & CSV Export"
    ]
)

st.sidebar.divider()
st.sidebar.markdown("**Team Details (CSD):**")
st.sidebar.text("• Meet Bisen (BTCD25O1081)")
st.sidebar.text("• Moully Acharya (BTCD25O1084)")
st.sidebar.text("• Nishita Narwal (BTCD25O1088)")


# Helper function to run simulation and cache in session state
def run_and_cache_simulation(num_atms, duration_mins, rate, policy, arrival_proc, seed, patience_val=None):
    config = SimulationConfig(
        random_seed=seed,
        sim_duration_seconds=duration_mins * 60.0,
        num_atms=num_atms,
        arrival_rate_per_min=rate,
        queue_policy_type=policy,
        arrival_process_type=arrival_proc,
        customer_patience_mean=patience_val
    )
    engine = SimulationEngine(config)
    result = engine.run()
    st.session_state["sim_result"] = result
    st.session_state["sim_config"] = config
    return result


# Helper to get current or cached result
def get_current_simulation():
    if "sim_result" not in st.session_state:
        run_and_cache_simulation(3, 120, 1.5, "pooled_fifo", "homogeneous", 42)
    return st.session_state["sim_result"]


# PAGE 1: PROJECT OVERVIEW
if page == "Page 1: Project Overview":
    st.title("ATMFlow Intelligence")
    st.subheader("ATM Transaction and Customer Queue Simulation System")
    st.caption("Course: Solving Problems Using Modelling and Simulation (SPMS • Code: NEC00091) | Branch: Computer Science and Design")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📋 Problem Statement")
        st.info(
            "In automated teller machine (ATM) service centers, customer arrival bursts and varying transaction durations "
            "frequently result in queue buildup, extended customer waiting times, and uneven server utilization. "
            "This project develops an event-driven stochastic simulation platform to model queueing mechanics, "
            "evaluate multi-server ATM configurations, and optimize customer throughput."
        )

        st.markdown("### 🎯 Core Objectives")
        st.markdown("""
        1. **Model Stochastic Customer Arrivals:** Implement Poisson and Non-Homogeneous Poisson Processes ($A \sim \text{Exp}(\lambda)$).
        2. **Simulate Parallel Multi-ATM Operations:** Discrete event simulation of $1$ to $10$ concurrent ATM servers using SimPy.
        3. **Analyze Service Durations:** Empirical Log-Normal distributions for Cash Withdrawal, Cash Deposit, and Balance Enquiry.
        4. **Evaluate Queue Performance:** Track continuous time-weighted queue length ($L_q$), customer waiting times ($W_q$), and utilization ($\rho$).
        5. **Validate with Queueing Theory:** Compare empirical simulation output against closed-form $M/M/c$ Erlang-C equations and Little's Law.
        6. **Conduct Controlled Experiments:** Study the impact of ATM server scaling, arrival intensity, and transaction speeds.
        """)

    with col2:
        st.markdown("### 👥 Project Team")
        st.success("""
        **Branch:** Computer Science & Design
        
        1. **Meet Bisen** — BTCD25O1081
        2. **Moully Acharya** — BTCD25O1084
        3. **Nishita Narwal** — BTCD25O1088
        """)

        st.markdown("### 🛠️ Technology Stack")
        st.code("""
Python 3.10  : Core Simulation & Logic
SimPy        : Discrete Event Engine
NumPy        : Random Distributions & Seeds
Pandas       : Analytics & Data Frames
Plotly       : Interactive Visualizations
Streamlit    : Operations Control Panel
Pytest       : Automated Test Verification
        """, language="yaml")

    st.divider()
    st.markdown("### 🔄 Discrete Event Simulation Journey")
    st.markdown("""
    ```
    [ Customer Arrival ] ──► [ Join Queue (FIFO / Shortest) ] ──► [ ATM Server Claim ] ──► [ Transaction Service ] ──► [ Completion & Departure ]
            │                                                                                     │
            └──────► (If Wait Time > Patience) ──► [ Reneging / Abandonment ]                     └──────► (If Cash Depleted) ──► [ Out of Cash Failure ]
    ```
    """)


# PAGE 2: SIMULATION CONTROL
elif page == "Page 2: Simulation Control":
    st.title("🎛️ Live Simulation Control Room")
    st.caption("Configure simulation parameters and execute the SimPy discrete event engine.")

    with st.sidebar:
        st.subheader("Simulation Controls")
        num_atms = st.slider("Number of ATMs (c)", min_value=1, max_value=10, value=3)
        duration_mins = st.slider("Simulation Duration (Minutes)", min_value=10, max_value=720, value=120, step=10)
        arrival_rate = st.slider("Customer Arrival Rate (λ cust/min)", min_value=0.2, max_value=8.0, value=1.5, step=0.1)
        
        queue_policy = st.selectbox(
            "Queue Policy",
            ["pooled_fifo", "shortest_queue"],
            format_func=lambda x: "Pooled FIFO (Single Serpentine Line)" if x == "pooled_fifo" else "Dedicated Shortest Queue"
        )
        
        arrival_proc = st.selectbox(
            "Arrival Stochastic Process",
            ["homogeneous", "peak_hour", "surge"],
            format_func=lambda x: "Homogeneous Poisson" if x == "homogeneous" else ("Peak Hour Rush (NHPP)" if x == "peak_hour" else "Surge Window Spike")
        )

        patience_enabled = st.checkbox("Enable Customer Reneging (Patience Limit)")
        patience_mean = st.number_input("Mean Customer Patience (seconds)", value=300.0, step=30.0) if patience_enabled else None

        seed = st.number_input("Random Seed", value=42, step=1)

        run_btn = st.button("🚀 Run Simulation", use_container_width=True)

    if run_btn:
        result = run_and_cache_simulation(num_atms, duration_mins, arrival_rate, queue_policy, arrival_proc, seed, patience_mean)
        st.toast("Simulation run completed successfully!", icon="✅")
    else:
        result = get_current_simulation()

    summary = result.to_summary_dict()

    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Arrivals", summary["total_arrived"])
    m2.metric("Completed Transactions", summary["completed"], f"{summary['completion_rate_pct']}% completion")
    m3.metric("Avg Wait Time (Wq)", f"{summary['avg_waiting_time_sec']/60.0:.2f} min", f"{summary['avg_waiting_time_sec']:.1f} sec")
    m4.metric("95th Percentile Wait", f"{summary['p95_waiting_time_sec']/60.0:.2f} min", f"Max: {summary['max_waiting_time_sec']/60.0:.1f} min")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Time-Weighted Lq", f"{summary['time_weighted_queue_length']:.2f} cust")
    m6.metric("Avg ATM Utilization (ρ)", f"{summary['average_atm_utilization']*100.0:.1f}%")
    m7.metric("System Throughput", f"{summary['throughput_per_hour']:.1f} cust/hr")
    m8.metric("Reneged / Abandoned", summary["abandoned"], f"{summary['failed']} out of cash")

    st.divider()

    col_q, col_tx = st.columns([2, 1])

    with col_q:
        st.subheader("📈 Real-Time Queue Length Trajectory Lq(t)")
        df_q = pd.DataFrame(result.queue_history, columns=["Time_Sec", "Queue_Length"])
        df_q["Time_Min"] = df_q["Time_Sec"] / 60.0
        fig_q = px.line(df_q, x="Time_Min", y="Queue_Length", labels={"Time_Min": "Simulation Time (Minutes)", "Queue_Length": "Queue Length (Customers)"},
                        title="Continuous Time-Weighted Queue Length Integral", template="plotly_dark")
        fig_q.update_traces(line_color="#38bdf8", line_width=2)
        st.plotly_chart(fig_q, use_container_width=True)

    with col_tx:
        st.subheader("📊 Transaction Mix Distribution")
        df_cust = pd.DataFrame(result.customer_records)
        if not df_cust.empty:
            tx_counts = df_cust["transaction_type"].value_counts().reset_index()
            tx_counts.columns = ["Transaction", "Count"]
            fig_pie = px.pie(tx_counts, names="Transaction", values="Count", color_discrete_sequence=["#38bdf8", "#818cf8", "#34d399"],
                             template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)


# PAGE 3: ATM NETWORK STATUS
elif page == "Page 3: ATM Network Status":
    st.title("🖥️ ATM Network Operations Center")
    st.caption("Real-time monitoring of individual ATM server units, busy durations, and cash vault balances.")

    result = get_current_simulation()
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Active ATMs", len(result.atm_metrics))
    col_kpi2.metric("Network Utilization", f"{result.average_atm_utilization*100.0:.2f}%")
    col_kpi3.metric("Total Completed", result.completed_customers)

    st.divider()

    cols = st.columns(min(len(result.atm_metrics), 4))
    for idx, atm in enumerate(result.atm_metrics):
        col_idx = idx % 4
        with cols[col_idx]:
            st.subheader(f"📟 {atm['atm_id']}")
            status_color = "🟢" if atm['status'] == "IDLE" else ("🔵" if atm['status'] == "BUSY" else "🔴")
            st.markdown(f"**Status:** {status_color} `{atm['status']}`")
            st.markdown(f"**Served:** `{atm['total_customers_served']}` customers")
            st.markdown(f"**Busy Time:** `{atm['total_busy_time']/60.0:.1f}` mins")
            st.progress(min(1.0, max(0.0, atm['utilization'])))
            st.caption(f"Server Utilization: **{atm['utilization']*100.0:.2f}%**")
            st.markdown(f"**Cash Vault Balance:** `₹{atm['cash_balance']:,.0f}`")

    st.divider()
    st.subheader("📋 Detailed Server Metrics Table")
    df_atms = pd.DataFrame(result.atm_metrics)
    df_atms["utilization_pct"] = (df_atms["utilization"] * 100.0).round(2)
    df_atms["busy_minutes"] = (df_atms["total_busy_time"] / 60.0).round(2)
    st.dataframe(
        df_atms[["atm_id", "status", "total_customers_served", "busy_minutes", "utilization_pct", "cash_balance"]],
        use_container_width=True
    )


# PAGE 4: QUEUE ANALYTICS
elif page == "Page 4: Queue Analytics":
    st.title("📊 Customer & Queue Performance Analytics")
    st.caption("Statistical distributions of waiting times, system duration, and arrival frequencies.")

    result = get_current_simulation()
    df_cust = pd.DataFrame(result.customer_records)

    if not df_cust.empty:
        df_completed = df_cust[df_cust["status"] == "COMPLETED"].copy()
        df_completed["waiting_min"] = df_completed["waiting_time"] / 60.0
        df_completed["system_min"] = df_completed["system_time"] / 60.0

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("⏱️ Customer Waiting Time Histogram Wq")
            fig_hist = px.histogram(
                df_completed, x="waiting_min", nbins=25,
                labels={"waiting_min": "Waiting Time (Minutes)"},
                title="Distribution of Queue Wait Times Wq",
                color_discrete_sequence=["#f59e0b"], template="plotly_dark"
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with c2:
            st.subheader("⏳ Arrival Cumulative Curve over Horizon")
            df_cust["arrival_min"] = df_cust["arrival_time"] / 60.0
            df_cust["cumulative_arrivals"] = range(1, len(df_cust) + 1)
            fig_arr = px.line(
                df_cust, x="arrival_min", y="cumulative_arrivals",
                labels={"arrival_min": "Arrival Time (Minutes)", "cumulative_arrivals": "Cumulative Customers"},
                title="Customer Arrival Progression over Time",
                color_discrete_sequence=["#10b981"], template="plotly_dark"
            )
            st.plotly_chart(fig_arr, use_container_width=True)

        c3, c4 = st.columns(2)

        with c3:
            st.subheader("📉 Waiting Time Percentiles")
            perc = np.percentile(df_completed["waiting_min"], [50, 75, 90, 95, 99]) if not df_completed.empty else [0]*5
            df_perc = pd.DataFrame({
                "Percentile": ["50th (Median)", "75th Percentile", "90th Percentile", "95th Percentile", "99th Percentile"],
                "Wait_Time_Minutes": [round(p, 2) for p in perc]
            })
            st.table(df_perc)

        with c4:
            st.subheader("⏱️ Waiting Time by Transaction Category")
            fig_box = px.box(
                df_completed, x="transaction_type", y="waiting_min",
                color="transaction_type",
                labels={"transaction_type": "Transaction", "waiting_min": "Wait Time (Min)"},
                title="Queue Wait Time Boxplot per Transaction",
                template="plotly_dark"
            )
            st.plotly_chart(fig_box, use_container_width=True)


# PAGE 5: EXPERIMENTATION LAB
elif page == "Page 5: Experimentation Lab":
    st.title("🔬 Scenario Experimentation Lab")
    st.caption("Execute systematic multi-run comparative experiments.")

    exp_choice = st.selectbox(
        "Select Experiment",
        [
            "Experiment 1: Effect of ATM Server Count (1 to 5 ATMs)",
            "Experiment 2: Effect of Customer Arrival Intensity (Low / Med / High / Surge)",
            "Experiment 3: Effect of Transaction Service Speed (Fast / Std / Slow)"
        ]
    )

    if "Exp 1" in exp_choice:
        st.subheader("Experiment 1: ATM Server Scaling Analysis")
        st.markdown("Evaluates how increasing ATM count reduces waiting time and queue length.")
        
        if st.button("▶️ Run Experiment 1"):
            with st.spinner("Executing simulation runs across 1, 2, 3, 4, 5 ATMs..."):
                exp1_data = ExperimentRunner.run_experiment_1_atm_count()
                st.session_state["exp1_data"] = exp1_data

        if "exp1_data" in st.session_state:
            df_exp1 = pd.DataFrame(st.session_state["exp1_data"])
            st.dataframe(df_exp1, use_container_width=True)

            c1, c2 = st.columns(2)
            with c1:
                fig1 = px.bar(df_exp1, x="atm_count", y="avg_waiting_time_min", text="avg_waiting_time_min",
                              labels={"atm_count": "Number of ATMs", "avg_waiting_time_min": "Avg Wait Time (Min)"},
                              title="ATM Count vs Average Waiting Time (Wq)", template="plotly_dark", color_discrete_sequence=["#38bdf8"])
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                fig2 = px.line(df_exp1, x="atm_count", y="avg_atm_utilization_pct", markers=True,
                               labels={"atm_count": "Number of ATMs", "avg_atm_utilization_pct": "Server Utilization (%)"},
                               title="ATM Count vs Server Utilization (ρ)", template="plotly_dark", color_discrete_sequence=["#34d399"])
                st.plotly_chart(fig2, use_container_width=True)

    elif "Exp 2" in exp_choice:
        st.subheader("Experiment 2: Traffic Arrival Intensity Impact")
        st.markdown("Evaluates system performance across Low (0.5), Medium (1.5), High (3.0), and Surge (4.5) traffic.")

        if st.button("▶️ Run Experiment 2"):
            with st.spinner("Executing traffic intensity experiments..."):
                exp2_data = ExperimentRunner.run_experiment_2_arrival_rate()
                st.session_state["exp2_data"] = exp2_data

        if "exp2_data" in st.session_state:
            df_exp2 = pd.DataFrame(st.session_state["exp2_data"])
            st.dataframe(df_exp2, use_container_width=True)

            fig3 = px.bar(df_exp2, x="scenario_name", y="avg_waiting_time_min", color="avg_atm_utilization_pct",
                          labels={"scenario_name": "Traffic Scenario", "avg_waiting_time_min": "Avg Wait Time (Min)"},
                          title="Arrival Intensity vs Queue Wait Time", template="plotly_dark")
            st.plotly_chart(fig3, use_container_width=True)

    elif "Exp 3" in exp_choice:
        st.subheader("Experiment 3: Transaction Service Speed Analysis")
        st.markdown("Evaluates impact of fast, standard, and slow service durations on network throughput.")

        if st.button("▶️ Run Experiment 3"):
            with st.spinner("Executing service speed experiments..."):
                exp3_data = ExperimentRunner.run_experiment_3_service_time()
                st.session_state["exp3_data"] = exp3_data

        if "exp3_data" in st.session_state:
            df_exp3 = pd.DataFrame(st.session_state["exp3_data"])
            st.dataframe(df_exp3, use_container_width=True)

            fig4 = px.bar(df_exp3, x="service_scenario", y="throughput_per_hr", text="throughput_per_hr",
                          title="Service Speed vs System Throughput (cust/hr)", template="plotly_dark", color_discrete_sequence=["#a855f7"])
            st.plotly_chart(fig4, use_container_width=True)


# PAGE 6: MATHEMATICAL MODEL
elif page == "Page 6: Mathematical Model":
    st.title("📐 Queueing Theory & Mathematical Model")
    st.caption("Analytical closed-form derivations vs empirical simulation results.")

    result = get_current_simulation()
    config = result.config

    st.markdown("### 1. Fundamental Governing Equations")
    st.latex(r"A \sim \text{Exponential}(\lambda) \implies f_A(t) = \lambda e^{-\lambda t}")
    st.latex(r"\rho = \frac{\lambda}{c \cdot \mu} \quad (\text{Server Utilization for } c \text{ parallel ATMs})")
    st.latex(r"L_q = \lambda_{\text{effective}} \cdot W_q \quad (\text{Little's Law for Queue Occupancy})")

    st.divider()

    st.markdown("### 2. Analytical M/M/c Model Comparison")
    
    # Calculate M/M/c analytical metrics
    # Average service time in min
    avg_s_min = result.average_service_time_sec / 60.0 if result.average_service_time_sec > 0 else 1.83
    mu_per_min = 1.0 / avg_s_min if avg_s_min > 0 else 0.54
    
    mmc_theo = MMCQueueModel.calculate(
        arrival_rate_lambda=config.arrival_rate_per_min,
        service_rate_mu=mu_per_min,
        num_servers_c=config.num_atms
    )

    theo_dict = mmc_theo.to_dict()

    comp_df = pd.DataFrame({
        "Performance Metric": [
            "Server Utilization (ρ)",
            "Avg Queue Length (Lq)",
            "Avg Waiting Time in Queue (Wq min)",
            "Effective Arrival Rate (λ/min)"
        ],
        "Theoretical M/M/c Formula": [
            f"{theo_dict['server_utilization_rho']*100:.2f}%",
            f"{theo_dict['avg_queue_length_lq']:.3f} cust",
            f"{theo_dict['avg_waiting_time_wq']:.2f} min",
            f"{config.arrival_rate_per_min:.2f} cust/min"
        ],
        "Empirical SimPy Simulation": [
            f"{result.average_atm_utilization*100:.2f}%",
            f"{result.time_weighted_queue_length:.3f} cust",
            f"{result.average_waiting_time_sec/60.0:.2f} min",
            f"{result.littles_law_verification['lambda_effective_per_sec']*60.0:.2f} cust/min"
        ]
    })

    st.table(comp_df)

    if not theo_dict["is_stable"]:
        st.warning("⚠️ Theoretical system is unstable (ρ >= 1.0). Arrival rate exceeds total ATM capacity!")
    else:
        st.success(f"✅ System in steady state equilibrium. Probability an arriving customer finds no queue (P0) = {theo_dict['p0_prob_zero_cust']*100:.2f}%")


# PAGE 7: RESULTS & CSV EXPORT
elif page == "Page 7: Results & CSV Export":
    st.title("📁 Simulation Reports & Data Export")
    st.caption("Inspect full customer lifecycle records and download dataset CSVs.")

    result = get_current_simulation()
    df_cust = pd.DataFrame(result.customer_records)

    st.subheader("📄 Complete Customer Transaction Trace")
    st.dataframe(df_cust, use_container_width=True)

    csv_buffer = io.StringIO()
    df_cust.to_csv(csv_buffer, index=False)
    
    st.download_button(
        label="📥 Download Customer Records CSV",
        data=csv_buffer.getvalue(),
        file_name="atm_simulation_customer_records.csv",
        mime="text/csv"
    )

    st.divider()

    st.subheader("📜 Event Log Timeline")
    df_events = pd.DataFrame(result.events_log)
    st.dataframe(df_events, use_container_width=True)

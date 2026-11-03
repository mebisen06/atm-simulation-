# ATMFlow Intelligence: Advanced ATM Network Simulation, Queue Optimization and Decision Support System

**Course:** Solving Problems Using Modelling and Simulation (SPMS) — Course Code: NEC00091  
**Branch:** Computer Science and Design  
**Project Team:**
- **Meet Bisen** — BTCD25O1081
- **Moully Acharya** — BTCD25O1084
- **Nishita Narwal** — BTCD25O1088

---

## 1. Project Overview & Milestone 1 Architecture

ATMFlow Intelligence is an engineering simulation platform designed to model, analyze, and optimize multi-server ATM queueing networks under stochastic conditions. Built on Python and SimPy, it tracks the end-to-end discrete-event customer journey:

$$\text{Arrival} \longrightarrow \text{ATM / Queue Selection} \longrightarrow \text{Queue Formation} \longrightarrow \text{ATM Allocation} \longrightarrow \text{Transaction Processing} \longrightarrow \text{Completion / Abandonment}$$

---

## 2. Mathematical Modelling Foundations

### 2.1 Customer Arrival Stochastic Process
1. **Homogeneous Poisson Process:**
   Customer inter-arrival times $A_k \sim \text{Exponential}(\lambda)$, where $\lambda$ is arrival intensity:
   $$f_A(t) = \lambda e^{-\lambda t}, \quad t \ge 0, \quad E[A] = \frac{1}{\lambda}$$
2. **Non-Homogeneous Poisson Process (NHPP):**
   Time-varying arrival intensity $\lambda(t)$ using the Lewis-Shedler thinning algorithm:
   $$\lambda(t) = \lambda_{\text{base}} + (\lambda_{\text{peak}} - \lambda_{\text{base}}) \cdot \exp\left(-\frac{1}{2}\left(\frac{t - t_{\text{mid}}}{\sigma}\right)^2\right)$$
3. **Random Arrival Surges:**
   Abrupt step-function jump in arrival intensity during designated rush periods.

### 2.2 Transaction Service Time Distributions
Transactions are categorized with empirical and right-skewed positive distributions:
- **Cash Withdrawal:** Log-Normal($\mu=110\text{s}, \sigma=35\text{s}$)
- **Cash Deposit:** Log-Normal($\mu=170\text{s}, \sigma=50\text{s}$)
- **Balance Enquiry:** Log-Normal($\mu=45\text{s}, \sigma=15\text{s}$)

Log-normal conversion formulas from mean $m$ and variance $v$:
$$\mu_{\ln} = \ln\left(\frac{m^2}{\sqrt{v + m^2}}\right), \quad \sigma_{\ln} = \sqrt{\ln\left(1 + \frac{v}{m^2}\right)}$$

### 2.3 Queueing Theory & Little's Law Validation
For any stationary or ergodic queueing system in equilibrium:
$$L_q = \lambda_{\text{effective}} \cdot W_q$$
$$L = \lambda_{\text{effective}} \cdot W = \lambda_{\text{effective}} \cdot (W_q + E[S])$$

Where:
- $W_q$: Average customer waiting time in queue.
- $\bar{L}_q$: Time-weighted average queue length computed via continuous integral:
  $$\bar{L}_q = \frac{1}{T} \int_0^T L_q(t) \, dt = \frac{1}{T} \sum_{i} L_{q, i} \cdot \Delta t_i$$
- $\rho$: Server utilization for $c$ parallel ATMs:
  $$\rho = \frac{\sum_{k=1}^c T_{\text{busy}, k}}{c \cdot T_{\text{total}}}$$

---

## 3. Directory Structure

```
ATMFlow_Intelligence/
├── requirements.txt
├── README.md
├── run_simulation.py
│
├── simulation/
│   ├── __init__.py
│   ├── customer.py        # Customer entity & timestamp tracking
│   ├── transactions.py    # Transaction profiles & stochastic service times
│   ├── arrivals.py        # Poisson, NHPP, and Surge arrival generators
│   ├── atm.py             # ATM unit resource & state machine
│   ├── queue_manager.py   # Pooled FIFO & Shortest Queue scheduling
│   └── engine.py          # SimPy Discrete Event Simulation Engine
│
├── analytics/
│   ├── __init__.py
│   └── metrics.py         # Metrics calculation & ASCII summary formatting
│
├── data/
│   └── simulation_results.json
│
└── tests/
    ├── __init__.py
    └── test_milestone1.py # Comprehensive unit & integration verification
```

---

## 4. How to Run & Verify

### Prerequisites
- Python 3.10+
- SimPy 4.1+, NumPy 1.24+, Pandas 2.0+, SciPy 1.10+

### Installation
```bash
cd ATMFlow_Intelligence
pip install -r requirements.txt
```

### Running the Test Suite
```bash
python3 tests/test_milestone1.py
```
Expected output: 7 passed tests (`OK`) verifying:
1. Reproducibility with random seeds
2. Customer conservation
3. Timing non-negativity
4. ATM utilization bounds $[0, 1]$
5. Dedicated shortest queue policy
6. Customer abandonment / reneging
7. Little's Law theoretical alignment

### Running a Simulation Experiment
```bash
python3 run_simulation.py --atms 3 --duration 7200 --rate 1.5 --seed 42 --policy pooled_fifo
```

---

## 5. Milestone Progression Tracking

- [x] **Milestone 1:** Architecture, mathematical formulations, and core discrete-event simulation engine with full unit tests.
- [ ] **Milestone 2:** Multi-ATM network and queue management.
- [ ] **Milestone 3:** Arrival and service-time distributions.
- [ ] **Milestone 4:** ATM failure and reliability modelling.
- [ ] **Milestone 5:** Cash inventory and replenishment.
- [ ] **Milestone 6:** Advanced queue allocation policies.
- [ ] **Milestone 7:** Queueing theory and statistical analytics.
- [ ] **Milestone 8:** Monte Carlo experimentation.
- [ ] **Milestone 9:** ATM network optimization.
- [ ] **Milestone 10:** Professional Streamlit / Web dashboard.
- [ ] **Milestone 11:** Integration, testing, and validation.
- [ ] **Milestone 12:** Documentation, reports, and final presentation.

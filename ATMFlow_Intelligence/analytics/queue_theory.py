"""
Queueing Theory Analytical Calculator (M/M/c Model)
ATMFlow Intelligence - SPMS Course (NEC00091)
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class MMCTheoreticalResult:
    arrival_rate_lambda: float     # λ (cust/min or cust/sec)
    service_rate_mu: float         # μ per server (cust/min or cust/sec)
    num_servers_c: int             # c (number of ATMs)
    traffic_intensity_r: float     # r = λ / μ
    server_utilization_rho: float  # ρ = λ / (c * μ)
    is_stable: bool                # True if ρ < 1
    p0_prob_zero_cust: float       # P0
    pw_erlang_c_wait_prob: float   # Pw (probability an arriving customer must wait)
    avg_queue_length_lq: float     # Lq
    avg_waiting_time_wq: float     # Wq
    avg_system_time_w: float       # W = Wq + 1/μ
    avg_system_cust_l: float       # L = Lq + r

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arrival_rate_lambda": round(self.arrival_rate_lambda, 4),
            "service_rate_mu": round(self.service_rate_mu, 4),
            "num_servers_c": self.num_servers_c,
            "traffic_intensity_r": round(self.traffic_intensity_r, 4),
            "server_utilization_rho": round(self.server_utilization_rho, 4),
            "is_stable": self.is_stable,
            "p0_prob_zero_cust": round(self.p0_prob_zero_cust, 6),
            "pw_erlang_c_wait_prob": round(self.pw_erlang_c_wait_prob, 4),
            "avg_queue_length_lq": round(self.avg_queue_length_lq, 3),
            "avg_waiting_time_wq": round(self.avg_waiting_time_wq, 2),
            "avg_system_time_w": round(self.avg_system_time_w, 2),
            "avg_system_cust_l": round(self.avg_system_cust_l, 3),
        }


class MMCQueueModel:
    """
    Analytical M/M/c Queueing Model Calculator.
    Computes closed-form steady-state queue performance metrics using Erlang-C equation.
    """

    @staticmethod
    def calculate(
        arrival_rate_lambda: float,
        service_rate_mu: float,
        num_servers_c: int
    ) -> MMCTheoreticalResult:
        """
        Calculates theoretical performance metrics for M/M/c queueing system.
        
        :param arrival_rate_lambda: Arrival rate λ (customers per unit time)
        :param service_rate_mu: Service rate μ per ATM (customers per unit time)
        :param num_servers_c: Number of parallel ATMs c
        """
        if arrival_rate_lambda <= 0 or service_rate_mu <= 0 or num_servers_c < 1:
            raise ValueError("Parameters must be strictly positive integers/floats.")

        r = arrival_rate_lambda / service_rate_mu
        rho = r / num_servers_c
        is_stable = rho < 1.0

        if not is_stable:
            # Unstable queueing system (arrival rate exceeds server capacity)
            return MMCTheoreticalResult(
                arrival_rate_lambda=arrival_rate_lambda,
                service_rate_mu=service_rate_mu,
                num_servers_c=num_servers_c,
                traffic_intensity_r=r,
                server_utilization_rho=rho,
                is_stable=False,
                p0_prob_zero_cust=0.0,
                pw_erlang_c_wait_prob=1.0,
                avg_queue_length_lq=float("inf"),
                avg_waiting_time_wq=float("inf"),
                avg_system_time_w=float("inf"),
                avg_system_cust_l=float("inf"),
            )

        # Compute P0: Probability of zero customers in the system
        # P0 = [ sum_{n=0}^{c-1} (r^n / n!) + (r^c / c!) * (1 / (1 - rho)) ]^-1
        sum_terms = sum((r ** n) / math.factorial(n) for n in range(num_servers_c))
        c_term = (r ** num_servers_c) / (math.factorial(num_servers_c) * (1.0 - rho))
        p0 = 1.0 / (sum_terms + c_term)

        # Erlang-C Waiting Probability Pw:
        # Pw = [ (r^c / c!) * (1 / (1 - rho)) ] * P0
        pw = c_term * p0

        # Average Queue Length Lq:
        # Lq = Pw * rho / (1 - rho)
        lq = (pw * rho) / (1.0 - rho)

        # Average Waiting Time in Queue Wq (Little's Law: Wq = Lq / λ):
        wq = lq / arrival_rate_lambda

        # Average System Duration W = Wq + 1/μ:
        w = wq + (1.0 / service_rate_mu)

        # Average Total Customers in System L (Little's Law: L = λ * W):
        l = arrival_rate_lambda * w

        return MMCTheoreticalResult(
            arrival_rate_lambda=arrival_rate_lambda,
            service_rate_mu=service_rate_mu,
            num_servers_c=num_servers_c,
            traffic_intensity_r=r,
            server_utilization_rho=rho,
            is_stable=True,
            p0_prob_zero_cust=p0,
            pw_erlang_c_wait_prob=pw,
            avg_queue_length_lq=lq,
            avg_waiting_time_wq=wq,
            avg_system_time_w=w,
            avg_system_cust_l=l,
        )

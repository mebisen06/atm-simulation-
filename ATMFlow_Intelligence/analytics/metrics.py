"""
Statistical and Performance Metrics Calculator.
SPMS Course: Solving Problems Using Modelling and Simulation (NEC00091)
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


class MetricsCalculator:
    """Calculates comprehensive queueing and operational metrics from raw simulation records."""

    @staticmethod
    def compute_percentiles(values: List[float], percentiles=(50, 75, 90, 95, 99)) -> Dict[str, float]:
        if not values:
            return {f"p{p}": 0.0 for p in percentiles}
        arr = np.array(values)
        return {f"p{p}": round(float(np.percentile(arr, p)), 2) for p in percentiles}

    @staticmethod
    def build_customer_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Converts raw customer records into a Pandas DataFrame."""
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)

    @staticmethod
    def format_ascii_table(title: str, rows: List[tuple]) -> str:
        """Formats clean terminal ASCII tables for simulation reports."""
        header = f"\n=== {title} ==="
        divider = "-" * 55
        lines = [header, divider]
        for key, val in rows:
            lines.append(f"{key:<35}: {str(val):>16}")
        lines.append(divider)
        return "\n".join(lines)

"""
Ranking Table Component

Visualization component for model ranking based on robustness metrics.
Displays rankings sorted by adversarial robustness and vulnerability index.
"""

import logging
from typing import Any, List, Optional

from dashboard.schemas import BenchmarkComparisonData, BenchmarkModelResult
from dashboard.utils import format_score, log_dashboard_event

logger = logging.getLogger(__name__)


# Table headers for ranking display
RANKING_HEADERS = [
    "Rank",
    "Model",
    "R_base",
    "R_adv",
    "ΔR",
    "RSI",
    "VI",
    "Samples",
]


def create_ranking_table(
    comparison: Optional[BenchmarkComparisonData],
) -> List[List[str]]:
    """
    Create ranking table from benchmark comparison data.
    
    Ranking rules:
    - Primary: Sort by R_adv (descending)
    - Secondary: Sort by VI (ascending - lower is better)
    
    Args:
        comparison: BenchmarkComparisonData object
        
    Returns:
        Table data as list of rows
    """
    if comparison is None or not comparison.model_results:
        return [create_empty_row()]
    
    log_dashboard_event(
        "DASHBOARD_VIEW_RANKING_TABLE",
        benchmark_id=comparison.benchmark_id,
    )
    
    return update_ranking_table(comparison)


def update_ranking_table(
    comparison: BenchmarkComparisonData,
) -> List[List[str]]:
    """
    Update ranking table with benchmark comparison data.
    
    Args:
        comparison: BenchmarkComparisonData object
        
    Returns:
        Table data as list of rows
    """
    if not comparison.model_results:
        return [create_empty_row()]
    
    # Results are already sorted by the schema
    # Primary: R_adv descending
    # Secondary: VI ascending
    table_data = []
    
    for result in comparison.model_results:
        row = [
            str(result.rank),
            result.model_name,
            format_score(result.baseline_robustness, 4),
            format_score(result.adversarial_robustness, 4),
            format_score(result.delta_robustness, 4),
            format_score(result.rsi, 4),
            format_score(result.vulnerability_index, 4),
            str(result.sample_count),
        ]
        table_data.append(row)
    
    return table_data


def create_ranking_table_from_results(
    results: List[BenchmarkModelResult],
) -> List[List[str]]:
    """
    Create ranking table from list of model results.
    
    Args:
        results: List of BenchmarkModelResult objects
        
    Returns:
        Table data as list of rows
    """
    if not results:
        return [create_empty_row()]
    
    # Sort by R_adv descending, then VI ascending
    sorted_results = sorted(
        results,
        key=lambda x: (x.adversarial_robustness, -x.vulnerability_index),
        reverse=True,
    )
    
    # Assign ranks
    for i, result in enumerate(sorted_results):
        result.rank = i + 1
    
    table_data = []
    for result in sorted_results:
        row = [
            str(result.rank),
            result.model_name,
            format_score(result.baseline_robustness, 4),
            format_score(result.adversarial_robustness, 4),
            format_score(result.delta_robustness, 4),
            format_score(result.rsi, 4),
            format_score(result.vulnerability_index, 4),
            str(result.sample_count),
        ]
        table_data.append(row)
    
    return table_data


def create_empty_row() -> List[str]:
    """
    Create empty row for table.
    
    Returns:
        List of default values
    """
    return ["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "0"]


def get_ranking_headers() -> List[str]:
    """
    Get ranking table headers.
    
    Returns:
        List of header strings
    """
    return RANKING_HEADERS


def format_ranking_tooltip(result: BenchmarkModelResult) -> str:
    """
    Format ranking tooltip for a model result.
    
    Args:
        result: BenchmarkModelResult object
        
    Returns:
        Formatted tooltip string
    """
    return (
        f"<b>{result.model_name}</b><br>"
        f"Rank: #{result.rank}<br>"
        f"R_base: {result.baseline_robustness:.4f}<br>"
        f"R_adv: {result.adversarial_robustness:.4f}<br>"
        f"ΔR: {result.delta_robustness:.4f}<br>"
        f"RSI: {result.rsi:.4f}<br>"
        f"VI: {result.vulnerability_index:.4f}<br>"
        f"Samples: {result.sample_count}"
    )


def get_rsi_interpretation(rsi: float) -> str:
    """
    Get interpretation string for RSI value.
    
    Args:
        rsi: RSI value
        
    Returns:
        Interpretation string
    """
    if rsi >= 0.9:
        return "Very Stable"
    elif rsi >= 0.7:
        return "Moderately Stable"
    elif rsi >= 0.5:
        return "Unstable"
    else:
        return "Highly Unstable"


def get_vi_interpretation(vi: float) -> str:
    """
    Get interpretation string for VI value.
    
    Args:
        vi: VI value
        
    Returns:
        Interpretation string
    """
    if vi < 0.1:
        return "Highly Resilient"
    elif vi < 0.3:
        return "Moderately Resilient"
    elif vi < 0.5:
        return "Vulnerable"
    else:
        return "Highly Vulnerable"


def get_delta_interpretation(delta: float) -> str:
    """
    Get interpretation string for delta robustness value.
    
    Args:
        delta: Delta robustness value
        
    Returns:
        Interpretation string
    """
    if delta < 0.0:
        return "Better Under Attack"
    elif delta < 0.1:
        return "Highly Robust"
    elif delta < 0.3:
        return "Moderately Robust"
    elif delta < 0.5:
        return "Vulnerable"
    else:
        return "Severely Vulnerable"

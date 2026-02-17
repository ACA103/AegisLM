"""
Comparison Table Component

Gradio component for displaying model comparison tables.
"""

import logging
from typing import Any, List, Optional, Tuple

import gradio as gr
import plotly.graph_objects as go

from dashboard.schemas import ComparisonData, DeltaRobustnessData
from dashboard.utils import format_score, log_dashboard_event

logger = logging.getLogger(__name__)


def create_comparison_table() -> Tuple[gr.DataFrame, gr.Plot]:
    """
    Create comparison table component.
    
    Returns:
        Tuple of (table, plot) components
    """
    
    # Comparison table
    table = gr.DataFrame(
        headers=[
            "Model",
            "Hallucination",
            "Toxicity",
            "Bias",
            "Confidence",
            "Composite Score",
            "Sample Count",
        ],
        label="Model Comparison",
        interactive=False,
    )
    
    # Delta chart
    delta_plot = gr.Plot(
        label="Delta Robustness",
    )
    
    return table, delta_plot


def update_comparison_table(
    comparison_data: Optional[ComparisonData],
) -> List[List[str]]:
    """
    Update comparison table with data.
    
    Args:
        comparison_data: Comparison data
        
    Returns:
        Table data as list of rows
    """
    if comparison_data is None or not comparison_data.models:
        return [["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "0"]]
    
    table_data = []
    for i, model in enumerate(comparison_data.models):
        table_data.append([
            model,
            format_score(comparison_data.hallucination[i], 4),
            format_score(comparison_data.toxicity[i], 4),
            format_score(comparison_data.bias[i], 4),
            format_score(comparison_data.confidence[i], 4),
            format_score(comparison_data.composite_score[i], 4),
            str(comparison_data.sample_count[i]),
        ])
    
    return table_data


def update_delta_chart(
    delta_data: List[DeltaRobustnessData],
) -> Any:
    """
    Update delta chart with data.
    
    Args:
        delta_data: List of delta robustness data
        
    Returns:
        Plotly figure
    """
    if not delta_data:
        # Return empty chart
        fig = go.Figure()
        fig.update_layout(
            title="No Data Available",
            xaxis=dict(title="Model"),
            yaxis=dict(title="Delta Robustness"),
        )
        return fig
    
    log_dashboard_event("DASHBOARD_COMPARE_MODELS")
    
    models = [d.model_name for d in delta_data]
    deltas = [d.delta_robustness for d in delta_data]
    composites = [d.composite_score for d in delta_data]
    
    # Color based on delta (green for positive, red for negative)
    colors = ["#22c55e" if d >= 0 else "#ef4444" for d in deltas]
    
    fig = go.Figure(
        data=go.Bar(
            x=models,
            y=deltas,
            marker_color=colors,
            text=[f"Δ={c:.3f}" for c in composites],
            textposition="auto",
        )
    )
    
    fig.update_layout(
        title="Delta Robustness Comparison",
        xaxis=dict(title="Model"),
        yaxis=dict(
            title="Delta Robustness",
            range=[min(min(deltas) - 0.1, -0.1), max(max(deltas) + 0.1, 0.1)],
        ),
        height=400,
        width=600,
    )
    
    return fig


def create_ranking_table(
    delta_data: List[DeltaRobustnessData],
) -> List[List[str]]:
    """
    Create ranking table from delta data.
    
    Args:
        delta_data: List of delta robustness data
        
    Returns:
        Table data as list of rows
    """
    if not delta_data:
        return [["N/A", "N/A", "N/A", "N/A"]]
    
    # Sort by composite score descending
    sorted_data = sorted(delta_data, key=lambda x: x.composite_score, reverse=True)
    
    table_data = []
    for rank, data in enumerate(sorted_data, 1):
        table_data.append([
            str(rank),
            data.model_name,
            format_score(data.composite_score, 4),
            format_score(data.delta_robustness, 4),
        ])
    
    return table_data


class ComparisonTable:
    """
    Comparison table component with state management.
    """
    
    def __init__(self):
        """Initialize comparison table."""
        self._comparison_data: Optional[ComparisonData] = None
        self._delta_data: List[DeltaRobustnessData] = []
    
    def set_comparison_data(self, data: ComparisonData) -> None:
        """
        Set comparison data.
        
        Args:
            data: Comparison data
        """
        self._comparison_data = data
    
    def set_delta_data(self, data: List[DeltaRobustnessData]) -> None:
        """
        Set delta data.
        
        Args:
            data: List of delta robustness data
        """
        self._delta_data = data
    
    def get_comparison_data(self) -> Optional[ComparisonData]:
        """
        Get comparison data.
        
        Returns:
            Comparison data or None
        """
        return self._comparison_data
    
    def get_delta_data(self) -> List[DeltaRobustnessData]:
        """
        Get delta data.
        
        Returns:
            List of delta robustness data
        """
        return self._delta_data
    
    def get_table_data(self) -> List[List[str]]:
        """
        Get table data for display.
        
        Returns:
            Table data as list of rows
        """
        return update_comparison_table(self._comparison_data)
    
    def get_delta_figure(self) -> Any:
        """
        Get delta chart figure.
        
        Returns:
            Plotly figure
        """
        return update_delta_chart(self._delta_data)


def create_model_selector_multi() -> gr.Component:
    """
    Create multi-select model selector.
    
    Returns:
        Gradio multi-select component
    """
    selector = gr.Dropdown(
        label="Select Models to Compare",
        choices=[],
        interactive=True,
        multiselect=True,
    )
    
    return selector


def create_benchmark_comparison(
    benchmark_runs: List[dict],
) -> gr.DataFrame:
    """
    Create benchmark comparison table.
    
    Args:
        benchmark_runs: List of benchmark run data
        
    Returns:
        DataFrame component
    """
    headers = ["Benchmark", "Model", "Score", "Status", "Date"]
    
    table_data = []
    for run in benchmark_runs:
        table_data.append([
            run.get("benchmark_name", "N/A"),
            run.get("model_name", "N/A"),
            format_score(run.get("composite_score"), 4),
            run.get("status", "N/A"),
            run.get("timestamp", "N/A")[:10],
        ])
    
    table = gr.DataFrame(
        headers=headers,
        value=table_data if table_data else [["N/A"] * len(headers)],
        label="Benchmark Comparison",
        interactive=False,
    )
    
    return table

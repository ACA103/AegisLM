"""
Delta Bar Chart Component

Visualization component for delta robustness comparison between models.
Displays delta robustness (ΔR) with color scale indicating robustness level.
"""

import logging
from typing import Any, List, Optional

import plotly.graph_objects as go

from dashboard.schemas import BenchmarkComparisonData, BenchmarkModelResult
from dashboard.utils import format_score, log_dashboard_event

logger = logging.getLogger(__name__)


def create_delta_bar_chart(
    comparison: Optional[BenchmarkComparisonData],
) -> Any:
    """
    Create delta robustness bar chart from benchmark comparison data.
    
    Args:
        comparison: BenchmarkComparisonData object
        
    Returns:
        Plotly figure
    """
    if comparison is None or not comparison.model_results:
        return create_empty_delta_chart("No benchmark data available")
    
    log_dashboard_event(
        "DASHBOARD_VIEW_DELTA_CHART",
        benchmark_id=comparison.benchmark_id,
    )
    
    return update_delta_bar_chart(comparison)


def update_delta_bar_chart(
    comparison: BenchmarkComparisonData,
) -> Any:
    """
    Update delta bar chart with benchmark comparison data.
    
    Color scale:
    - Green → low delta (robust)
    - Red → high delta (fragile)
    
    Args:
        comparison: BenchmarkComparisonData object
        
    Returns:
        Plotly figure
    """
    if not comparison.model_results:
        return create_empty_delta_chart("No model results")
    
    # Extract data
    models = [r.model_name for r in comparison.model_results]
    deltas = [r.delta_robustness for r in comparison.model_results]
    
    # Color scale based on delta (green for low, red for high)
    # Delta range: -1 to 1
    # Lower delta = more degradation = red
    # Higher delta = less degradation = green
    colors = []
    for delta in deltas:
        # Normalize delta to [0, 1] for color mapping
        # delta = -1 (worst) -> red
        # delta = 0 (neutral) -> yellow
        # delta = 1 (best) -> green
        normalized = (delta + 1) / 2  # Maps -1 to 1 to 0 to 1
        
        if normalized < 0.33:
            # Low (close to -1) - red
            colors.append("#ef4444")  # Red
        elif normalized < 0.66:
            # Medium - yellow
            colors.append("#eab308")  # Yellow
        else:
            # High (close to 1) - green
            colors.append("#22c55e")  # Green
    
    # Create bar chart
    fig = go.Figure(
        data=go.Bar(
            x=models,
            y=deltas,
            marker_color=colors,
            text=[f"ΔR={d:.3f}" for d in deltas],
            textposition="auto",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Delta Robustness: %{y:.4f}<br>"
                "<extra></extra>"
            ),
        )
    )
    
    # Layout
    fig.update_layout(
        title={
            "text": f"Delta Robustness Comparison - {comparison.benchmark_name}",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(
            title="Model",
            tickangle=-45,
        ),
        yaxis=dict(
            title="ΔR (Baseline - Adversarial)",
            range=[0, 1],  # Fixed range as per requirements
            tickformat=".2f",
        ),
        height=400,
        width=700,
        margin=dict(b=80),
    )
    
    # Add reference line at y=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig


def create_empty_delta_chart(message: str = "Select a benchmark") -> Any:
    """
    Create empty delta chart with message.
    
    Args:
        message: Message to display
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    fig.update_layout(
        title={
            "text": f"Delta Robustness - {message}",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(title="Model"),
        yaxis=dict(
            title="ΔR",
            range=[0, 1],
        ),
        height=400,
        width=700,
    )
    return fig


def create_delta_chart_from_results(
    results: List[BenchmarkModelResult],
    title: str = "Delta Robustness Comparison",
) -> Any:
    """
    Create delta bar chart from list of model results.
    
    Args:
        results: List of BenchmarkModelResult objects
        title: Chart title
        
    Returns:
        Plotly figure
    """
    if not results:
        return create_empty_delta_chart("No results")
    
    # Extract data
    models = [r.model_name for r in results]
    deltas = [r.delta_robustness for r in results]
    
    # Color scale
    colors = []
    for delta in deltas:
        normalized = (delta + 1) / 2
        if normalized < 0.33:
            colors.append("#ef4444")
        elif normalized < 0.66:
            colors.append("#eab308")
        else:
            colors.append("#22c55e")
    
    fig = go.Figure(
        data=go.Bar(
            x=models,
            y=deltas,
            marker_color=colors,
            text=[f"ΔR={d:.3f}" for d in deltas],
            textposition="auto",
        )
    )
    
    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(
            title="Model",
            tickangle=-45,
        ),
        yaxis=dict(
            title="ΔR",
            range=[0, 1],
        ),
        height=400,
        width=700,
        margin=dict(b=80),
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig

"""
Stability Scatter Plot Component

Visualization component for stability analysis between baseline and adversarial robustness.
Shows models plotted on R_base vs R_adv space with diagonal reference line.
"""

import logging
from typing import Any, List, Optional

import plotly.graph_objects as go

from dashboard.schemas import BenchmarkComparisonData, BenchmarkModelResult
from dashboard.utils import log_dashboard_event

logger = logging.getLogger(__name__)


def create_stability_scatter(
    comparison: Optional[BenchmarkComparisonData],
) -> Any:
    """
    Create stability scatter plot from benchmark comparison data.
    
    Args:
        comparison: BenchmarkComparisonData object
        
    Returns:
        Plotly figure
    """
    if comparison is None or not comparison.model_results:
        return create_empty_stability_chart("No benchmark data available")
    
    log_dashboard_event(
        "DASHBOARD_VIEW_STABILITY_CHART",
        benchmark_id=comparison.benchmark_id,
    )
    
    return update_stability_scatter(comparison)


def update_stability_scatter(
    comparison: BenchmarkComparisonData,
) -> Any:
    """
    Update stability scatter plot with benchmark comparison data.
    
    Each model is plotted as a point at (R_base, R_adv).
    A diagonal line y=x shows perfect stability.
    Closer to diagonal = more stable.
    
    Args:
        comparison: BenchmarkComparisonData object
        
    Returns:
        Plotly figure
    """
    if not comparison.model_results:
        return create_empty_stability_chart("No model results")
    
    # Extract data
    baselines = [r.baseline_robustness for r in comparison.model_results]
    adversarials = [r.adversarial_robustness for r in comparison.model_results]
    models = [r.model_name for r in comparison.model_results]
    rsis = [r.rsi for r in comparison.model_results]
    
    # Color based on RSI (stability)
    # RSI close to 1 = stable = green
    # RSI far from 1 = unstable = red
    colors = []
    for rsi in rsis:
        # RSI range: 0 to 2, target is 1
        distance_from_1 = abs(rsi - 1)
        
        if distance_from_1 < 0.1:
            colors.append("#22c55e")  # Green - very stable
        elif distance_from_1 < 0.3:
            colors.append("#84cc16")  # Lime - stable
        elif distance_from_1 < 0.5:
            colors.append("#eab308")  # Yellow - moderate
        elif distance_from_1 < 0.7:
            colors.append("#f97316")  # Orange - unstable
        else:
            colors.append("#ef4444")  # Red - very unstable
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add diagonal line (perfect stability)
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect Stability (y=x)",
            line=dict(color="gray", dash="dash", width=2),
            hoverinfo="name",
        )
    )
    
    # Add model points
    fig.add_trace(
        go.Scatter(
            x=baselines,
            y=adversarials,
            mode="markers+text",
            name="Models",
            marker=dict(
                size=14,
                color=colors,
                line=dict(color="white", width=1),
            ),
            text=models,
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "R_base: %{x:.4f}<br>"
                "R_adv: %{y:.4f}<br>"
                "<extra></extra>"
            ),
        )
    )
    
    # Layout
    fig.update_layout(
        title={
            "text": f"Robustness Stability - {comparison.benchmark_name}",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(
            title="R_base (Baseline Robustness)",
            range=[0, 1],
            tickformat=".2f",
            constrain="domain",
        ),
        yaxis=dict(
            title="R_adv (Adversarial Robustness)",
            range=[0, 1],
            tickformat=".2f",
            scaleanchor="x",
            scaleratio=1,
        ),
        height=500,
        width=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
        ),
        hovermode="closest",
    )
    
    return fig


def create_empty_stability_chart(message: str = "Select a benchmark") -> Any:
    """
    Create empty stability chart with message.
    
    Args:
        message: Message to display
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Add diagonal line
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect Stability (y=x)",
            line=dict(color="gray", dash="dash", width=2),
        )
    )
    
    fig.update_layout(
        title={
            "text": f"Robustness Stability - {message}",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(
            title="R_base",
            range=[0, 1],
        ),
        yaxis=dict(
            title="R_adv",
            range=[0, 1],
            scaleanchor="x",
            scaleratio=1,
        ),
        height=500,
        width=600,
    )
    
    return fig


def create_stability_scatter_from_results(
    results: List[BenchmarkModelResult],
    title: str = "Robustness Stability",
) -> Any:
    """
    Create stability scatter plot from list of model results.
    
    Args:
        results: List of BenchmarkModelResult objects
        title: Chart title
        
    Returns:
        Plotly figure
    """
    if not results:
        return create_empty_stability_chart("No results")
    
    # Extract data
    baselines = [r.baseline_robustness for r in results]
    adversarials = [r.adversarial_robustness for r in results]
    models = [r.model_name for r in results]
    rsis = [r.rsi for r in results]
    
    # Color based on RSI
    colors = []
    for rsi in rsis:
        distance_from_1 = abs(rsi - 1)
        if distance_from_1 < 0.1:
            colors.append("#22c55e")
        elif distance_from_1 < 0.3:
            colors.append("#84cc16")
        elif distance_from_1 < 0.5:
            colors.append("#eab308")
        elif distance_from_1 < 0.7:
            colors.append("#f97316")
        else:
            colors.append("#ef4444")
    
    fig = go.Figure()
    
    # Add diagonal line
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect Stability (y=x)",
            line=dict(color="gray", dash="dash", width=2),
        )
    )
    
    # Add model points
    fig.add_trace(
        go.Scatter(
            x=baselines,
            y=adversarials,
            mode="markers+text",
            name="Models",
            marker=dict(
                size=14,
                color=colors,
                line=dict(color="white", width=1),
            ),
            text=models,
            textposition="top center",
            textfont=dict(size=10),
        )
    )
    
    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis=dict(
            title="R_base",
            range=[0, 1],
        ),
        yaxis=dict(
            title="R_adv",
            range=[0, 1],
            scaleanchor="x",
            scaleratio=1,
        ),
        height=500,
        width=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
        ),
    )
    
    return fig

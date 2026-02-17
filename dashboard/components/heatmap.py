"""
Heatmap Component

Gradio component for displaying attack vulnerability heatmaps.
"""

import logging
from typing import Any, List, Optional

import gradio as gr
import plotly.graph_objects as go

from dashboard.schemas import HeatmapData
from dashboard.utils import log_dashboard_event

logger = logging.getLogger(__name__)


def create_heatmap_chart() -> gr.Plot:
    """
    Create heatmap chart component.
    
    Returns:
        Plot component
    """
    plot = gr.Plot(
        label="Attack Vulnerability Heatmap",
    )
    
    return plot


def update_heatmap_chart(
    heatmap_data: Optional[HeatmapData],
) -> Any:
    """
    Update heatmap chart with data.
    
    Args:
        heatmap_data: Heatmap data
        
    Returns:
        Plotly figure
    """
    if heatmap_data is None or not heatmap_data.attack_types:
        # Return empty chart
        fig = go.Figure()
        fig.update_layout(
            title="No Data Available",
            xaxis=dict(title="Metrics"),
            yaxis=dict(title="Attack Types"),
        )
        return fig
    
    log_dashboard_event("DASHBOARD_VIEW_HEATMAP", run_id=heatmap_data.run_id)
    
    # Create heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.metrics,
            y=heatmap_data.attack_types,
            colorscale="RdYlGn_r",  # Red (high) to Green (low) - reversed
            zmin=0,
            zmax=1,
            colorbar=dict(
                title=dict(text="Metric Value", side="right"),
            ),
            hovertemplate=(
                "<b>Attack:</b> %{y}<br>"
                "<b>Metric:</b> %{x}<br>"
                "<b>Value:</b> %{z:.3f}<extra></extra>"
            ),
        )
    )
    
    fig.update_layout(
        title="Attack Vulnerability Heatmap",
        xaxis=dict(title="Metrics"),
        yaxis=dict(
            title="Attack Types",
            autorange="reversed",  # Top to bottom
        ),
        height=500,
        width=700,
    )
    
    return fig


def create_comparison_heatmap(
    heatmap_data_list: List[HeatmapData],
    model_names: List[str],
) -> Any:
    """
    Create comparison heatmap across multiple runs.
    
    Args:
        heatmap_data_list: List of heatmap data
        model_names: List of model names
        
    Returns:
        Plotly figure
    """
    if not heatmap_data_list:
        # Return empty chart
        fig = go.Figure()
        fig.update_layout(title="No Data Available")
        return fig
    
    # For comparison, we'll show the average vulnerability
    import numpy as np
    
    all_attack_types = set()
    for hd in heatmap_data_list:
        all_attack_types.update(hd.attack_types)
    
    attack_types = sorted(list(all_attack_types))
    metrics = heatmap_data_list[0].metrics if heatmap_data_list else []
    
    # Calculate average values
    avg_values = []
    for attack_type in attack_types:
        row = []
        for metric in metrics:
            values = []
            for hd in heatmap_data_list:
                if attack_type in hd.attack_types and metric in hd.metrics:
                    idx = hd.attack_types.index(attack_type)
                    m_idx = hd.metrics.index(metric)
                    values.append(hd.values[idx][m_idx])
            
            if values:
                row.append(np.mean(values))
            else:
                row.append(0.0)
        avg_values.append(row)
    
    fig = go.Figure(
        data=go.Heatmap(
            z=avg_values,
            x=metrics,
            y=attack_types,
            colorscale="RdYlGn_r",
            zmin=0,
            zmax=1,
            colorbar=dict(
                title=dict(text="Avg Value", side="right"),
            ),
        )
    )
    
    fig.update_layout(
        title="Average Attack Vulnerability Across Models",
        xaxis=dict(title="Metrics"),
        yaxis=dict(
            title="Attack Types",
            autorange="reversed",
        ),
        height=500,
        width=700,
    )
    
    return fig


class HeatmapChart:
    """
    Heatmap chart component with state management.
    """
    
    def __init__(self):
        """Initialize heatmap chart."""
        self._current_data: Optional[HeatmapData] = None
    
    def set_data(self, data: HeatmapData) -> None:
        """
        Set heatmap data.
        
        Args:
            data: Heatmap data
        """
        self._current_data = data
    
    def get_data(self) -> Optional[HeatmapData]:
        """
        Get current heatmap data.
        
        Returns:
            Current heatmap data or None
        """
        return self._current_data
    
    def get_figure(self) -> Any:
        """
        Get Plotly figure.
        
        Returns:
            Plotly figure
        """
        return update_heatmap_chart(self._current_data)
    
    @staticmethod
    def create_empty() -> Any:
        """
        Create empty heatmap chart.
        
        Returns:
            Empty Plotly figure
        """
        fig = go.Figure()
        fig.update_layout(
            title="Select a run to view vulnerability heatmap",
            xaxis=dict(title="Metrics"),
            yaxis=dict(title="Attack Types"),
            height=400,
            width=600,
        )
        return fig


def get_heatmap_tooltip() -> str:
    """
    Get heatmap tooltip explanation.
    
    Returns:
        Tooltip string
    """
    return (
        "Heatmap shows mean metric values for each attack type.\n\n"
        "Color Scale:\n"
        "• Red (1.0) = High vulnerability (bad)\n"
        "• Yellow (0.5) = Medium vulnerability\n"
        "• Green (0.0) = Low vulnerability (good)\n\n"
        "Formula: M_ij = mean(metric_j | attack_i)"
    )

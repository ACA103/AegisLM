"""
Radar Chart Component

Gradio component for displaying composite robustness radar charts.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import plotly.graph_objects as go

from dashboard.schemas import RadarData
from dashboard.utils import log_dashboard_event

logger = logging.getLogger(__name__)


def create_radar_chart() -> gr.Plot:
    """
    Create radar chart component.
    
    Returns:
        Plot component
    """
    plot = gr.Plot(
        label="Composite Robustness Radar",
    )
    
    return plot


def update_radar_chart(
    radar_data: Optional[RadarData],
) -> Any:
    """
    Update radar chart with data.
    
    Args:
        radar_data: Radar data
        
    Returns:
        Plotly figure
    """
    if radar_data is None:
        # Return empty chart
        fig = go.Figure()
        fig.update_layout(
            title="No Data Available",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1]),
            ),
        )
        return fig
    
    log_dashboard_event("DASHBOARD_VIEW_RADAR", run_id=radar_data.run_id)
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatterpolar(
            r=[
                radar_data.hallucination,
                radar_data.toxicity,
                radar_data.bias,
                radar_data.confidence,
            ],
            theta=[
                "Factual Stability",
                "Safety",
                "Fairness",
                "Confidence",
            ],
            fill="toself",
            name=radar_data.model_name or "Model",
            line_color="#2563eb",
            fillcolor="rgba(37, 99, 235, 0.3)",
        )
    )
    
    fig.update_layout(
        title=f"Robustness Radar - {radar_data.model_name or 'Model'}",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                title="Score (higher is better)",
            ),
        ),
        showlegend=True,
        height=500,
        width=500,
    )
    
    return fig


def create_multi_radar_chart(
    radar_data_list: List[RadarData],
) -> Any:
    """
    Create radar chart with multiple models.
    
    Args:
        radar_data_list: List of radar data for multiple models
        
    Returns:
        Plotly figure
    """
    if not radar_data_list:
        # Return empty chart
        fig = go.Figure()
        fig.update_layout(
            title="No Data Available",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1]),
            ),
        )
        return fig
    
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]
    
    fig = go.Figure()
    
    for i, radar_data in enumerate(radar_data_list):
        color = colors[i % len(colors)]
        
        fig.add_trace(
            go.Scatterpolar(
                r=[
                    radar_data.hallucination,
                    radar_data.toxicity,
                    radar_data.bias,
                    radar_data.confidence,
                ],
                theta=[
                    "Factual Stability",
                    "Safety",
                    "Fairness",
                    "Confidence",
                ],
                fill="toself",
                name=radar_data.model_name or f"Model {i+1}",
                line_color=color,
                fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.3)",
            )
        )
    
    fig.update_layout(
        title="Model Comparison Radar",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                title="Score (higher is better)",
            ),
        ),
        showlegend=True,
        height=600,
        width=600,
    )
    
    return fig


class RadarChart:
    """
    Radar chart component with state management.
    """
    
    def __init__(self):
        """Initialize radar chart."""
        self._current_data: Optional[RadarData] = None
    
    def set_data(self, data: RadarData) -> None:
        """
        Set radar data.
        
        Args:
            data: Radar data
        """
        self._current_data = data
    
    def get_data(self) -> Optional[RadarData]:
        """
        Get current radar data.
        
        Returns:
            Current radar data or None
        """
        return self._current_data
    
    def get_figure(self) -> Any:
        """
        Get Plotly figure.
        
        Returns:
            Plotly figure
        """
        return update_radar_chart(self._current_data)
    
    @staticmethod
    def create_empty() -> Any:
        """
        Create empty radar chart.
        
        Returns:
            Empty Plotly figure
        """
        fig = go.Figure()
        fig.update_layout(
            title="Select a run to view radar chart",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1]),
            ),
            height=400,
            width=400,
        )
        return fig


def get_radar_tooltip_formula() -> str:
    """
    Get radar chart formula tooltip.
    
    Returns:
        Formula string
    """
    return "Radar Vector: V = [1 - H̄, 1 - T̄, 1 - B̄, C̄]\n\n" + \
           "Where:\n" + \
           "• 1 - H̄ = 1 - mean hallucination (higher is better)\n" + \
           "• 1 - T̄ = 1 - mean toxicity (higher is better)\n" + \
           "• 1 - B̄ = 1 - mean bias (higher is better)\n" + \
           "• C̄ = mean confidence (higher is better)"

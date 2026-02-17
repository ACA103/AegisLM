"""
Metrics Panel Component

Gradio component for displaying metric summaries and statistics.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from dashboard.schemas import MetricSummary, RunSummary
from dashboard.utils import format_percentage, format_score

logger = logging.getLogger(__name__)


def create_metrics_panel() -> Tuple[gr.DataFrame, gr.JSON]:
    """
    Create metrics panel component.
    
    Returns:
        Tuple of (dataframe, json) components
    """
    
    # Metrics table
    metrics_table = gr.DataFrame(
        headers=["Metric", "Mean", "Std Dev", "Min", "Max", "Count"],
        label="Metric Summary",
        interactive=False,
    )
    
    # Summary JSON
    summary_json = gr.JSON(
        label="Run Summary",
        visible=False,
    )
    
    return metrics_table, summary_json


def update_metrics_panel(
    run_summary: Optional[RunSummary],
) -> Tuple[List[List[str]], Dict[str, Any]]:
    """
    Update metrics panel with run summary data.
    
    Args:
        run_summary: Run summary data
        
    Returns:
        Tuple of (table data, json data)
    """
    if run_summary is None:
        return [["N/A", "N/A", "N/A", "N/A", "N/A", "0"]], {}
    
    # Build table data
    table_data = []
    for metric in run_summary.metric_summary:
        table_data.append([
            metric.metric_name.capitalize(),
            format_score(metric.mean, 4),
            format_score(metric.std, 4),
            format_score(metric.min, 4),
            format_score(metric.max, 4),
            str(metric.count),
        ])
    
    # Add composite score
    if run_summary.composite_score is not None:
        table_data.append([
            "Composite Score",
            format_score(run_summary.composite_score, 4),
            "N/A",
            "N/A",
            "N/A",
            str(run_summary.total_samples),
        ])
    
    # Add vulnerability index
    table_data.append([
        "Vulnerability Index",
        format_score(run_summary.vulnerability_index, 4),
        "N/A",
        "N/A",
        "N/A",
        "N/A",
    ])
    
    # Build JSON data
    json_data = {
        "run_id": str(run_summary.metadata.run_id),
        "model_name": run_summary.metadata.model_name,
        "model_version": run_summary.metadata.model_version,
        "dataset_version": run_summary.metadata.dataset_version,
        "status": run_summary.metadata.status,
        "composite_score": run_summary.composite_score,
        "total_samples": run_summary.total_samples,
        "vulnerability_index": run_summary.vulnerability_index,
        "attack_coverage": run_summary.attack_coverage,
    }
    
    return table_data, json_data


def create_stat_display() -> Tuple[gr.Number, gr.Number, gr.Number, gr.Number]:
    """
    Create statistical display components.
    
    Returns:
        Tuple of (composite_score, vulnerability_index, sample_count, attack_count) components
    """
    
    with gr.Row():
        with gr.Column():
            composite_score = gr.Number(
                label="Composite Score",
                interactive=False,
            )
        with gr.Column():
            vulnerability_index = gr.Number(
                label="Vulnerability Index",
                interactive=False,
            )
        with gr.Column():
            sample_count = gr.Number(
                label="Total Samples",
                interactive=False,
            )
        with gr.Column():
            attack_count = gr.Number(
                label="Attack Types",
                interactive=False,
            )
    
    return composite_score, vulnerability_index, sample_count, attack_count


def update_stat_display(
    run_summary: Optional[RunSummary],
) -> Tuple[float, float, int, int]:
    """
    Update statistical displays.
    
    Args:
        run_summary: Run summary data
        
    Returns:
        Tuple of (composite_score, vulnerability_index, sample_count, attack_count)
    """
    if run_summary is None:
        return 0.0, 0.0, 0, 0
    
    return (
        run_summary.composite_score or 0.0,
        run_summary.vulnerability_index or 0.0,
        run_summary.total_samples,
        len(run_summary.attack_coverage),
    )


class MetricsPanel:
    """
    Metrics panel component with state management.
    """
    
    def __init__(self):
        """Initialize metrics panel."""
        self._current_summary: Optional[RunSummary] = None
    
    def set_summary(self, summary: RunSummary) -> None:
        """
        Set current run summary.
        
        Args:
            summary: Run summary data
        """
        self._current_summary = summary
    
    def get_summary(self) -> Optional[RunSummary]:
        """
        Get current run summary.
        
        Returns:
            Current run summary or None
        """
        return self._current_summary
    
    def get_table_data(self) -> List[List[str]]:
        """
        Get table data for display.
        
        Returns:
            Table data as list of rows
        """
        if self._current_summary is None:
            return [["N/A", "N/A", "N/A", "N/A", "N/A", "0"]]
        
        table_data = []
        for metric in self._current_summary.metric_summary:
            table_data.append([
                metric.metric_name.capitalize(),
                format_score(metric.mean, 4),
                format_score(metric.std, 4),
                format_score(metric.min, 4),
                format_score(metric.max, 4),
                str(metric.count),
            ])
        
        return table_data
    
    def get_metric_tooltips(self) -> Dict[str, str]:
        """
        Get metric tooltips with formulas.
        
        Returns:
            Dictionary of metric name to tooltip
        """
        return {
            "Hallucination": "Mean hallucination score (0 = no hallucination, 1 = full hallucination)",
            "Toxicity": "Mean toxicity score (0 = non-toxic, 1 = toxic)",
            "Bias": "Mean bias score (0 = unbiased, 1 = biased)",
            "Confidence": "Mean confidence score (0 = low, 1 = high)",
            "Composite Score": "R = w1(1-H) + w2(1-T) + w3(1-B) + w4*C",
            "Vulnerability Index": "(H + T + B) / 3 - average of negative metrics",
        }


def create_metric_card(
    metric_name: str,
    value: float,
    tooltip: str = "",
) -> gr.Component:
    """
    Create a metric card component.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        tooltip: Optional tooltip text
        
    Returns:
        Gradio component
    """
    card = gr.Number(
        label=metric_name,
        value=value,
        interactive=False,
    )
    
    return card


def create_metrics_grid() -> gr.Component:
    """
    Create metrics grid layout.
    
    Returns:
        Gradio component
    """
    with gr.Row():
        with gr.Column():
            gr.Number(label="Hallucination", interactive=False)
        with gr.Column():
            gr.Number(label="Toxicity", interactive=False)
        with gr.Column():
            gr.Number(label="Bias", interactive=False)
        with gr.Column():
            gr.Number(label="Confidence", interactive=False)
    
    return gr.Row()

"""
Run Selector Component

Gradio component for selecting evaluation runs.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from dashboard.data_loader import DashboardDataLoader
from dashboard.utils import format_timestamp, log_dashboard_event

logger = logging.getLogger(__name__)


def create_run_selector(
    data_loader: DashboardDataLoader,
) -> Tuple[gr.Dropdown, gr.DataFrame]:
    """
    Create run selector component.
    
    Args:
        data_loader: DashboardDataLoader instance
        
    Returns:
        Tuple of (dropdown, dataframe) components
    """
    
    def load_runs() -> List[Tuple[str, str]]:
        """
        Load available runs for dropdown.
        
        Returns:
            List of (run_id, label) tuples
        """
        try:
            runs = data_loader.get_all_runs()
            
            options = []
            for run in runs:
                label = f"{run['model_name']} ({run['timestamp'][:19] if run.get('timestamp') else 'N/A'}) - {run['status']}"
                options.append((label, run["id"]))
            
            return options
        except Exception as e:
            logger.error(f"Error loading runs: {e}")
            return [("No runs available", "")]
    
    def get_run_details(run_id: str) -> Dict[str, Any]:
        """
        Get run details for display.
        
        Args:
            run_id: Selected run ID
            
        Returns:
            Dictionary of run details
        """
        if not run_id:
            return {
                "model": "",
                "version": "",
                "dataset": "",
                "timestamp": "",
                "status": "",
                "score": "",
            }
        
        try:
            run = data_loader.get_run_by_id(run_id)
            log_dashboard_event("DASHBOARD_VIEW_RUN", run_id=run_id)
            
            if run:
                return {
                    "model": run.get("model_name", "N/A"),
                    "version": run.get("model_version", "N/A"),
                    "dataset": run.get("dataset_version", "N/A"),
                    "timestamp": run.get("timestamp", "N/A")[:19] if run.get("timestamp") else "N/A",
                    "status": run.get("status", "N/A"),
                    "score": f"{run.get('composite_score', 0):.4f}" if run.get("composite_score") else "N/A",
                }
        except Exception as e:
            logger.error(f"Error fetching run details: {e}")
        
        return {
            "model": "Error",
            "version": "",
            "dataset": "",
            "timestamp": "",
            "status": "",
            "score": "",
        }
    
    # Create components
    with gr.Row():
        with gr.Column(scale=2):
            run_dropdown = gr.Dropdown(
                label="Select Evaluation Run",
                choices=load_runs(),
                value=None,
                interactive=True,
            )
        with gr.Column(scale=1):
            refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
    
    # Run details display
    with gr.Row():
        details_df = gr.DataFrame(
            headers=["Property", "Value"],
            label="Run Details",
            interactive=False,
            visible=True,
        )
    
    # Event handlers
    def on_select(run_id: str) -> Dict[str, Any]:
        """Handle run selection."""
        details = get_run_details(run_id)
        data = [
            ["Model", details["model"]],
            ["Model Version", details["version"]],
            ["Dataset Version", details["dataset"]],
            ["Timestamp", details["timestamp"]],
            ["Status", details["status"]],
            ["Composite Score", details["score"]],
        ]
        return {"data": data}
    
    def on_refresh() -> List[Tuple[str, str]]:
        """Handle refresh button click."""
        return load_runs()
    
    run_dropdown.change(
        fn=on_select,
        inputs=[run_dropdown],
        outputs=[details_df],
    )
    
    refresh_btn.click(
        fn=on_refresh,
        inputs=[],
        outputs=[run_dropdown],
    )
    
    return run_dropdown, details_df


def create_run_selector_simple(
    data_loader: DashboardDataLoader,
) -> gr.Dropdown:
    """
    Create simple run selector dropdown.
    
    Args:
        data_loader: DashboardDataLoader instance
        
    Returns:
        Dropdown component
    """
    
    def load_runs() -> List[str]:
        """
        Load available run IDs.
        
        Returns:
            List of run ID strings
        """
        try:
            runs = data_loader.get_all_runs()
            return [run["id"] for run in runs]
        except Exception as e:
            logger.error(f"Error loading runs: {e}")
            return []
    
    dropdown = gr.Dropdown(
        label="Select Evaluation Run",
        choices=load_runs(),
        value=None,
        interactive=True,
    )
    
    return dropdown


class RunSelector:
    """
    Run selector component with caching and state management.
    """
    
    def __init__(self, data_loader: DashboardDataLoader):
        """
        Initialize run selector.
        
        Args:
            data_loader: DashboardDataLoader instance
        """
        self._data_loader = data_loader
        self._runs_cache = None
        self._selected_run = None
    
    def get_runs(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of runs.
        
        Args:
            force_refresh: Force refresh cache
            
        Returns:
            List of run dictionaries
        """
        if self._runs_cache is None or force_refresh:
            self._runs_cache = self._data_loader.get_all_runs()
        
        return self._runs_cache
    
    def get_run_choices(self) -> List[Tuple[str, str]]:
        """
        Get run choices for dropdown.
        
        Returns:
            List of (label, run_id) tuples
        """
        runs = self.get_runs()
        
        choices = []
        for run in runs:
            label = f"{run['model_name']} ({run.get('timestamp', 'N/A')[:19]})"
            choices.append((label, run["id"]))
        
        return choices
    
    def set_selected_run(self, run_id: str) -> None:
        """
        Set selected run ID.
        
        Args:
            run_id: Run ID to select
        """
        self._selected_run = run_id
        log_dashboard_event("DASHBOARD_VIEW_RUN", run_id=run_id)
    
    def get_selected_run(self) -> Optional[str]:
        """
        Get currently selected run ID.
        
        Returns:
            Selected run ID or None
        """
        return self._selected_run

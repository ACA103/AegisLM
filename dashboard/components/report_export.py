"""
Report Export Component

Gradio component for exporting evaluation reports.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from dashboard.schemas import ExportFormat, RunSummary
from dashboard.utils import export_report, log_dashboard_event

logger = logging.getLogger(__name__)


def create_export_panel() -> Tuple[gr.Dropdown, gr.Checkbox, gr.Button, gr.JSON]:
    """
    Create export panel component.
    
    Returns:
        Tuple of (format_dropdown, include_config_checkbox, export_button, output_json) components
    """
    
    # Format selector
    format_dropdown = gr.Dropdown(
        label="Export Format",
        choices=["json", "csv"],
        value="json",
        interactive=True,
    )
    
    # Options
    include_config_checkbox = gr.Checkbox(
        label="Include Configuration",
        value=True,
        interactive=True,
    )
    
    # Export button
    export_button = gr.Button(
        "Export Report",
        variant="primary",
    )
    
    # Output
    output_json = gr.JSON(
        label="Export Output",
        visible=True,
    )
    
    return format_dropdown, include_config_checkbox, export_button, output_json


def handle_export(
    run_summary: Optional[RunSummary],
    format: str,
    include_config: bool,
) -> Tuple[str, str]:
    """
    Handle export button click.
    
    Args:
        run_summary: Run summary data
        format: Export format (json or csv)
        include_config: Include configuration in export
        
    Returns:
        Tuple of (output, filename)
    """
    if run_summary is None:
        return "Error: No run data available", "error.txt"
    
    try:
        export_format = ExportFormat.JSON if format == "json" else ExportFormat.CSV
        
        output = export_report(
            run_summary,
            format=export_format,
            include_config=include_config,
            include_raw_outputs=False,
        )
        
        # Log event
        log_dashboard_event(
            "DASHBOARD_EXPORT_REPORT",
            run_id=str(run_summary.metadata.run_id),
            extra={"format": format},
        )
        
        # Generate filename
        filename = f"report_{run_summary.metadata.run_id}.{format}"
        
        return output, filename
        
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        return f"Error: {str(e)}", "error.txt"


def create_export_section() -> Tuple[gr.Button, gr.DownloadButton]:
    """
    Create export section with buttons.
    
    Returns:
        Tuple of (json_button, csv_button) components
    """
    
    json_button = gr.DownloadButton(
        label="Download JSON Report",
        value=None,
        interactive=False,
    )
    
    csv_button = gr.DownloadButton(
        label="Download CSV Report",
        value=None,
        interactive=False,
    )
    
    return json_button, csv_button


class ReportExporter:
    """
    Report exporter component with state management.
    """
    
    def __init__(self):
        """Initialize report exporter."""
        self._current_summary: Optional[RunSummary] = None
        self._export_cache: Dict[str, str] = {}
    
    def set_summary(self, summary: RunSummary) -> None:
        """
        Set current run summary.
        
        Args:
            summary: Run summary data
        """
        self._current_summary = summary
        # Clear cache when summary changes
        self._export_cache = {}
    
    def get_summary(self) -> Optional[RunSummary]:
        """
        Get current run summary.
        
        Returns:
            Current run summary or None
        """
        return self._current_summary
    
    def export_json(self, include_config: bool = True) -> Optional[str]:
        """
        Export report as JSON.
        
        Args:
            include_config: Include configuration in export
            
        Returns:
            JSON string or None
        """
        if self._current_summary is None:
            return None
        
        cache_key = f"json_{include_config}"
        if cache_key in self._export_cache:
            return self._export_cache[cache_key]
        
        output = export_report(
            self._current_summary,
            format=ExportFormat.JSON,
            include_config=include_config,
            include_raw_outputs=False,
        )
        
        self._export_cache[cache_key] = output
        return output
    
    def export_csv(self) -> Optional[str]:
        """
        Export report as CSV.
        
        Returns:
            CSV string or None
        """
        if self._current_summary is None:
            return None
        
        cache_key = "csv"
        if cache_key in self._export_cache:
            return self._export_cache[cache_key]
        
        output = export_report(
            self._current_summary,
            format=ExportFormat.CSV,
            include_config=False,
            include_raw_outputs=False,
        )
        
        self._export_cache[cache_key] = output
        return output
    
    def get_filename(self, format: ExportFormat) -> str:
        """
        Get export filename.
        
        Args:
            format: Export format
            
        Returns:
            Filename string
        """
        if self._current_summary is None:
            return f"report.{format.value}"
        
        return f"report_{self._current_summary.metadata.run_id}.{format.value}"


def create_export_options() -> Tuple[gr.Checkbox, gr.Checkbox, gr.Checkbox]:
    """
    Create export options checkboxes.
    
    Returns:
        Tuple of checkbox components
    """
    
    include_config = gr.Checkbox(
        label="Include Configuration (config_hash, weights)",
        value=True,
        interactive=True,
    )
    
    include_metadata = gr.Checkbox(
        label="Include Metadata (model, dataset versions)",
        value=True,
        interactive=True,
    )
    
    include_raw = gr.Checkbox(
        label="Include Raw Outputs (privacy sensitive)",
        value=False,
        interactive=True,
    )
    
    return include_config, include_metadata, include_raw


def get_export_info() -> str:
    """
    Get export information text.
    
    Returns:
        Information string
    """
    return """
## Export Requirements

The exported report includes:

1. **Run Metadata**:
   - Run ID
   - Model name and version
   - Dataset version
   - Timestamp
   - Status

2. **Aggregate Metrics**:
   - Mean, Std, Min, Max for each metric
   - Sample count
   - Composite score
   - Vulnerability index

3. **Configuration** (optional):
   - Config hash for reproducibility
   - Scoring weights

4. **Raw Outputs** (optional, privacy sensitive):
   - Raw model outputs
   - Processed prompts

Note: Raw outputs are disabled by default to protect sensitive information.
"""


def create_share_report_section() -> Tuple[gr.Textbox, gr.Button]:
    """
    Create share report section.
    
    Returns:
        Tuple of (share_link, copy_button) components
    """
    
    share_link = gr.Textbox(
        label="Share Link",
        interactive=False,
        visible=False,
    )
    
    copy_button = gr.Button(
        "Copy Link",
        visible=False,
    )
    
    return share_link, copy_button

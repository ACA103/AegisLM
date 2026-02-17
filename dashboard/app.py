"""
AegisLM Dashboard Application

Governance-grade analytics interface for evaluation results,
benchmark comparisons, and model robustness visualization.

Built with Gradio and Plotly.
"""

import logging
from typing import Any, Dict, List, Optional

import gradio as gr

from dashboard.components.attack_breakdown import (
    ATTACK_BREAKDOWN_HEADERS,
    create_attack_breakdown_table,
    create_attack_selector,
    format_breakdown_tooltip,
    get_attack_breakdown_details,
    get_breakdown_tooltip_explanation,
    get_small_sample_warning,
    log_attack_breakdown_view,
    update_attack_breakdown_table,
    update_attack_selector,
)
from dashboard.components.comparison_table import (
    create_comparison_table,
    update_comparison_table,
    update_delta_chart,
)
from dashboard.components.delta_bar_chart import (
    create_delta_bar_chart,
    create_empty_delta_chart,
    update_delta_bar_chart,
)
from dashboard.components.heatmap import create_heatmap_chart, update_heatmap_chart
from dashboard.components.metrics_panel import (
    create_metrics_panel,
    update_metrics_panel,
    update_stat_display,
)
from dashboard.components.radar_chart import create_radar_chart, update_radar_chart
from dashboard.components.ranking_table import (
    RANKING_HEADERS,
    create_ranking_table,
    update_ranking_table,
)
from dashboard.components.report_export import (
    create_export_panel,
    handle_export,
    get_export_info,
)
from dashboard.components.run_selector import create_run_selector
from dashboard.components.stability_scatter import (
    create_stability_scatter,
    create_empty_stability_chart,
    update_stability_scatter,
)
from dashboard.data_loader import DashboardDataLoader
from dashboard.schemas import (
    BenchmarkComparisonData,
    BenchmarkStats,
    ComparisonData,
    DeltaRobustnessData,
    RunSummary,
)
from dashboard.utils import (
    format_score,
    get_sample_heatmap_data,
    get_sample_radar_data,
    get_sample_run_summary,
    log_dashboard_event,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Dashboard Application
# =============================================================================


class AegisLMDashboard:
    """
    AegisLM Dashboard Application.
    
    Main Gradio interface for governance-grade analytics.
    """

    def __init__(self, data_loader: Optional[DashboardDataLoader] = None):
        """
        Initialize dashboard.
        
        Args:
            data_loader: Optional data loader instance
        """
        self._data_loader = data_loader or DashboardDataLoader()
        self._current_run_id: Optional[str] = None
        self._current_summary: Optional[RunSummary] = None

    def load_run_data(self, run_id: str) -> Dict[str, Any]:
        """
        Load all data for a run.
        
        Args:
            run_id: Run ID to load
            
        Returns:
            Dictionary with all visualization data
        """
        self._current_run_id = run_id
        
        # Get run summary
        run_summary = self._data_loader.get_run_summary(run_id)
        self._current_summary = run_summary
        
        # Get radar data
        radar_data = self._data_loader.get_radar_data(run_id)
        
        # Get heatmap data
        heatmap_data = self._data_loader.get_attack_heatmap(run_id)
        
        # Get attack breakdown data
        attack_breakdown = self._data_loader.get_attack_breakdown(run_id)
        
        return {
            "run_summary": run_summary,
            "radar_data": radar_data,
            "heatmap_data": heatmap_data,
            "attack_breakdown": attack_breakdown,
        }

    def get_comparison_data(
        self,
        run_ids: List[str],
    ) -> tuple[ComparisonData, List[DeltaRobustnessData]]:
        """
        Get comparison data for multiple runs.
        
        Args:
            run_ids: List of run IDs to compare
            
        Returns:
            Tuple of (comparison_data, delta_data)
        """
        comparison_data = self._data_loader.get_model_comparison(run_ids)
        delta_data = self._data_loader.get_delta_robustness(run_ids)
        
        return comparison_data, delta_data


def create_dashboard(
    data_loader: Optional[DashboardDataLoader] = None,
    demo_mode: bool = False,
) -> gr.Blocks:
    """
    Create the Gradio dashboard interface.
    
    Args:
        data_loader: Optional data loader instance
        demo_mode: Enable demo mode with sample data
        
    Returns:
        Gradio Blocks interface
    """
    # Initialize dashboard
    dashboard = AegisLMDashboard(data_loader)
    
    # =============================================================================
    # UI Layout
    # =============================================================================
    
    with gr.Blocks(
        title="AegisLM Dashboard",
        theme=gr.themes.Soft(),
    ) as app:
        
        # Header
        gr.Markdown("""
        # 🛡️ AegisLM Dashboard
        
        **Governance-Grade Analytics Interface**
        
        Multi-Agent Adversarial LLM Evaluation Framework
        
        ---
        """)
        
        # =============================================================================
        # Tab 1: Evaluation Runs
        # =============================================================================
        
        with gr.Tab("Evaluation Runs"):
            gr.Markdown("### Select and analyze evaluation runs")
            
            # Run selector
            with gr.Row():
                run_dropdown = gr.Dropdown(
                    label="Select Evaluation Run",
                    choices=[],
                    interactive=True,
                    allow_custom_value=True,
                )
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
            
            # Run details
            with gr.Row():
                with gr.Column(scale=2):
                    # Radar chart
                    radar_plot = gr.Plot(label="Composite Robustness Radar")
                with gr.Column(scale=1):
                    # Quick stats
                    composite_score = gr.Number(label="Composite Score", interactive=False)
                    vulnerability_index = gr.Number(label="Vulnerability Index", interactive=False)
                    sample_count = gr.Number(label="Total Samples", interactive=False)
            
            # Heatmap
            with gr.Row():
                heatmap_plot = gr.Plot(label="Attack Vulnerability Heatmap")
            
            # Attack Breakdown Section
            gr.Markdown("### Per-Attack Metric Breakdown")
            
            with gr.Row():
            # Attack type selector dropdown
                attack_selector = gr.Dropdown(
                    label="Select Attack Type",
                    choices=[],
                    interactive=True,
                    allow_custom_value=True,
                )
            
            # Attack breakdown table
            with gr.Row():
                attack_breakdown_table = gr.Dataframe(
                    headers=ATTACK_BREAKDOWN_HEADERS,
                    label="Attack Breakdown Details",
                    interactive=False,
                )
            
            # Metrics table
            with gr.Row():
                metrics_table = gr.DataFrame(
                    headers=["Metric", "Mean", "Std Dev", "Min", "Max", "Count"],
                    label="Metric Summary",
                    interactive=False,
                )
        
        # =============================================================================
        # Tab 2: Benchmark Comparison
        # =============================================================================
        
        with gr.Tab("Benchmark Comparison"):
            gr.Markdown("### Cross-Model Benchmark Comparison")
            
            # Benchmark selector
            with gr.Row():
                benchmark_dropdown = gr.Dropdown(
                    label="Select Benchmark",
                    choices=[],
                    interactive=True,
                    allow_custom_value=True,
                )
                refresh_benchmarks_btn = gr.Button("🔄 Refresh", variant="secondary")
            
            # Charts row
            with gr.Row():
                with gr.Column(scale=1):
                    # Delta bar chart
                    delta_plot = gr.Plot(label="Delta Robustness (ΔR)")
                with gr.Column(scale=1):
                    # Stability scatter plot
                    stability_plot = gr.Plot(label="Robustness Stability")
            
            # Ranking table
            gr.Markdown("### Model Rankings")
            with gr.Row():
                ranking_table = gr.Dataframe(
                    headers=RANKING_HEADERS,
                    label="Model Rankings (Sorted by R_adv, then VI)",
                    interactive=False,
                )
            
            # Statistical summary
            gr.Markdown("### Statistical Summary")
            with gr.Row():
                with gr.Column():
                    mean_baseline = gr.Number(label="Mean R_base", interactive=False)
                    mean_adversarial = gr.Number(label="Mean R_adv", interactive=False)
                    mean_delta = gr.Number(label="Mean ΔR", interactive=False)
                with gr.Column():
                    std_baseline = gr.Number(label="Std R_base", interactive=False)
                    best_model = gr.Textbox(label="Best Model", interactive=False)
                    most_stable = gr.Textbox(label="Most Stable", interactive=False)
                with gr.Column():
                    mean_rsi = gr.Number(label="Mean RSI", interactive=False)
                    most_vulnerable = gr.Textbox(label="Most Vulnerable", interactive=False)
                    total_models = gr.Number(label="Total Models", interactive=False)
            
            # Formula explanation
            with gr.Accordion("Formulas", open=False):
                gr.Markdown("""
                **Delta Robustness**: ΔR = R_base - R_adv
                
                **RSI (Robustness Stability Index)**: RSI = R_adv / R_base
                - Closer to 1 = more stable
                
                **VI (Vulnerability Index)**: VI = ΔR / R_base
                - Higher = more fragile
                
                **Ranking**: Primary by R_adv (descending), Secondary by VI (ascending)
                """)
            
            # Legacy comparison section (for run-based comparison)
            gr.Markdown("---")
            gr.Markdown("### Run-Based Comparison (Legacy)")
            with gr.Row():
                model_multiselect = gr.Dropdown(
                    label="Select Models to Compare",
                    choices=[],
                    interactive=True,
                    multiselect=True,
                    allow_custom_value=True,
                )
                compare_btn = gr.Button("Compare", variant="primary")
            
            # Legacy comparison table
            with gr.Row():
                comparison_table = gr.DataFrame(
                    headers=["Model", "Hallucination", "Toxicity", "Bias", "Confidence", "Composite Score", "Sample Count"],
                    label="Model Comparison",
                    interactive=False,
                )
        
        # =============================================================================
        # Tab 3: Model Ranking
        # =============================================================================
        
        with gr.Tab("Model Ranking"):
            gr.Markdown("### Model rankings by robustness")
            
            # Ranking table
            with gr.Row():
                ranking_table = gr.DataFrame(
                    headers=["Rank", "Model", "Composite Score", "Delta"],
                    label="Model Rankings",
                    interactive=False,
                )
            
            # Info
            gr.Markdown("""
            **Formula**: R = w₁(1-H) + w₂(1-T) + w₃(1-B) + w₄*C
            
            Where:
            - H = Hallucination score
            - T = Toxicity score
            - B = Bias score
            - C = Confidence score
            - Weights: w₁ = w₂ = w₃ = w₄ = 0.25
            """)
        
        # =============================================================================
        # Tab 4: Export Reports
        # =============================================================================
        
        with gr.Tab("Export Reports"):
            gr.Markdown("### Export evaluation reports")
            
            # Export options
            with gr.Row():
                with gr.Column():
                    export_format = gr.Dropdown(
                        label="Export Format",
                        choices=["json", "csv"],
                        value="json",
                        interactive=True,
                    )
                with gr.Column():
                    include_config = gr.Checkbox(
                        label="Include Configuration",
                        value=True,
                        interactive=True,
                    )
            
            # Export button
            export_btn = gr.Button("Export Report", variant="primary")
            
            # Export output
            export_output = gr.JSON(label="Export Output")
            
            # Export info
            with gr.Accordion("Export Information", open=False):
                gr.Markdown(get_export_info())
        
        # =============================================================================
        # Footer
        # =============================================================================
        
        gr.Markdown("""
        ---
        
        **AegisLM** - Multi-Agent Adversarial LLM Evaluation Framework
        
        Version 0.1.0
        """)
        
        # =============================================================================
        # Event Handlers
        # =============================================================================
        
        def load_runs() -> List[str]:
            """Load available runs."""
            try:
                runs = dashboard._data_loader.get_all_runs()
                choices = [run["id"] for run in runs]
                return choices
            except Exception as e:
                logger.error(f"Error loading runs: {e}")
                return []
        
        def on_run_select(run_id):
            """Handle run selection."""
            # Handle both string and list inputs from Gradio
            if isinstance(run_id, list):
                if not run_id:
                    return (
                        create_empty_radar(),
                        0.0, 0.0, 0,
                        create_empty_heatmap(),
                        [],  # attack_selector choices
                        [["N/A", "0", "0.000", "0.000", "0.000", "0.000", "0.000", "0.000"]],  # attack_breakdown_table
                        [["N/A", "N/A", "N/A", "N/A", "N/A", "0"]],  # metrics_table
                    )
                # Take the first run_id from the list
                run_id = run_id[0]
            
            if not run_id:
                return (
                    create_empty_radar(),
                    0.0, 0.0, 0,
                    create_empty_heatmap(),
                    [],  # attack_selector choices
                    [["N/A", "0", "0.000", "0.000", "0.000", "0.000", "0.000", "0.000"]],  # attack_breakdown_table
                    [["N/A", "N/A", "N/A", "N/A", "N/A", "0"]],  # metrics_table
                )
            
            log_dashboard_event("DASHBOARD_VIEW_RUN", run_id=run_id)
            
            # Load data
            data = dashboard.load_run_data(run_id)
            
            run_summary = data["run_summary"]
            radar_data = data["radar_data"]
            heatmap_data = data["heatmap_data"]
            attack_breakdown = data.get("attack_breakdown")
            
            # Log heatmap view
            if heatmap_data:
                log_dashboard_event("DASHBOARD_VIEW_HEATMAP", run_id=run_id)
            
            # Get updates
            radar_fig = update_radar_chart(radar_data)
            heatmap_fig = update_heatmap_chart(heatmap_data)
            
            # Get stats
            stats = update_stat_display(run_summary)
            
            # Get attack breakdown data
            attack_selector_choices = update_attack_selector(attack_breakdown)
            attack_table_data = update_attack_breakdown_table(attack_breakdown)
            
            # Get metrics table
            table_data, _ = update_metrics_panel(run_summary)
            
            return (
                radar_fig,
                stats[0], stats[1], stats[2],
                heatmap_fig,
                attack_selector_choices,
                attack_table_data,
                table_data,
            )
        
        def on_refresh():
            """Handle refresh button."""
            return load_runs()
        
        def on_compare(model_ids: List[str]):
            """Handle compare button."""
            if not model_ids or len(model_ids) < 2:
                return (
                    [["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "0"]],
                    create_empty_delta(),
                )
            
            log_dashboard_event("DASHBOARD_COMPARE_MODELS", extra={"count": len(model_ids)})
            
            comparison_data, delta_data = dashboard.get_comparison_data(model_ids)
            
            table_data = update_comparison_table(comparison_data)
            delta_fig = update_delta_chart(delta_data)
            
            return table_data, delta_fig
        
        def on_export(run_id, format: str, include_config: bool):
            """Handle export button."""
            # Handle case where run_id might be a list (from Gradio dropdown)
            if isinstance(run_id, list):
                run_id = run_id[0] if run_id else None
            
            if not run_id:
                return {"error": "No run selected", "content": ""}

            summary = dashboard._data_loader.get_run_summary(run_id)

            if summary is None:
                return {"error": "Run not found", "content": ""}

            result = handle_export(summary, format, include_config)
            
            # Handle tuple return (output, filename)
            if isinstance(result, tuple):
                output, filename = result
                # For CSV format, wrap in a dict that JSON can handle
                if format == "csv":
                    return {
                        "format": "csv",
                        "filename": filename,
                        "content": output if output else ""
                    }
                return {"content": output, "filename": filename}
            return result

        def load_benchmarks() -> List[str]:
            """Load available benchmarks."""
            try:
                benchmarks = dashboard._data_loader.list_benchmarks()
                choices = [b.benchmark_id for b in benchmarks]
                return choices
            except Exception as e:
                logger.error(f"Error loading benchmarks: {e}")
                return []

        def on_benchmark_select(benchmark_id):
            """Handle benchmark selection."""
            # Handle both string and list inputs from Gradio
            if isinstance(benchmark_id, list):
                if not benchmark_id:
                    return (
                        create_empty_delta_chart("Select a benchmark"),
                        create_empty_stability_chart("Select a benchmark"),
                        [["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "0"]],
                        0.0, 0.0, 0.0,
                        "N/A", "N/A",
                        0.0, "N/A", "N/A", 0,
                    )
                # Take the first benchmark_id from the list
                benchmark_id = benchmark_id[0]
            
            if not benchmark_id:
                return (
                    create_empty_delta_chart("Select a benchmark"),
                    create_empty_stability_chart("Select a benchmark"),
                    [["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "0"]],
                    0.0, 0.0, 0.0,
                    "N/A", "N/A",
                    0.0, "N/A", "N/A", 0,
                )

            log_dashboard_event("DASHBOARD_VIEW_BENCHMARK", extra={"benchmark_id": benchmark_id})

            # Load benchmark comparison data
            comparison = dashboard._data_loader.get_benchmark_comparison(benchmark_id)
            stats = dashboard._data_loader.get_benchmark_stats(benchmark_id)

            if comparison is None or stats is None:
                return (
                    create_empty_delta_chart("Benchmark not found"),
                    create_empty_stability_chart("Benchmark not found"),
                    [["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "0"]],
                    0.0, 0.0, 0.0,
                    "N/A", "N/A",
                    0.0, "N/A", "N/A", 0,
                )

            # Generate charts
            delta_fig = update_delta_bar_chart(comparison)
            stability_fig = update_stability_scatter(comparison)
            ranking_data = update_ranking_table(comparison)

            return (
                delta_fig,
                stability_fig,
                ranking_data,
                stats.mean_baseline,
                stats.mean_adversarial,
                stats.mean_delta,
                stats.std_baseline,
                stats.best_model,
                stats.most_stable,
                stats.mean_rsi,
                stats.most_vulnerable,
                stats.total_models,
            )

        def on_refresh_benchmarks():
            """Handle refresh benchmarks button."""
            return load_benchmarks()
        
        # Bind events
        run_dropdown.change(
            fn=on_run_select,
            inputs=[run_dropdown],
            outputs=[
                radar_plot,
                composite_score, vulnerability_index, sample_count,
                heatmap_plot,
                attack_selector,
                attack_breakdown_table,
                metrics_table,
            ],
        )
        
        refresh_btn.click(
            fn=on_refresh,
            inputs=[],
            outputs=[run_dropdown],
        )
        
        compare_btn.click(
            fn=on_compare,
            inputs=[model_multiselect],
            outputs=[comparison_table, delta_plot],
        )
        
        export_btn.click(
            fn=on_export,
            inputs=[run_dropdown, export_format, include_config],
            outputs=[export_output],
        )
        
        # Benchmark events
        benchmark_dropdown.change(
            fn=on_benchmark_select,
            inputs=[benchmark_dropdown],
            outputs=[
                delta_plot,
                stability_plot,
                ranking_table,
                mean_baseline,
                mean_adversarial,
                mean_delta,
                std_baseline,
                best_model,
                most_stable,
                mean_rsi,
                most_vulnerable,
                total_models,
            ],
        )
        
        refresh_benchmarks_btn.click(
            fn=on_refresh_benchmarks,
            inputs=[],
            outputs=[benchmark_dropdown],
        )
        
        # Load runs and benchmarks on start
        app.load(
            fn=load_runs,
            inputs=[],
            outputs=[run_dropdown, model_multiselect],
        )
        
        # Load benchmarks on start
        app.load(
            fn=load_benchmarks,
            inputs=[],
            outputs=[benchmark_dropdown],
        )
    
    return app


# =============================================================================
# Helper Functions
# =============================================================================


def create_empty_radar():
    """Create empty radar chart."""
    import plotly.graph_objects as go
    
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


def create_empty_heatmap():
    """Create empty heatmap."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    fig.update_layout(
        title="Select a run to view vulnerability heatmap",
        xaxis=dict(title="Metrics"),
        yaxis=dict(title="Attack Types"),
        height=400,
        width=600,
    )
    return fig


def create_empty_delta():
    """Create empty delta chart."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    fig.update_layout(
        title="Select models to compare",
        xaxis=dict(title="Model"),
        yaxis=dict(title="Delta Robustness"),
        height=400,
        width=600,
    )
    return fig


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """Main entry point for the dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AegisLM Dashboard")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to bind to",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Enable demo mode with sample data",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Create dashboard
    app = create_dashboard(demo_mode=args.demo)
    
    # Launch
    app.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.debug,  # Share in debug mode for testing
    )


if __name__ == "__main__":
    main()

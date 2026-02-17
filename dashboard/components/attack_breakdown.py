"""
Attack Breakdown Component

Gradio component for displaying per-attack metric breakdown and vulnerability analysis.
"""

import logging
from typing import Any, List, Optional

import gradio as gr

from dashboard.schemas import AttackBreakdown, AttackBreakdownList
from dashboard.utils import log_dashboard_event

logger = logging.getLogger(__name__)


# Table headers for attack breakdown
ATTACK_BREAKDOWN_HEADERS = [
    "Attack Type",
    "Sample Count",
    "Hallucination",
    "Toxicity",
    "Bias",
    "Confidence",
    "Robustness",
    "Vulnerability Index",
]


def create_attack_breakdown_table() -> gr.Dataframe:
    """
    Create attack breakdown table component.
    
    Returns:
        DataFrame component
    """
    table = gr.Dataframe(
        headers=ATTACK_BREAKDOWN_HEADERS,
        label="Per-Attack Metric Breakdown",
        interactive=False,
    )
    return table


def create_attack_selector() -> gr.Dropdown:
    """
    Create attack type selector dropdown.
    
    Returns:
        Dropdown component
    """
    dropdown = gr.Dropdown(
        label="Select Attack Type",
        choices=[],
        interactive=True,
    )
    return dropdown


def update_attack_breakdown_table(
    breakdown_list: Optional[AttackBreakdownList],
) -> List[List[Any]]:
    """
    Update attack breakdown table with data.
    
    Args:
        breakdown_list: Attack breakdown list
        
    Returns:
        Table data as list of lists
    """
    if breakdown_list is None or not breakdown_list.breakdowns:
        return [["N/A", "0", "0.000", "0.000", "0.000", "0.000", "0.000", "0.000"]]
    
    table_data = []
    for breakdown in breakdown_list.breakdowns:
        table_data.append(breakdown.to_table_row())
    
    return table_data


def update_attack_selector(
    breakdown_list: Optional[AttackBreakdownList],
) -> List[str]:
    """
    Update attack selector dropdown with available attack types.
    
    Args:
        breakdown_list: Attack breakdown list
        
    Returns:
        List of attack type choices
    """
    if breakdown_list is None or not breakdown_list.breakdowns:
        return []
    
    return [b.attack_type for b in breakdown_list.breakdowns]


def get_attack_breakdown_details(
    breakdown_list: Optional[AttackBreakdownList],
    attack_type: str,
) -> Optional[AttackBreakdown]:
    """
    Get breakdown details for a specific attack type.
    
    Args:
        breakdown_list: Attack breakdown list
        attack_type: The attack type to get details for
        
    Returns:
        AttackBreakdown or None
    """
    if breakdown_list is None or not breakdown_list.breakdowns:
        return None
    
    for breakdown in breakdown_list.breakdowns:
        if breakdown.attack_type == attack_type:
            return breakdown
    
    return None


def format_breakdown_tooltip(breakdown: AttackBreakdown) -> str:
    """
    Format tooltip text for breakdown details.
    
    Args:
        breakdown: Attack breakdown
        
    Returns:
        Formatted tooltip string
    """
    tooltips = {
        "hallucination": "High value indicates increased factual instability under this attack.",
        "toxicity": "High value indicates increased toxic content generation under this attack.",
        "bias": "High value indicates increased biased output under this attack.",
        "confidence_collapse": "High value indicates model uncertainty increase.",
    }
    
    return (
        f"Attack: {breakdown.attack_type}\n"
        f"Samples: {breakdown.sample_count}\n"
        f"Hallucination: {breakdown.mean_hallucination:.3f} - {tooltips['hallucination']}\n"
        f"Toxicity: {breakdown.mean_toxicity:.3f} - {tooltips['toxicity']}\n"
        f"Bias: {breakdown.mean_bias:.3f} - {tooltips['bias']}\n"
        f"Confidence: {breakdown.mean_confidence:.3f}\n"
        f"Confidence Collapse: {breakdown.confidence_collapse:.3f} - {tooltips['confidence_collapse']}\n"
        f"Robustness (R_a): {breakdown.robustness:.3f}\n"
        f"Vulnerability Index (VI_a): {breakdown.vulnerability_index:.3f}"
    )


def get_small_sample_warning(sample_count: int) -> str:
    """
    Get warning message for small sample sizes.
    
    Args:
        sample_count: Number of samples
        
    Returns:
        Warning message or empty string
    """
    if sample_count < 3:
        return f"⚠️ Warning: Small sample size ({sample_count}). Results may not be statistically significant."
    return ""


class AttackBreakdownComponent:
    """
    Attack breakdown component with state management.
    """
    
    def __init__(self):
        """Initialize attack breakdown component."""
        self._current_breakdown_list: Optional[AttackBreakdownList] = None
    
    def set_data(self, data: AttackBreakdownList) -> None:
        """
        Set breakdown data.
        
        Args:
            data: Attack breakdown list
        """
        self._current_breakdown_list = data
    
    def get_data(self) -> Optional[AttackBreakdownList]:
        """
        Get current breakdown data.
        
        Returns:
            Current breakdown list or None
        """
        return self._current_breakdown_list
    
    def get_attack_types(self) -> List[str]:
        """
        Get available attack types.
        
        Returns:
            List of attack type strings
        """
        if self._current_breakdown_list is None:
            return []
        return [b.attack_type for b in self._current_breakdown_list.breakdowns]
    
    @staticmethod
    def create_empty_table() -> List[List[Any]]:
        """
        Create empty breakdown table.
        
        Returns:
            Empty table data
        """
        return [["N/A", "0", "0.000", "0.000", "0.000", "0.000", "0.000", "0.000"]]


def log_attack_breakdown_view(run_id: str, attack_type: str) -> None:
    """
    Log attack breakdown view event.
    
    Args:
        run_id: Evaluation run ID
        attack_type: Selected attack type
    """
    log_dashboard_event(
        "DASHBOARD_VIEW_ATTACK_BREAKDOWN",
        run_id=run_id,
        attack_type=attack_type,
    )


def get_breakdown_tooltip_explanation() -> str:
    """
    Get breakdown tooltip explanation for governance interpretation.
    
    Returns:
        Explanation string
    """
    return """
    ## Metric Interpretation Guide
    
    ### Hallucination
    High value indicates increased factual instability under this attack.
    - Red (1.0): Model produces significant hallucinations
    - Green (0.0): Model maintains factual accuracy
    
    ### Toxicity
    High value indicates increased toxic content generation under this attack.
    - Red (1.0): Model generates highly toxic content
    - Green (0.0): Model generates non-toxic content
    
    ### Bias
    High value indicates increased biased output under this attack.
    - Red (1.0): Model shows significant bias
    - Green (0.0): Model is unbiased
    
    ### Confidence Collapse
    High value indicates model uncertainty increase.
    - Red (1.0): Complete confidence collapse
    - Green (0.0): Full model confidence
    
    ### Robustness (R_a)
    Composite score for this attack: R = w₁(1-H) + w₂(1-T) + w₃(1-B) + w₄*C
    - Higher is better
    
    ### Vulnerability Index (VI_a)
    Relative vulnerability compared to baseline:
    - VI = (R_base - R_adv) / R_base
    - Higher means more vulnerable to this attack
    """

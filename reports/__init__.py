"""
Reports Module

Exportable governance reports for AegisLM evaluation framework.
Supports:
- Run reports (JSON/CSV)
- Benchmark reports (JSON/CSV)
- Report integrity validation
- Report metadata
"""

import csv
import json
import hashlib
import logging
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

__version__ = "0.1.0"

# Default reports directory
REPORTS_DIR = Path("reports")

logger = logging.getLogger(__name__)


# =============================================================================
# Directory Management
# =============================================================================


def get_reports_directory() -> Path:
    """
    Get the reports directory path.
    
    Returns:
        Path to reports directory
    """
    return REPORTS_DIR


def ensure_reports_directory() -> Path:
    """
    Ensure the reports directory exists.
    
    Returns:
        Path to reports directory
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def list_reports() -> List[str]:
    """
    List all available report files.
    
    Returns:
        List of report filenames
    """
    ensure_reports_directory()
    return [f.name for f in REPORTS_DIR.glob("*.json")]


def list_benchmark_reports() -> List[str]:
    """
    List all available benchmark report files.
    
    Returns:
        List of benchmark report filenames
    """
    ensure_reports_directory()
    return [f.name for f in REPORTS_DIR.glob("benchmark_*.json")]


# =============================================================================
# Report ID Generation
# =============================================================================


def generate_report_id(run_id: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate unique report ID using SHA256(run_id + timestamp).
    
    Args:
        run_id: The run identifier
        timestamp: Optional timestamp (defaults to now)
        
    Returns:
        SHA256 hash as hex string (first 16 characters for brevity)
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    data_to_hash = f"{run_id}_{timestamp.isoformat()}"
    return hashlib.sha256(data_to_hash.encode()).hexdigest()[:16]


# =============================================================================
# Save Run Report
# =============================================================================


def save_report(
    report_data: Dict[str, Any],
    run_id: str,
    format: str = "json",
) -> str:
    """
    Save a run report to the reports directory.
    
    Args:
        report_data: The report data dictionary
        run_id: The run identifier
        format: The format (json or csv)
        
    Returns:
        Path to the saved file
    """
    ensure_reports_directory()
    
    # Generate report ID
    report_id = generate_report_id(run_id)
    
    # Add report ID to data
    report_data["report_id"] = report_id
    report_data["generated_at"] = datetime.utcnow().isoformat()
    
    # Determine filename
    filename = f"report_{run_id}_{report_id}.{format}"
    filepath = REPORTS_DIR / filename
    
    if format == "json":
        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2)
    elif format == "csv":
        # Convert to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["Metric", "Mean", "Value"])
        
        # Data rows
        if "aggregate_metrics" in report_data:
            for metric_name, metric_data in report_data["aggregate_metrics"].items():
                if isinstance(metric_data, dict):
                    writer.writerow([
                        metric_name,
                        metric_data.get("mean", ""),
                        json.dumps(metric_data),
                    ])
        
        with open(filepath, "w") as f:
            f.write(output.getvalue())
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(
        f"Report saved",
        metadata={"report_id": report_id, "run_id": run_id, "format": format, "path": str(filepath)},
    )
    
    return str(filepath)


# =============================================================================
# Save Benchmark Report
# =============================================================================


def save_benchmark_report(
    report_data: Dict[str, Any],
    benchmark_id: str,
    format: str = "json",
) -> str:
    """
    Save a benchmark report to the reports directory.
    
    Args:
        report_data: The report data dictionary
        benchmark_id: The benchmark identifier
        format: The format (json or csv)
        
    Returns:
        Path to the saved file
    """
    ensure_reports_directory()
    
    # Generate report ID
    timestamp = datetime.utcnow()
    report_id = hashlib.sha256(f"{benchmark_id}_{timestamp.isoformat()}".encode()).hexdigest()[:16]
    
    # Add report metadata
    report_data["report_id"] = report_id
    report_data["generated_at"] = timestamp.isoformat()
    report_data["benchmark_id"] = benchmark_id
    
    # Determine filename
    filename = f"benchmark_{benchmark_id}_{report_id}.{format}"
    filepath = REPORTS_DIR / filename
    
    if format == "json":
        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2)
    elif format == "csv":
        # Convert to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["Rank", "Model", "Baseline", "Adversarial", "Delta_R", "RSI", "VI"])
        
        # Data rows
        if "models" in report_data:
            for model in report_data["models"]:
                writer.writerow([
                    model.get("rank", ""),
                    model.get("model_name", ""),
                    model.get("baseline_robustness", ""),
                    model.get("adversarial_robustness", ""),
                    model.get("delta_R", ""),
                    model.get("RSI", ""),
                    model.get("VI", ""),
                ])
        
        with open(filepath, "w") as f:
            f.write(output.getvalue())
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(
        f"Benchmark report saved",
        metadata={"report_id": report_id, "benchmark_id": benchmark_id, "format": format, "path": str(filepath)},
    )
    
    return str(filepath)


# =============================================================================
# Load Report
# =============================================================================


def load_report(report_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a report by ID.
    
    Args:
        report_id: The report identifier
        
    Returns:
        Report data dictionary or None if not found
    """
    ensure_reports_directory()
    
    # Search for report
    for filepath in REPORTS_DIR.glob("report_*.json"):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                if data.get("report_id") == report_id:
                    return data
        except Exception:
            continue
    
    return None


def load_benchmark_report(report_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a benchmark report by ID.
    
    Args:
        report_id: The report identifier
        
    Returns:
        Report data dictionary or None if not found
    """
    ensure_reports_directory()
    
    # Search for report
    for filepath in REPORTS_DIR.glob("benchmark_*.json"):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                if data.get("report_id") == report_id:
                    return data
        except Exception:
            continue
    
    return None


# =============================================================================
# Delete Report
# =============================================================================


def delete_report(report_id: str) -> bool:
    """
    Delete a report by ID.
    
    Args:
        report_id: The report identifier
        
    Returns:
        True if deleted, False if not found
    """
    ensure_reports_directory()
    
    for filepath in REPORTS_DIR.glob("report_*.json"):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                if data.get("report_id") == report_id:
                    filepath.unlink()
                    logger.info(f"Report deleted", metadata={"report_id": report_id})
                    return True
        except Exception:
            continue
    
    return False


def delete_benchmark_report(report_id: str) -> bool:
    """
    Delete a benchmark report by ID.
    
    Args:
        report_id: The report identifier
        
    Returns:
        True if deleted, False if not found
    """
    ensure_reports_directory()
    
    for filepath in REPORTS_DIR.glob("benchmark_*.json"):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                if data.get("report_id") == report_id:
                    filepath.unlink()
                    logger.info(f"Benchmark report deleted", metadata={"report_id": report_id})
                    return True
        except Exception:
            continue
    
    return False


__all__ = [
    "REPORTS_DIR",
    "get_reports_directory",
    "ensure_reports_directory",
    "list_reports",
    "list_benchmark_reports",
    "generate_report_id",
    "save_report",
    "save_benchmark_report",
    "load_report",
    "load_benchmark_report",
    "delete_report",
    "delete_benchmark_report",
]

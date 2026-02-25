"""
Ecosystem Analytics Layer

Provides aggregated, anonymized ecosystem-wide metrics for AI governance.
All data is aggregated to protect individual tenant information.
"""

from ecosystem.analytics_engine import (
    EcosystemAnalyticsEngine,
    SectorRobustnessMetrics,
    AttackTrendMetrics,
    VulnerabilityPattern,
    EcosystemDashboardData,
)

__all__ = [
    "EcosystemAnalyticsEngine",
    "SectorRobustnessMetrics",
    "AttackTrendMetrics",
    "VulnerabilityPattern",
    "EcosystemDashboardData",
]

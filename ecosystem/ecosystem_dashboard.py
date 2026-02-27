"""
Ecosystem Dashboard Component

Provides visualization and data access for the ecosystem analytics layer.
Integrates with the main dashboard to display ecosystem-wide metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ecosystem.analytics_engine import (
    EcosystemAnalyticsEngine,
    EcosystemDashboardData,
    SectorRobustnessMetrics,
    AttackTrendMetrics,
    VulnerabilityPattern,
    CertificationDistribution,
)


@dataclass
class DashboardChartData:
    """Data structure for dashboard charts."""
    chart_type: str
    title: str
    data: Dict[str, Any]
    labels: List[str]
    values: List[float]
    colors: Optional[List[str]] = None


@dataclass
class EcosystemAlert:
    """Ecosystem-level alert."""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    affected_sectors: List[str]
    timestamp: datetime
    action_required: bool = False


class EcosystemDashboard:
    """
    Dashboard component for ecosystem analytics.
    
    Provides:
    - Public metrics visualization
    - Enterprise benchmarking
    - Alert management
    - Trend analysis
    """
    
    def __init__(self, analytics_engine: Optional[EcosystemAnalyticsEngine] = None):
        """
        Initialize the ecosystem dashboard.
        
        Args:
            analytics_engine: Optional analytics engine instance
        """
        self._analytics = analytics_engine or EcosystemAnalyticsEngine()
        self._alerts: List[EcosystemAlert] = []
        self._initialize_demo_alerts()
    
    def _initialize_demo_alerts(self):
        """Initialize demo alerts."""
        self._alerts = [
            EcosystemAlert(
                alert_id="ALERT-001",
                alert_type="vulnerability",
                severity="critical",
                title="New Jailbreak Technique Detected",
                description="Multi-turn jailbreak chains showing increased success in Technology sector",
                affected_sectors=["Technology", "Retail"],
                timestamp=datetime.utcnow() - timedelta(hours=2),
                action_required=True,
            ),
            EcosystemAlert(
                alert_id="ALERT-002",
                alert_type="certification",
                severity="medium",
                title="Certification Downgrade Wave",
                description="5 models in Finance sector have shown declining robustness",
                affected_sectors=["Finance"],
                timestamp=datetime.utcnow() - timedelta(hours=8),
                action_required=False,
            ),
        ]
    
    # =========================================================================
    # Public Dashboard Data
    # =========================================================================
    
    def get_public_metrics(self) -> Dict[str, Any]:
        """
        Get public-facing metrics for the dashboard.
        
        Returns:
            Dictionary of public metrics
        """
        dashboard_data = self._analytics.get_dashboard_data()
        
        return {
            "total_active_models": dashboard_data.total_active_models,
            "average_ecosystem_robustness": dashboard_data.average_ecosystem_robustness,
            "certification_distribution": {
                "tier_a": dashboard_data.certification_distribution.tier_a_count,
                "tier_b": dashboard_data.certification_distribution.tier_b_count,
                "tier_c": dashboard_data.certification_distribution.tier_c_count,
                "tier_d": dashboard_data.certification_distribution.tier_d_count,
            },
            "participating_organizations": dashboard_data.participating_organizations,
            "total_evaluations": dashboard_data.total_evaluations,
            "last_updated": dashboard_data.last_updated.isoformat(),
        }
    
    def get_sector_robustness_chart(self) -> DashboardChartData:
        """
        Get sector robustness data for bar chart.
        
        Returns:
            Chart data for sector robustness
        """
        dashboard_data = self._analytics.get_dashboard_data()
        
        labels = [s.sector for s in dashboard_data.sector_metrics]
        values = [s.avg_robustness for s in dashboard_data.sector_metrics]
        
        # Color by tier
        colors = []
        for v in values:
            if v >= 0.85:
                colors.append("#22c55e")  # Green - Tier A
            elif v >= 0.70:
                colors.append("#3b82f6")  # Blue - Tier B
            elif v >= 0.50:
                colors.append("#f59e0b")  # Yellow - Tier C
            else:
                colors.append("#ef4444")  # Red - Tier D
        
        return DashboardChartData(
            chart_type="bar",
            title="Average Robustness by Sector",
            data={},
            labels=labels,
            values=values,
            colors=colors,
        )
    
    def get_certification_distribution_chart(self) -> DashboardChartData:
        """
        Get certification distribution data for pie chart.
        
        Returns:
            Chart data for certification distribution
        """
        dist = self._analytics.get_dashboard_data().certification_distribution
        
        labels = ["Tier A", "Tier B", "Tier C", "Tier D"]
        values = [
            dist.tier_a_count,
            dist.tier_b_count,
            dist.tier_c_count,
            dist.tier_d_count,
        ]
        colors = ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444"]
        
        return DashboardChartData(
            chart_type="pie",
            title="Certification Tier Distribution",
            data={},
            labels=labels,
            values=values,
            colors=colors,
        )
    
    def get_attack_trends_chart(self) -> DashboardChartData:
        """
        Get attack trends data for line chart.
        
        Returns:
            Chart data for attack trends
        """
        trends = self._analytics.get_all_attack_trends()
        
        labels = [t.attack_type for t in trends]
        values = [t.success_rate for t in trends]
        
        return DashboardChartData(
            chart_type="line",
            title="Attack Success Rates",
            data={},
            labels=labels,
            values=values,
            colors=None,
        )
    
    def get_vulnerability_index(self) -> float:
        """
        Calculate composite vulnerability index.
        
        Returns:
            Vulnerability index [0, 1] where 1 = most vulnerable
        """
        trends = self._analytics.get_all_attack_trends()
        
        if not trends:
            return 0.0
        
        # Average of attack success rates
        avg_success = sum(t.success_rate for t in trends) / len(trends)
        
        # Weight by trend (increasing attacks more concerning)
        trend_weight = 1.0 + sum(max(0, t.trend_percent / 100) for t in trends) / len(trends)
        
        vulnerability = avg_success * trend_weight
        
        return min(1.0, round(vulnerability, 3))
    
    def get_gss_version_adoption(self) -> Dict[str, float]:
        """
        Get GSS version adoption rates.
        
        Returns:
            Dictionary of version adoption percentages
        """
        return {
            "v1.0": 45.0,
            "v1.1": 35.0,
            "v1.2": 20.0,
        }
    
    def get_regional_compliance(self) -> List[Dict[str, Any]]:
        """
        Get regional compliance alignment.
        
        Returns:
            List of regional compliance data
        """
        return [
            {
                "region": "North America",
                "compliance_rate": 0.92,
                "average_robustness": 0.82,
                "certification_count": 68,
            },
            {
                "region": "Europe",
                "compliance_rate": 0.88,
                "average_robustness": 0.79,
                "certification_count": 45,
            },
            {
                "region": "Asia Pacific",
                "compliance_rate": 0.85,
                "average_robustness": 0.76,
                "certification_count": 38,
            },
            {
                "region": "Other",
                "compliance_rate": 0.78,
                "average_robustness": 0.72,
                "certification_count": 18,
            },
        ]
    
    # =========================================================================
    # Enterprise Dashboard Data
    # =========================================================================
    
    def compare_against_sector(
        self,
        robustness_score: float,
        sector: str,
    ) -> Dict[str, Any]:
        """
        Compare a model's robustness against sector average.
        
        Args:
            robustness_score: Model's robustness score
            sector: Industry sector
            
        Returns:
            Comparison result
        """
        return self._analytics.compare_against_sector(robustness_score, sector)
    
    def get_peer_benchmarking(
        self,
        sector: str,
        organization_id: str,
    ) -> Dict[str, Any]:
        """
        Get peer benchmarking data (opt-in).
        
        Args:
            sector: Industry sector
            organization_id: Organization identifier
            
        Returns:
            Benchmarking data with anonymized peers
        """
        sector_metrics = self._analytics.calculate_sector_robustness(sector, [])
        
        return {
            "sector": sector,
            "sector_average": sector_metrics.avg_robustness,
            "peer_count": sector_metrics.sample_count,
            "your_percentile": 75,  # Demo value
            "peer_average_delta": -0.02,
            "top_performers": [
                {"percentile": 99, "score": 0.94},
                {"percentile": 95, "score": 0.91},
                {"percentile": 90, "score": 0.88},
            ],
        }
    
    # =========================================================================
    # Alert Management
    # =========================================================================
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Get active ecosystem alerts.
        
        Returns:
            List of active alerts
        """
        return [
            {
                "alert_id": a.alert_id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "affected_sectors": a.affected_sectors,
                "timestamp": a.timestamp.isoformat(),
                "action_required": a.action_required,
            }
            for a in self._alerts
        ]
    
    def add_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        affected_sectors: List[str],
    ) -> EcosystemAlert:
        """
        Add a new ecosystem alert.
        
        Args:
            alert_type: Type of alert
            severity: Alert severity
            title: Alert title
            description: Alert description
            affected_sectors: Affected sectors
            
        Returns:
            Created alert
        """
        alert = EcosystemAlert(
            alert_id=f"ALERT-{len(self._alerts) + 1:03d}",
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            affected_sectors=affected_sectors,
            timestamp=datetime.utcnow(),
            action_required=severity in ["critical", "high"],
        )
        
        self._alerts.append(alert)
        return alert
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert identifier
            
        Returns:
            True if acknowledged
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.action_required = False
                return True
        return False
    
    # =========================================================================
    # Complete Dashboard
    # =========================================================================
    
    def get_complete_dashboard(self) -> Dict[str, Any]:
        """
        Get complete dashboard data.
        
        Returns:
            All dashboard data
        """
        robustness_chart = self.get_sector_robustness_chart()
        cert_chart = self.get_certification_distribution_chart()
        attack_chart = self.get_attack_trends_chart()
        
        return {
            "public_metrics": self.get_public_metrics(),
            "sector_robustness": {
                "chart_type": robustness_chart.chart_type,
                "labels": robustness_chart.labels,
                "values": robustness_chart.values,
                "colors": robustness_chart.colors,
            },
            "certification_distribution": {
                "chart_type": cert_chart.chart_type,
                "labels": cert_chart.labels,
                "values": cert_chart.values,
                "colors": cert_chart.colors,
            },
            "attack_trends": {
                "chart_type": attack_chart.chart_type,
                "labels": attack_chart.labels,
                "values": attack_chart.values,
            },
            "vulnerability_index": self.get_vulnerability_index(),
            "gss_version_adoption": self.get_gss_version_adoption(),
            "regional_compliance": self.get_regional_compliance(),
            "active_alerts": self.get_active_alerts(),
        }


# =============================================================================
# Factory
# =============================================================================

def create_ecosystem_dashboard() -> EcosystemDashboard:
    """Create and return an ecosystem dashboard instance."""
    analytics = EcosystemAnalyticsEngine()
    return EcosystemDashboard(analytics)


__all__ = [
    "EcosystemDashboard",
    "DashboardChartData",
    "EcosystemAlert",
    "create_ecosystem_dashboard",
]

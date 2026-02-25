# Ecosystem Aggregated Metrics

## Overview

This document describes the aggregated metrics available through the AegisLM Ecosystem Analytics Layer. All metrics are computed from anonymized, aggregated data to protect individual tenant information.

## Aggregation Methodology

### Data Aggregation Formula

All sector-level metrics use the following aggregation formula:

```
SectorRobustness_{avg} = (1/n) * Σ R_i
```

Where:
- `n` = number of evaluations in the sector
- `R_i` = robustness score for evaluation i

### Trend Calculation

Trends are calculated as percentage change from the previous period:

```
Trend(t) = (R_t - R_{t-1}) / R_{t-1} * 100
```

## Available Metrics

### 1. Sector Robustness Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| `avg_robustness` | Mean robustness score across sector | [0, 1] |
| `median_robustness` | Median robustness score | [0, 1] |
| `std_deviation` | Standard deviation of robustness | [0, 1] |
| `sample_count` | Number of evaluations | ≥ 10 |
| `tier_distribution` | Count per certification tier | {A, B, C, D} |

### 2. Attack Success Trends

| Metric | Description | Range |
|--------|-------------|-------|
| `success_rate` | Percentage of successful attacks | [0, 1] |
| `trend_percent` | Change from previous period | [-100, 100] |
| `sample_count` | Number of attack attempts | ≥ 10 |

Attack types tracked:
- Injection attacks
- Jailbreak attempts
- Bias triggers
- Context poisoning
- Role confusion
- Multi-hop chaining

### 3. Vulnerability Patterns

| Field | Description |
|-------|-------------|
| `pattern_id` | Unique vulnerability identifier |
| `pattern_type` | Category of vulnerability |
| `severity` | Impact level (low, medium, high, critical) |
| `affected_sectors` | List of impacted industries |
| `occurrence_count` | Total occurrences detected |

### 4. Certification Distribution

| Tier | Robustness Range | Count |
|------|-----------------|-------|
| Tier A | ≥ 0.85 | Current count |
| Tier B | 0.70 - 0.84 | Current count |
| Tier C | 0.50 - 0.69 | Current count |
| Tier D | < 0.50 | Current count |

### 5. Drift Metrics

Drift detection tracks changes in model behavior over time:

| Metric | Description | Threshold |
|--------|-------------|-----------|
| `hallucination_drift` | Change in hallucination rate | > 0.1 |
| `toxicity_drift` | Change in toxicity rate | > 0.1 |
| `bias_drift` | Change in bias rate | > 0.1 |
| `confidence_drift` | Change in confidence | > 0.1 |
| `overall_drift_score` | Average of all drifts | > 0.1 |

## Privacy Guarantees

### Data Protection

1. **No Tenant Identifiers**: All tenant-specific identifiers are removed
2. **k-Anonymity**: Minimum 10 evaluations required for any metric
3. **No Model Names**: Only aggregated sector-level data exposed
4. **No User Data**: All user-identifiable information excluded
5. **Aggregation Only**: Only statistical aggregates returned

### Verification

Each API response includes a privacy compliance verification:

```
json
{
  "compliant": true,
  "checks": {
    "no_tenant_identifiers": true,
    "no_model_identifiers": true,
    "no_user_data": true,
    "only_aggregated_metrics": true,
    "k_anonymity_met": true
  }
}
```

## Usage in Dashboard

### Public Dashboard View

The public ecosystem dashboard displays:
- Average robustness by industry
- Certification tier distribution
- Attack vulnerability index
- GSS version adoption rates
- Regional compliance alignment

### Enterprise Benchmarking (Opt-in)

Enterprise tenants can opt-in to compare against sector averages:

```
python
result = engine.compare_against_sector(
    robustness_score=0.82,
    sector="Healthcare"
)
```

Response:
```
json
{
  "sector_average": 0.78,
  "your_score": 0.82,
  "delta": 0.04,
  "percentile": 72,
  "risk_assessment": "above_average"
}
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /ecosystem/metrics` | Get all ecosystem metrics |
| `GET /ecosystem/sectors/{sector}` | Get metrics for specific sector |
| `GET /ecosystem/trends` | Get attack trend data |
| `GET /ecosystem/vulnerabilities` | Get vulnerability patterns |
| `GET /ecosystem/certifications` | Get certification distribution |

## Rate Limits

- **Public API**: 60 requests/minute
- **Enterprise API**: 600 requests/minute
- **Dashboard**: Real-time with 5-minute cache

## Data Freshness

- Metrics updated: Every 15 minutes
- Trend data: Daily aggregation
- Vulnerability patterns: Real-time detection
- Certification distribution: Hourly updates

---

*Last Updated: Week 11 Day 2*
*Version: 1.0*

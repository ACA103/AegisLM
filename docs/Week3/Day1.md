# ✅ Week 3 – Day 1

---

## Objective

Design the **Robustness Scoring Dashboard Architecture** (Gradio + Plotly) before implementing UI components.

Today is UI system design, data flow definition, and visualization schema planning.

No visual polishing yet.
We design a **governance-grade analytics interface**.

---

# 1️⃣ Dashboard Architectural Role

Dashboard must:

* Display evaluation runs
* Display benchmark comparisons
* Show vulnerability heatmaps
* Show radar charts
* Compare models
* Export JSON reports
* Show run metadata
* Show statistical deltas

---

# 2️⃣ Dashboard Folder Structure

Create:

```
dashboard/
│
├── app.py
├── components/
│   ├── run_selector.py
│   ├── metrics_panel.py
│   ├── radar_chart.py
│   ├── heatmap.py
│   ├── comparison_table.py
│   └── report_export.py
│
├── data_loader.py
├── schemas.py
└── utils.py
```

Dashboard communicates with backend via internal function calls (same container).

---

# 3️⃣ Dashboard Architecture Diagram (Conceptual)

```
User
  ↓
Gradio Interface
  ↓
Dashboard Controller
  ↓
Backend DB + Artifact Loader
  ↓
Visualization Generator (Plotly)
  ↓
UI Render
```

No direct DB exposure to frontend.

---

# 4️⃣ Data Retrieval Layer

File: `dashboard/data_loader.py`

Responsibilities:

* Fetch evaluation_runs
* Fetch evaluation_results
* Fetch benchmark artifacts
* Transform data into chart-ready format

Define:

```python
class DashboardDataLoader:
    def get_run_summary(run_id)
    def get_attack_heatmap(run_id)
    def get_model_comparison(benchmark_id)
```

---

# 5️⃣ Visualization Requirements

We define 4 primary visualization types.

---

## 1️⃣ Composite Robustness Radar Chart

Axes:

* 1 − Hallucination
* 1 − Toxicity
* 1 − Bias
* Confidence

Each normalized [0,1].

Mathematically:

Radar vector:

[
V = [1 - \bar{H}, 1 - \bar{T}, 1 - \bar{B}, \bar{C}]
]

Used to compare models.

---

## 2️⃣ Attack Vulnerability Heatmap

Matrix:

Rows = Attack Types
Columns = Metrics

Cell value:

[
M_{ij} = mean(metric_j | attack_i)
]

Color-coded:

* Red → high vulnerability
* Green → low vulnerability

---

## 3️⃣ Delta Robustness Comparison Chart

Bar chart:

[
\Delta R_{model}
]

Allows cross-model ranking.

---

## 4️⃣ Metric Trend Line (Optional)

If multiple runs:

Plot robustness over time.

---

# 6️⃣ Data Schema for Visualization

Define in `schemas.py`:

```python
class RadarData(BaseModel):
    hallucination: float
    toxicity: float
    bias: float
    confidence: float
```

---

```python
class HeatmapData(BaseModel):
    attack_types: List[str]
    metrics: List[str]
    values: List[List[float]]
```

---

# 7️⃣ Statistical Display Requirements

Dashboard must show:

* Mean
* Standard deviation
* Delta robustness
* Vulnerability index
* Sample size

Display formulas in tooltip.

---

# 8️⃣ Report Export Requirements

Allow export:

* Benchmark JSON
* CSV summary
* PDF-ready JSON (future)

Export must include:

* Config hash
* Dataset version
* Model version
* Weights
* Aggregate metrics
* Delta metrics

---

# 9️⃣ Performance Considerations

Dashboard must:

* Avoid loading full raw outputs
* Load only aggregated metrics
* Use DB queries with filtering
* Paginate large results

---

# 🔟 Security Considerations

* No raw prompt exposure by default
* Optional debug toggle
* No arbitrary file reads

---

# 11️⃣ UI Layout Plan (Gradio Blocks)

Structure:

```
Header: AegisLM Dashboard

Tabs:
  - Evaluation Runs
  - Benchmark Comparison
  - Model Ranking
  - Export Reports
```

Within Evaluation Runs:

* Run selector dropdown
* Radar chart
* Heatmap
* Metric summary table

---

# 12️⃣ Logging Dashboard Usage

Log:

```
DASHBOARD_VIEW_RUN
DASHBOARD_EXPORT_REPORT
DASHBOARD_COMPARE_MODELS
```

Include timestamp + run_id.

---

# 13️⃣ Documentation Updates

Update:

`docs/architecture.md`:

Add dashboard component diagram.

Update:

`docs/blog.md` outline section:

* Governance visualization layer.

---

# 14️⃣ Risks

* Loading large result sets into memory.
* UI freezing during large benchmark.
* Inconsistent metric scales.
* Misleading color scaling.

Mitigation:

* Cap visualized runs.
* Normalize all metrics.
* Add color scale legend.

---

# 15️⃣ Validation Criteria

Day 1 complete if:

* Dashboard folder structure created.
* DataLoader interface defined.
* Visualization schema defined.
* Radar + heatmap math formally defined.
* UI layout drafted.
* Export requirements documented.

No charts rendered yet.

---

# 📦 Deliverables

1. `dashboard/` structure created
2. Visualization schemas defined
3. Data loader interface created
4. UI layout plan defined
5. Export specification defined
6. Architecture documentation updated

---

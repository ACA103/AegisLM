# ✅ Week 3 – Day 2

---

## Objective

Implement the first functional visualization layer:

* **Composite Robustness Radar Chart**
* **Metrics Summary Panel**
* Data transformation from DB → Plotly
* Gradio integration (basic functional UI)

Today the dashboard becomes operational.

---

# 1️⃣ Architecture Recap

We implement:

```
dashboard/
├── app.py
├── data_loader.py
├── components/
│   ├── radar_chart.py
│   └── metrics_panel.py
```

Focus only on **Evaluation Runs tab**.

---

# 2️⃣ Data Flow for Radar Chart

Flow:

```
User selects run_id
      ↓
DataLoader.get_run_summary(run_id)
      ↓
Aggregate metrics fetched
      ↓
Transform to radar vector
      ↓
Plotly radar chart
      ↓
Rendered in Gradio
```

---

# 3️⃣ Mathematical Definition (Radar Data)

We compute:

[
V = [1 - \bar{H}, 1 - \bar{T}, 1 - \bar{B}, \bar{C}]
]

Where:

* ( \bar{H} ) = mean hallucination
* ( \bar{T} ) = mean toxicity
* ( \bar{B} ) = mean bias
* ( \bar{C} ) = mean confidence

All values ∈ [0,1].

Radar labels:

```
["Factual Stability", "Safety", "Fairness", "Confidence"]
```

---

# 4️⃣ Data Loader Implementation

File: `dashboard/data_loader.py`

### get_run_summary()

Must:

1. Query evaluation_runs table
2. Compute mean metrics from evaluation_results
3. Return:

```python
{
  "hallucination_mean": ...,
  "toxicity_mean": ...,
  "bias_mean": ...,
  "confidence_mean": ...,
  "robustness": ...,
  "std_dev": {...},
  "sample_count": ...
}
```

---

### Standard Deviation Calculation

For hallucination:

[
\sigma_H = \sqrt{\frac{1}{N}\sum(H_i - \bar{H})^2}
]

Compute for each metric.

---

# 5️⃣ Radar Chart Component

File: `components/radar_chart.py`

Use Plotly:

```python
go.Scatterpolar(
    r=[...],
    theta=[...],
    fill='toself'
)
```

Axis range fixed:

```
range = [0, 1]
```

No auto-scaling.

---

# 6️⃣ Metrics Panel Component

File: `components/metrics_panel.py`

Display:

* Composite Robustness Score
* Hallucination Mean ± Std
* Toxicity Mean ± Std
* Bias Mean ± Std
* Confidence Mean ± Std
* Sample Count
* Dataset Version
* Model Version

Format values to 4 decimals.

---

# 7️⃣ UI Layout (Gradio Blocks)

In `app.py`:

```
with gr.Blocks():
    gr.Markdown("# AegisLM Dashboard")

    with gr.Tab("Evaluation Runs"):
        run_dropdown
        radar_plot
        metrics_panel
```

Populate dropdown dynamically from DB:

```
SELECT id FROM evaluation_runs ORDER BY timestamp DESC
```

---

# 8️⃣ Performance Considerations

Avoid:

* Loading full raw outputs
* Running expensive queries repeatedly

Optimization:

* Cache run summary per session
* Use DB aggregation queries instead of Python loops when possible

Example:

```sql
SELECT AVG(hallucination), STDDEV(hallucination)
FROM evaluation_results
WHERE run_id = ...
```

---

# 9️⃣ Logging Requirements

Log:

```
DASHBOARD_VIEW_RUN
{
  run_id,
  timestamp
}
```

Ensure no sensitive output logged.

---

# 🔟 Edge Case Handling

If run_id invalid:

* Show error message
* Do not crash UI

If run has zero samples:

* Show “No data available”

If metrics outside [0,1]:

* Raise error (indicates scoring bug)

---

# 11️⃣ Validation Tests

Create test scenario:

1. Run baseline evaluation.
2. Run adversarial evaluation.
3. Load both in dashboard.
4. Verify:

   * Radar values correct
   * Means match DB
   * Composite score matches formula

---

# 12️⃣ Risks

* Radar misinterpreted as absolute measure.
* Metric normalization inconsistency.
* Std deviation computation error.
* DB query performance degradation.

Mitigation:

* Lock metric ranges.
* Validate aggregation query.
* Add unit test for metric consistency.

---

# 13️⃣ Documentation Updates

Update:

`docs/architecture.md`

Add:

```
Dashboard Layer
  - Radar Visualization
  - Metrics Summary
  - Aggregation Pipeline
```

Update:

`docs/blog.md` outline:

Add section:

> Visualizing Robustness: Radar-Based Governance Analytics

---

# 14️⃣ Validation Criteria

Day 2 complete if:

* Dashboard loads successfully.
* Run dropdown populated.
* Radar chart renders correctly.
* Metrics panel displays correct numbers.
* Std deviations computed correctly.
* No raw outputs exposed.
* UI stable under multiple selections.

---

# 📦 Deliverables

1. Radar chart implemented
2. Metrics panel implemented
3. DataLoader aggregation functional
4. Gradio app boots and displays runs
5. DB aggregation verified
6. Structured logging added
7. Architecture documentation updated

---

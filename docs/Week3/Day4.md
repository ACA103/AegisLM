# ✅ Week 3 – Day 4

---

## Objective

Implement the **Cross-Model Comparison Dashboard + Ranking Table + Delta Robustness Visualization**.

Today AegisLM becomes a **model benchmarking platform**, not just a single-run analyzer.

We will:

* Visualize baseline vs adversarial robustness
* Display delta robustness per model
* Rank models by robustness stability
* Show vulnerability index comparison
* Add benchmark selection UI
* Enable model-level drilldown

---

# 1️⃣ Architectural Extension

We now use:

```
experiments/benchmarks/{benchmark_id}.json
```

Dashboard must support:

```
Benchmark Selector
    ↓
Load benchmark artifact
    ↓
Generate comparison visuals
```

---

# 2️⃣ Data Flow for Benchmark Comparison

```
User selects benchmark_id
        ↓
DataLoader.get_model_comparison(benchmark_id)
        ↓
Extract:
  - baseline_score
  - adversarial_score
  - delta
  - RSI
  - vulnerability index
        ↓
Generate:
  - Bar chart (ΔR)
  - Ranking table
  - Stability chart
```

---

# 3️⃣ Mathematical Definitions (Reinforced)

For each model ( m ):

---

### Baseline Robustness

[
R_{base}^{(m)}
]

---

### Adversarial Robustness

[
R_{adv}^{(m)}
]

---

### Delta Robustness

[
\Delta R^{(m)} = R_{base}^{(m)} - R_{adv}^{(m)}
]

---

### Robustness Stability Index (RSI)

[
RSI^{(m)} = \frac{R_{adv}^{(m)}}{R_{base}^{(m)}}
]

Closer to 1 = stable.

---

### Vulnerability Index

[
VI^{(m)} = \frac{\Delta R^{(m)}}{R_{base}^{(m)}}
]

Higher = more fragile.

---

# 4️⃣ Dashboard Module Updates

Add:

```
dashboard/
└── components/
    ├── model_comparison_chart.py
    ├── ranking_table.py
    ├── delta_bar_chart.py
```

---

# 5️⃣ Benchmark Data Loader

Update `data_loader.py`:

```python
def get_model_comparison(benchmark_id):
```

Load artifact:

```
experiments/benchmarks/{benchmark_id}.json
```

Return structured list:

```python
[
  {
    model,
    baseline,
    adversarial,
    delta,
    RSI,
    VI
  }
]
```

---

# 6️⃣ Delta Robustness Bar Chart

File: `delta_bar_chart.py`

Plot:

* X-axis = model names
* Y-axis = ΔR

Formula used:

[
\Delta R^{(m)}
]

Color scale:

* Green → low delta (robust)
* Red → high delta (fragile)

Fix Y range [0,1].

---

# 7️⃣ Ranking Table Component

Sort models by:

1️⃣ Highest adversarial robustness
2️⃣ Lowest vulnerability index

Ranking rule:

Primary key:

[
Sort = R_{adv}
]

Secondary key:

[
Sort = -VI
]

Display:

| Rank | Model | R_base | R_adv | ΔR | RSI | VI |

---

# 8️⃣ Stability Visualization (Optional but Recommended)

Add second chart:

Plot:

[
(R_{base}, R_{adv})
]

Each model as a point.

Line:

[
y = x
]

Closer to diagonal → stable.

---

# 9️⃣ UI Integration

Add new tab:

```
Tab: Benchmark Comparison
```

Layout:

```
Benchmark Selector Dropdown
Delta Robustness Chart
Stability Scatter Plot
Ranking Table
```

Populate dropdown from:

```
SELECT benchmark_id FROM benchmarks ORDER BY timestamp DESC
```

---

# 🔟 Statistical Display

Display:

* Mean robustness
* Std deviation across models
* Best model
* Most vulnerable model

Optional:

Confidence interval (if multiple runs per model later).

---

# 11️⃣ Performance Considerations

* Benchmark artifacts relatively small.
* Avoid recomputation.
* Cache loaded artifact in memory.
* No DB-heavy queries needed here.

---

# 12️⃣ Logging

Log:

```
DASHBOARD_VIEW_BENCHMARK
{
  benchmark_id
}
```

Log:

```
DASHBOARD_COMPARE_MODELS
{
  benchmark_id,
  model_count
}
```

---

# 13️⃣ Risks

* Misleading ranking due to small dataset.
* Overinterpretation of ΔR without context.
* Model fairness differences not visible in aggregate score.
* Cross-model hardware differences affecting confidence.

Mitigation:

* Show dataset version prominently.
* Show sample size.
* Add warning if N < threshold.

---

# 14️⃣ Documentation Updates

Update:

`docs/benchmarks.md`

Add:

* Cross-model comparison explanation
* RSI formula
* Vulnerability index formula
* Ranking methodology

Update:

`docs/blog.md` outline:

Add section:

> Benchmarking LLM Robustness: Beyond Raw Accuracy

---

# 15️⃣ Validation Criteria

Day 4 complete if:

* Benchmark selector dropdown functional.
* Delta bar chart renders correctly.
* Stability scatter plot renders correctly.
* Ranking table correctly sorted.
* RSI and VI computed correctly.
* No raw outputs exposed.
* Dashboard responsive under multiple models.

---

# 📦 Deliverables

1. Cross-model comparison implemented
2. Delta robustness chart working
3. Stability scatter plot working
4. Ranking table implemented
5. RSI + VI computed
6. UI integrated
7. Documentation updated

---


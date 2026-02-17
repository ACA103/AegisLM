# ✅ Week 3 – Day 3

---

## Objective

Implement the **Attack Vulnerability Heatmap + Per-Attack Metric Breakdown**.

This converts AegisLM from a simple evaluation viewer into a **vulnerability intelligence system**.

Today we:

* Build per-attack metric aggregation
* Compute vulnerability matrix
* Implement Plotly heatmap
* Add attack-level drilldown table
* Integrate into dashboard

---

# 1️⃣ Conceptual Goal

Instead of only:

> “Model robustness = 0.73”

We now answer:

> “Model fails most under jailbreak + context poisoning due to hallucination spike.”

This is governance insight.

---

# 2️⃣ Mathematical Formulation

For each attack type ( a ):

Let:

[
H_a = mean(H_i | attack=a)
]
[
T_a = mean(T_i | attack=a)
]
[
B_a = mean(B_i | attack=a)
]
[
C_a = mean(C_i | attack=a)
]

Vulnerability matrix:

[
M_a = [H_a, T_a, B_a, 1 - C_a]
]

We use:

* Hallucination (direct vulnerability)
* Toxicity (direct vulnerability)
* Bias (direct vulnerability)
* Confidence collapse = (1 - C_a)

All normalized [0,1].

---

# 3️⃣ Heatmap Structure

Rows = Attack Types
Columns = Metrics

Example:

| Attack Type  | Hallucination | Toxicity | Bias | Confidence Collapse |
| ------------ | ------------- | -------- | ---- | ------------------- |
| Jailbreak    | 0.72          | 0.81     | 0.30 | 0.40                |
| Injection    | 0.60          | 0.45     | 0.20 | 0.33                |
| Bias Trigger | 0.40          | 0.20     | 0.78 | 0.25                |

Color scale:

* Green → low vulnerability
* Yellow → medium
* Red → high

---

# 4️⃣ Data Aggregation Layer

Update `dashboard/data_loader.py`

Add:

```python
def get_attack_heatmap(run_id) -> HeatmapData
```

SQL aggregation:

```sql
SELECT attack_type,
       AVG(hallucination),
       AVG(toxicity),
       AVG(bias),
       AVG(confidence)
FROM evaluation_results
WHERE run_id = ...
GROUP BY attack_type
```

Post-process:

```
confidence_collapse = 1 - avg_confidence
```

Return structured HeatmapData.

---

# 5️⃣ Heatmap Component

File: `components/heatmap.py`

Use Plotly:

```python
go.Heatmap(
    z=values,
    x=metric_names,
    y=attack_types,
    colorscale='RdYlGn_r'
)
```

Important:

* Reverse color scale so red = high vulnerability
* Fix value range [0,1]

---

# 6️⃣ Per-Attack Drilldown Panel

Add component:

```
components/attack_breakdown.py
```

Displays table:

For selected attack:

* Sample count
* Mean hallucination
* Mean toxicity
* Mean bias
* Mean confidence
* Robustness under this attack

Compute robustness per attack:

[
R_a = w_1(1-H_a) + w_2(1-T_a) + w_3(1-B_a) + w_4 C_a
]

---

# 7️⃣ UI Integration

Update `app.py`:

Under Evaluation Runs tab:

```
Run Selector
Radar Chart
Metrics Panel
Heatmap
Attack Breakdown Dropdown
Attack Breakdown Table
```

Flow:

1. User selects run
2. Radar + heatmap update
3. User selects attack
4. Breakdown table updates

---

# 8️⃣ Vulnerability Index per Attack

Define:

[
VI_a = \frac{R_{base,a} - R_{adv,a}}{R_{base,a}}
]

(If baseline available)

If no baseline:

[
VI_a = 1 - R_a
]

Display in breakdown table.

---

# 9️⃣ Logging Requirements

Log:

```
DASHBOARD_VIEW_HEATMAP
{
  run_id
}
```

Log:

```
DASHBOARD_VIEW_ATTACK_BREAKDOWN
{
  run_id,
  attack_type
}
```

---

# 🔟 Performance Considerations

* Use SQL GROUP BY (not Python loops).
* Cache heatmap data per run.
* Avoid recomputing on every dropdown change.
* Do not load raw outputs.

---

# 11️⃣ Edge Cases

If:

* Only one attack type → still render heatmap
* Missing metric → show 0, log warning
* Very small sample size (<3) → display warning

---

# 12️⃣ Governance Interpretation Layer

Add hover tooltip explanation:

For hallucination:

> “High value indicates increased factual instability under this attack.”

For confidence collapse:

> “High value indicates model uncertainty increase.”

---

# 13️⃣ Documentation Updates

Update:

`docs/architecture.md`

Add:

```
Vulnerability Analysis Layer
  - Per-attack aggregation
  - Vulnerability heatmap
  - Attack robustness computation
```

Update:

`docs/blog.md` outline:

Add section:

> From Metrics to Vulnerabilities: Heatmap-Based Risk Intelligence

---

# 14️⃣ Risks

* Misinterpretation of color scale.
* Attack imbalance skewing results.
* Heatmap too sparse for small datasets.
* Overloaded UI.

Mitigation:

* Include legend.
* Show sample count per attack.
* Normalize per attack.

---

# 15️⃣ Validation Criteria

Day 3 complete if:

* Heatmap renders correctly.
* Values match DB aggregation.
* Attack breakdown table functional.
* Robustness per attack computed correctly.
* UI responsive.
* No raw outputs exposed.
* Logs recorded correctly.

---

# 📦 Deliverables

1. Heatmap implemented
2. Per-attack breakdown table implemented
3. Aggregation queries optimized
4. Confidence collapse metric added
5. UI integrated
6. Vulnerability index computed
7. Documentation updated

---


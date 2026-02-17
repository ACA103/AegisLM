# AegisLM Live Demo Script

This document provides the live demo script for AegisLM presentations. It is deterministic and clean.

---

## Demo Flow

### Step 1 — Show Problem

**Narrative:**
"Large Language Models are increasingly deployed in production, but they remain vulnerable to adversarial manipulation. Traditional static benchmarks miss this degradation. Let me show you what I mean."

**Display:**
- Explain briefly:
  * Static benchmarks miss adversarial degradation
  * Need multi-agent adversarial evaluation

**Transition:**
"Let's start by running a baseline evaluation to see how the model performs under normal conditions."

---

### Step 2 — Run Baseline Evaluation

**Action:**
1. Select model from dropdown (e.g., gpt-4)
2. Select dataset (e.g., truthfulqa)
3. Click "Run Baseline Evaluation"

**Display:**
- Clean prompts processed
- Composite robustness score displayed (R = 0.85)
- Radar chart showing:
  * Hallucination: 0.12
  * Toxicity: 0.08
  * Bias: 0.10
  * Confidence: 0.85

**Narrative:**
"Under baseline conditions, this model achieves a robustness score of 0.85. The radar chart shows balanced performance across all safety dimensions."

**Highlight:**
- Hallucination score
- Bias score
- Confidence stability

**Transition:**
"Now let's see what happens when we enable adversarial attacks."

---

### Step 3 — Run Adversarial Evaluation

**Action:**
1. Enable attack types:
   - Jailbreak: ON
   - Prompt injection: ON
2. Set mutation depth = 2
3. Click "Run Adversarial Evaluation"

**Display:**
- Attack prompts generated
- Mutation engine obfuscates attacks
- Model responses evaluated

**Result:**
- Drop in robustness score (R = 0.62)
- Heatmap shows vulnerability changes
- Per-attack breakdown displayed

**Narrative:**
"Under adversarial conditions, the robustness score drops from 0.85 to 0.62 — that's a 23% degradation. The heatmap shows which attack types cause the most damage."

**Transition:**
"Let's quantify this degradation precisely."

---

### Step 4 — Show Delta Robustness

**Action:**
Click "Show Delta Analysis"

**Display:**
```
ΔR = R_base - R_adv = 0.85 - 0.62 = 0.23
```

**Narrative:**
"Delta Robustness of 0.23 tells us the model loses 23% of its robustness under adversarial attack. Looking at the per-attack breakdown, we can see that jailbreak attacks cause the most degradation."

**Highlight:**
- Which attack type caused most degradation
- Visualization of the drop

**Transition:**
(Optional) "We can also compare multiple models to see which is most resilient."

---

### Step 5 — Cross-Model Benchmark (Optional)

**Action:**
1. Select multiple models (e.g., gpt-4, claude-3, llama-2)
2. Click "Run Comparison"

**Display:**
- Ranking table:
  | Rank | Model | R_adv | RSI | VI |
  |------|-------|-------|-----|-----|
  | 1 | gpt-4 | 0.72 | 0.89 | 0.11 |
  | 2 | claude-3 | 0.68 | 0.85 | 0.15 |
  | 3 | llama-2 | 0.55 | 0.75 | 0.25 |

- RSI (Robustness Stability Index) for each model
- Vulnerability Index (VI) for each model

**Narrative:**
"This comparison shows gpt-4 is the most robust under adversarial conditions, while llama-2 shows the highest vulnerability."

**Transition:**
"Finally, let's export a governance report for compliance purposes."

---

### Step 6 — Export Governance Report

**Action:**
1. Click "Export Report"
2. Select format (JSON)
3. Save file

**Display:**
Open the JSON file and show:
```
json
{
  "report_id": "sha256_hash",
  "generated_at": "2024-01-15T10:30:00Z",
  "model": {
    "name": "gpt-4",
    "version": "v1.0"
  },
  "dataset": {
    "name": "truthfulqa",
    "version": "v1.0",
    "checksum": "sha256..."
  },
  "config_hash": "sha256...",
  "composite_score": {
    "baseline": 0.85,
    "adversarial": 0.62,
    "delta": 0.23
  },
  "mean_metrics": {
    "hallucination": 0.12,
    "toxicity": 0.08,
    "bias": 0.10,
    "confidence": 0.85
  },
  "per_attack": [
    {"attack": "jailbreak", "robustness": 0.55},
    {"attack": "injection", "robustness": 0.68}
  ],
  "integrity": {
    "acs": 1,
    "ris": 1
  }
}
```

**Narrative:**
"This report includes everything auditors need: model version, dataset version, config hash for reproducibility, composite scores, and per-attack breakdowns. The integrity scores confirm the mathematical validity of all computations."

**Emphasis:**
- Auditability
- Reproducibility
- Config hash for verification
- Dataset version for provenance

---

## Demo Summary

This demo showcases:

1. **Baseline Evaluation**: Clean prompt robustness measurement
2. **Adversarial Evaluation**: Stress testing under attack conditions
3. **Delta Robustness**: Quantified degradation metric
4. **Cross-Model Comparison**: Fair model ranking
5. **Governance Reporting**: Audit-ready JSON exports

---

## Quick Reference

| Demo Step | Action | Key Metric |
|-----------|--------|------------|
| 1. Show Problem | Context setting | N/A |
| 2. Baseline | Run clean eval | R = 0.85 |
| 3. Adversarial | Run attack eval | R = 0.62 |
| 4. Delta | Show degradation | ΔR = 0.23 |
| 5. Compare | Multi-model | Ranking table |
| 6. Export | Generate JSON | Config hash |

---

*Last Updated: 2024*

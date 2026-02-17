# ✅ Week 4 – Day 3

---

## Objective

Complete `docs/benchmarks.md` — the **formal benchmarking protocol and reproducibility specification** for AegisLM.

This document must define:

* Dataset strategy
* Dataset versioning
* Sampling methodology
* Baseline vs adversarial evaluation protocol
* Cross-model comparison rules
* Fairness and reproducibility constraints
* Statistical reporting
* Benchmark artifact structure
* Experimental integrity guarantees

This is the governance backbone of the framework.

---

# 📂 File: `docs/benchmarks.md`

Below is the structured content that must be implemented.

---

# 1️⃣ Benchmarking Philosophy

AegisLM benchmarks are designed to measure:

1. **Robustness degradation under adversarial stress**
2. **Safety stability**
3. **Bias amplification under attack**
4. **Confidence collapse**
5. **Cross-model resilience comparison**

Benchmarks must be:

* Deterministic
* Reproducible
* Version-controlled
* Audit-traceable

---

# 2️⃣ Dataset Strategy

Datasets are categorized into:

---

## 2.1 Factual Evaluation Datasets

Purpose:
Measure hallucination behavior.

Examples:

* TruthfulQA-style datasets
* Custom factual QA corpus

Schema:

```
{
  sample_id,
  prompt,
  ground_truth,
  category: "factual"
}
```

Ground truth required.

---

## 2.2 Safety Evaluation Datasets

Purpose:
Measure toxicity and policy violations.

Schema:

```
{
  sample_id,
  prompt,
  category: "safety"
}
```

Ground truth optional.

---

## 2.3 Synthetic Adversarial Datasets

Generated via mutation engine.

Schema:

```
{
  sample_id,
  base_prompt,
  mutated_prompt,
  mutation_trace,
  category: "synthetic"
}
```

Includes mutation metadata.

---

# 3️⃣ Dataset Versioning Protocol

Each processed dataset version includes:

```
manifest.json
```

Fields:

* dataset_name
* version
* checksum
* preprocessing_steps
* num_samples
* evaluation_config

---

## 3.1 Checksum Definition

[
checksum = SHA256(serialized_dataset)
]

Checksum stored in:

* manifest.json
* database
* benchmark artifact

If mismatch → benchmark aborts.

---

# 4️⃣ Sampling Methodology

Sampling must be deterministic.

Seed:

[
seed = hash(run_id + dataset_version)
]

Sampling strategies:

* Full dataset
* Stratified by category
* Fixed N random sample

Sampling metadata logged.

---

# 5️⃣ Baseline Evaluation Protocol

Baseline evaluation disables:

* Attacker agent
* Mutation engine

Pipeline:

```
Prompt → Model → Defender → Judge → Score
```

Purpose:

Measure intrinsic robustness.

---

# 6️⃣ Adversarial Evaluation Protocol

Adversarial evaluation enables:

* Attacker agent
* Mutation engine
* Multi-turn chaining

Pipeline:

```
Prompt → Attack → Mutation → Model → Defender → Judge → Score
```

Purpose:

Measure robustness degradation.

---

# 7️⃣ Benchmark Execution Rules

For each model ( m ):

1. Run baseline evaluation.
2. Run adversarial evaluation.
3. Compute:

[
R_{base}^{(m)}
]
[
R_{adv}^{(m)}
]
[
\Delta R^{(m)}
]
[
RSI^{(m)}
]
[
VI^{(m)}
]

4. Store benchmark artifact.

---

# 8️⃣ Cross-Model Comparison Rules

To ensure fairness:

* Same dataset version
* Same sampling seed
* Same attack configuration
* Same mutation depth
* Same scoring weights

Any change invalidates comparison.

Comparison invalid if:

[
config_hash_1 \ne config_hash_2
]

---

# 9️⃣ Fairness & Reproducibility Constraints

A benchmark is valid only if:

* Dataset checksum matches
* Model version logged
* Config hash stored
* Policy version stored
* Weights validated

All parameters must be included in artifact.

---

# 🔟 Statistical Reporting

Each benchmark must include:

---

## 10.1 Mean Metrics

[
\bar{H}, \bar{T}, \bar{B}, \bar{C}
]

---

## 10.2 Standard Deviation

[
\sigma_H, \sigma_T, \sigma_B, \sigma_C
]

---

## 10.3 Delta Robustness

[
\Delta R = R_{base} - R_{adv}
]

---

## 10.4 Robustness Stability Index

[
RSI = \frac{R_{adv}}{R_{base}}
]

---

## 10.5 Vulnerability Index

[
VI = \frac{\Delta R}{R_{base}}
]

---

# 11️⃣ Per-Attack Analysis

For each attack ( a ):

[
H_a, T_a, B_a, C_a
]

[
R_a = w_1(1-H_a) + w_2(1-T_a) + w_3(1-B_a) + w_4 C_a
]

Used for:

* Heatmap
* Vulnerability ranking

---

# 12️⃣ Benchmark Artifact Schema

```
{
  benchmark_id,
  dataset_version,
  config_hash,
  models: [
    {
      model_name,
      baseline_score,
      adversarial_score,
      delta_robustness,
      RSI,
      VI,
      std_dev,
      sample_count
    }
  ],
  ranking,
  timestamp
}
```

---

# 13️⃣ Model Ranking Methodology

Ranking priority:

1. Highest adversarial robustness
2. Lowest vulnerability index
3. Lowest hallucination under attack

Sorting rule:

Primary key:

[
R_{adv}
]

Secondary key:

[

* VI
  ]

---

# 14️⃣ Experimental Integrity Rules

A benchmark must abort if:

* Dataset checksum mismatch
* Weight sum ≠ 1
* Metric out of range
* Missing model version
* Missing dataset version

---

# 15️⃣ Limitations of Benchmark Protocol

* Small dataset size may bias ranking
* Embedding-based hallucination proxy imperfect
* Toxicity classifier bias
* No human evaluation layer
* Single-run variance not captured

Document explicitly.

---

# 16️⃣ Validation Criteria

Day 3 complete if:

* benchmarks.md fully written
* Dataset strategy clearly documented
* Baseline vs adversarial protocol defined
* Cross-model fairness constraints included
* Artifact schema defined
* Ranking methodology documented
* Integrity rules documented
* Limitations documented

---

# 📦 Deliverables

1. `docs/benchmarks.md` completed
2. Reproducibility protocol documented
3. Fairness constraints defined
4. Ranking methodology defined
5. Artifact schema defined
6. Integrity rules included
7. Limitations included

---



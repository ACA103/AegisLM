# ✅ Week 2 – Day 2

---

## Objective

Design and implement the **Dataset Ingestion & Versioning Pipeline**.

This is critical for:

* Reproducibility
* Benchmark integrity
* Dataset hashing
* Version control
* Synthetic adversarial augmentation
* Clean separation of raw vs processed data

AegisLM must treat datasets like production artifacts — not CSV files thrown into a folder.

---

# 1️⃣ Architectural Role

Dataset flow:

```
datasets/raw/
        ↓
Preprocessing Pipeline
        ↓
datasets/processed/{version}/
        ↓
Dataset Manifest (JSON)
        ↓
DB Registration
        ↓
Evaluation Orchestrator
```

---

# 2️⃣ Folder Structure

Refine:

```
datasets/
│
├── raw/
│   ├── truthfulqa/
│   ├── advbench/
│   └── safetybench/
│
├── processed/
│   ├── v1/
│   │   ├── data.json
│   │   └── manifest.json
│
└── registry/
    └── dataset_registry.json
```

---

# 3️⃣ Dataset Types

AegisLM must support 3 dataset categories:

---

## 1️⃣ Factual QA Datasets

Examples:

* TruthfulQA
* Custom QA corpus

Schema:

```json
{
  "sample_id": "...",
  "prompt": "...",
  "ground_truth": "...",
  "category": "factual"
}
```

---

## 2️⃣ Safety Challenge Datasets

Examples:

* Jailbreak prompts
* Harmful intent prompts

Schema:

```json
{
  "sample_id": "...",
  "prompt": "...",
  "category": "safety"
}
```

Ground truth optional.

---

## 3️⃣ Synthetic Adversarial Dataset

Generated via mutation engine.

Schema:

```json
{
  "sample_id": "...",
  "base_prompt": "...",
  "mutated_prompt": "...",
  "mutation_trace": [...],
  "category": "synthetic"
}
```

---

# 4️⃣ Dataset Versioning Strategy

Each processed dataset version must include:

```
manifest.json
```

Structure:

```json
{
  "dataset_name": "truthfulqa",
  "version": "v1.0",
  "source": "official",
  "num_samples": 817,
  "preprocessing_steps": [
      "lowercase normalization",
      "whitespace cleanup"
  ],
  "created_at": "...",
  "checksum": "sha256_hash"
}
```

---

# 5️⃣ Checksum Strategy

Checksum must be computed over:

* Sorted JSON content
* Deterministic serialization

[
checksum = SHA256(serialized_dataset)
]

Store checksum in:

* manifest.json
* database dataset_versions table

Ensures no silent modification.

---

# 6️⃣ Dataset Registry System

File: `datasets/registry/dataset_registry.json`

Structure:

```json
{
  "truthfulqa": {
    "latest_version": "v1.0",
    "available_versions": ["v1.0"]
  }
}
```

Allows orchestrator to fetch correct version.

---

# 7️⃣ Preprocessing Pipeline

Create module:

```
backend/core/dataset_loader.py
```

Functions:

```python
load_raw_dataset(name)
preprocess_dataset(raw_data)
save_processed_dataset(version)
compute_checksum()
register_dataset()
```

---

## Deterministic Preprocessing Rules

* Strip whitespace
* Normalize encoding
* Ensure unique sample IDs
* Remove duplicates
* Standardize schema fields

No randomness allowed.

---

# 8️⃣ Dataset Sampling Strategy

Allow:

* Full evaluation
* Stratified sampling
* Category-based selection

Sampling must log:

```
{
  sampling_method,
  sample_size,
  seed
}
```

Sampling seed:

[
seed = hash(run_id + dataset_version)
]

Ensures reproducibility.

---

# 9️⃣ Benchmarking Preparation

Each dataset must define:

* Hallucination threshold
* Bias threshold
* Toxicity threshold
* Evaluation mode (factual vs safety)

Add to manifest:

```json
"evaluation_config": {
  "hallucination_threshold": 0.5,
  "toxicity_threshold": 0.6,
  "bias_threshold": 0.5
}
```

---

# 🔟 Evaluation Dataset Interface

Define interface in orchestrator:

```python
class EvaluationDataset:
    def __iter__(self)
    def get_ground_truth(sample_id)
    def metadata()
```

Ensures Judge can access ground truth when available.

---

# 11️⃣ Synthetic Dataset Generation Pipeline

Allow mutation engine to generate synthetic dataset:

Flow:

```
Base dataset
    ↓
Mutation engine
    ↓
Synthetic dataset version
```

Store:

```
datasets/processed/v1_synthetic/
```

Must store:

* Base dataset version
* Mutation parameters
* Diversity mean
* Mutation depth

---

# 12️⃣ Metrics Introduced Today

### Dataset Integrity Score

Binary:

[
DIS = 1 \quad \text{if checksum matches manifest}
]

Else fail run.

---

### Category Coverage

[
Coverage = \frac{\text{Samples in category}}{\text{Total samples}}
]

Ensures balanced benchmark.

---

# 13️⃣ Logging Requirements

On dataset load:

```
{
  dataset_name,
  version,
  checksum,
  num_samples,
  sampling_method
}
```

If checksum mismatch → ERROR + abort.

---

# 14️⃣ Performance Considerations

* Load dataset into memory once.
* Avoid repeated disk reads.
* Cache dataset per run.
* Use streaming only for large datasets.

HF Spaces constraint:

* Keep dataset size reasonable (< few thousand samples initially).

---

# 15️⃣ Risks

* Dataset license issues.
* Corrupted raw files.
* Non-deterministic preprocessing.
* Sampling bias.

Mitigation:

* Checksum enforcement.
* Strict preprocessing rules.
* Dataset documentation in `benchmarks.md`.

---

# 16️⃣ Documentation Updates

Update:

`docs/benchmarks.md`:

* Dataset descriptions
* Versioning strategy
* Checksum explanation
* Sampling methodology

---

# 17️⃣ Validation Criteria

Day 2 complete if:

* Raw dataset ingested.
* Processed dataset version created.
* Manifest JSON generated.
* Checksum verified.
* Dataset registered in DB.
* Orchestrator loads dataset deterministically.
* Sampling reproducible.

---

# 📦 Deliverables

1. Dataset ingestion pipeline implemented
2. Versioned processed dataset created
3. Manifest JSON created
4. Dataset checksum validation working
5. Dataset registry updated
6. Orchestrator loads dataset successfully
7. Documentation updated

---


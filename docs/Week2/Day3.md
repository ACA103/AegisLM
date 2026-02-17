# ✅ Week 2 – Day 3

---

## Objective

Implement the **Full Evaluation Pipeline Integration**:

> attack → mutation → model → defender → judge → scoring → persistence

Today we:

* Convert skeleton orchestrator into production-grade async pipeline
* Implement evaluation run lifecycle
* Add concurrency control
* Add structured persistence
* Enforce determinism & version tagging
* Add failure handling & recovery logic

This is where AegisLM becomes a real system.

---

# 1️⃣ Final Evaluation Flow (Production)

```
Create Run
    ↓
Load Dataset (version-locked)
    ↓
For each sample (async controlled):
    1. Attack
    2. Mutation
    3. Model Execution
    4. Defender
    5. Judge
    6. Persist Result
    ↓
Aggregate Metrics
    ↓
Compute Composite Robustness
    ↓
Store Artifact JSON
    ↓
Update Run Status
```

---

# 2️⃣ Orchestrator Redesign

File: `backend/core/orchestrator.py`

We replace stub with:

### EvaluationOrchestrator Class

```python
class EvaluationOrchestrator:
    async def run_evaluation(self, run_config: RunConfig)
```

---

# 3️⃣ Run Lifecycle State Machine

Add states to DB:

```
CREATED
RUNNING
FAILED
COMPLETED
```

Transitions:

* CREATED → RUNNING
* RUNNING → COMPLETED
* RUNNING → FAILED (on fatal error)

Non-fatal sample-level failures logged, not aborting run.

---

# 4️⃣ Concurrency Strategy

HF Spaces constraint:

* Limited GPU memory.

Decision:

* Use bounded concurrency.
* Max concurrent samples = configurable (default 2–4).

Implementation:

```python
semaphore = asyncio.Semaphore(config.max_concurrency)
```

Ensures controlled parallelism.

---

# 5️⃣ Deterministic Run Configuration

Define:

```python
class RunConfig(BaseModel):
    run_id: UUID
    model_name: str
    model_version: str
    dataset_name: str
    dataset_version: str
    weights: Dict[str, float]
    mutation_depth: int
    attack_types: List[str]
    sampling_config: Dict
```

Hash config:

[
config_hash = SHA256(sorted(json(config)))
]

Store in evaluation_runs table.

---

# 6️⃣ Full Sample Execution Flow (Detailed)

Inside orchestrator:

```python
async def process_sample(sample):
    attack_output = attacker.execute(...)
    mutation_output = mutation_engine.mutate(...)
    model_output = model_executor.generate(...)
    defender_output = defender.evaluate(...)
    judge_output = judge.evaluate(...)
    persist_result(...)
```

All intermediate metadata passed forward.

---

# 7️⃣ Failure Handling Design

Three failure types:

---

## 1️⃣ Attack Failure

If mutation invalid:

* Log
* Skip sample
* Continue

---

## 2️⃣ Model Inference Failure

Retry logic:

[
max_retries = 2
]

If still fails:

* Mark sample FAILED
* Continue

---

## 3️⃣ Critical Failure

Examples:

* Dataset checksum mismatch
* Model load failure

→ Abort run
→ Status = FAILED

---

# 8️⃣ Persistence Strategy

For each sample:

Insert into `evaluation_results`:

```
run_id
sample_id
attack_type
mutation_trace
hallucination
toxicity
bias
confidence
robustness
raw_output
latency_ms
```

No batching.
Each sample persisted independently.

---

# 9️⃣ Aggregate Metrics Computation

After all samples processed:

Compute:

---

### Mean Hallucination

[
\bar{H} = \frac{1}{N} \sum H_i
]

---

### Mean Toxicity

[
\bar{T} = \frac{1}{N} \sum T_i
]

---

### Mean Bias

[
\bar{B} = \frac{1}{N} \sum B_i
]

---

### Mean Confidence

[
\bar{C} = \frac{1}{N} \sum C_i
]

---

### Final Robustness Score

[
R = w_1(1 - \bar{H}) + w_2(1 - \bar{T}) + w_3(1 - \bar{B}) + w_4 \bar{C}
]

Store in `evaluation_runs.composite_score`.

---

# 🔟 Artifact Storage

At run completion:

Create:

```
experiments/runs/{run_id}.json
```

Structure:

```json
{
  "run_id": "...",
  "config": {...},
  "dataset_version": "...",
  "model_version": "...",
  "aggregate_metrics": {...},
  "per_sample_summary": {
      "mean_latency_ms": ...,
      "attack_success_rate": ...
  }
}
```

Store only summaries, not full raw outputs (to limit size).

---

# 11️⃣ Performance Tracking

Track per sample:

* latency_ms
* tokens_generated
* attack_chain_depth
* mutation_depth

Compute:

---

### Mean Latency

[
ML = \frac{1}{N} \sum latency_i
]

---

### Throughput

[
Throughput = \frac{N}{TotalTime}
]

---

### Failure Rate

[
FR = \frac{FailedSamples}{TotalSamples}
]

Store in run metadata.

---

# 12️⃣ Observability Enhancements

Add run-level logs:

```
RUN_STARTED
SAMPLE_COMPLETED
SAMPLE_FAILED
RUN_COMPLETED
RUN_FAILED
```

Each log contains run_id + timestamp.

---

# 13️⃣ Benchmarking Foundations

Today we enable:

* Baseline evaluation (no attack)
* Adversarial evaluation
* Delta robustness

Delta robustness:

[
\Delta R = R_{baseline} - R_{adversarial}
]

Will be computed later in benchmarking module.

---

# 14️⃣ Scalability Considerations

HF Spaces GPU constraint:

* Single model loaded
* Avoid reloading between samples
* Lazy load on first call
* Clear GPU cache periodically if needed

Future scaling:

* Microservice separation possible
* Redis queue for distributed runs

---

# 15️⃣ Documentation Updates

Update:

`docs/architecture.md`:

* Add evaluation lifecycle diagram
* Add state machine
* Add concurrency design

Update:

`docs/math.md`:

* Add aggregate metric formulas
* Add delta robustness formula

---

# 16️⃣ Risks

* Memory leak during long runs
* Async deadlocks
* DB connection exhaustion
* Large artifact files

Mitigation:

* Use connection pooling
* Close sessions properly
* Limit artifact size
* Monitor memory

---

# 17️⃣ Validation Criteria

Day 3 complete if:

* Full pipeline runs end-to-end.
* Results stored per sample.
* Composite score computed.
* Artifact JSON created.
* Run status transitions correct.
* Concurrency works.
* No memory spike.

---

# 📦 Deliverables

1. Orchestrator fully implemented
2. End-to-end evaluation working
3. DB persistence verified
4. Artifact generation working
5. Aggregate metrics implemented
6. Concurrency control implemented
7. Logging lifecycle implemented

---


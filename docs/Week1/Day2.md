# ✅ Week 1 – Day 2

---

## Objective

Design and implement the **backend core infrastructure layer**.

Today we establish:

* FastAPI service structure
* Async execution pipeline
* Config system
* Model abstraction layer
* Database schema (PostgreSQL)
* Structured logging framework
* Evaluation run lifecycle design

No agents yet.
We build the execution backbone.

---

# 1️⃣ Backend Architectural Decisions

### Decision 1: No Monolithic Pipeline

Instead of:

```
attack → model → defend → judge (inline chain)
```

We implement:

```
Evaluation Orchestrator (async)
    ├── Attacker
    ├── Model Executor
    ├── Defender
    ├── Judge
    └── Scoring Aggregator
```

Orchestrator controls lifecycle.

---

### Decision 2: Strict Typed Schemas

All agent I/O must use Pydantic models.

No raw dict passing.

---

### Decision 3: Stateless API

* API is stateless.
* All evaluation state stored in DB.
* Artifacts stored in `/experiments/runs/`.

---

# 2️⃣ Folder Implementation (Backend Layer)

Refine structure:

```
backend/
│
├── api/
│   ├── routes.py
│   └── dependencies.py
│
├── core/
│   ├── orchestrator.py
│   ├── model_registry.py
│   ├── config.py
│   └── exceptions.py
│
├── db/
│   ├── models.py
│   ├── session.py
│   └── migrations/
│
├── logging/
│   ├── logger.py
│   └── schema.py
│
├── scoring/
│   └── aggregator.py
│
└── main.py
```

Deliverable: Folder created.

---

# 3️⃣ Database Schema Design (PostgreSQL)

We design 4 core tables.

---

## Table 1: evaluation_runs

```sql
id UUID PRIMARY KEY
timestamp TIMESTAMP
model_name VARCHAR
model_version VARCHAR
dataset_version VARCHAR
status VARCHAR
config_hash VARCHAR
composite_score FLOAT
```

---

## Table 2: evaluation_results

```sql
id UUID PRIMARY KEY
run_id UUID REFERENCES evaluation_runs(id)
attack_type VARCHAR
mutation_type VARCHAR
hallucination FLOAT
toxicity FLOAT
bias FLOAT
confidence FLOAT
robustness FLOAT
raw_output TEXT
```

---

## Table 3: model_versions

```sql
model_name VARCHAR
model_version VARCHAR
parameters JSONB
checksum VARCHAR
```

---

## Table 4: dataset_versions

```sql
dataset_name VARCHAR
version VARCHAR
checksum VARCHAR
metadata JSONB
```

---

## Engineering Decision

* Use SQLAlchemy ORM.
* Async engine (`asyncpg`).
* Use Alembic for migrations.

---

# 4️⃣ Evaluation Lifecycle Design

Define full lifecycle:

```
1. Create evaluation_run
2. Load dataset
3. For each sample:
       → orchestrator.process()
       → store evaluation_result
4. Compute aggregate metrics
5. Update evaluation_run status + score
6. Persist artifact JSON
```

All operations async.

---

# 5️⃣ Model Abstraction Layer

We design a clean interface.

File: `core/model_registry.py`

### BaseModelExecutor

```python
class BaseModelExecutor:
    async def generate(self, prompt: str, temperature: float) -> ModelResponse:
        raise NotImplementedError
```

### ModelResponse Schema

```python
class ModelResponse(BaseModel):
    text: str
    token_probs: Optional[List[float]]
    metadata: Dict[str, Any]
```

---

### Concrete Implementation Example

* Llama executor
* Mistral executor

Each loads from HuggingFace Transformers.

---

## Engineering Tradeoff

Avoid using pipeline() for generation.
Use model.generate() for probability access.

We need logits for confidence.

---

# 6️⃣ Config System

File: `core/config.py`

We implement environment-driven config:

```python
class Settings(BaseSettings):
    database_url: str
    redis_url: Optional[str]
    default_model: str
    default_temperature: float
    hallucination_alpha: float
    hallucination_beta: float
```

Config hash generated per run:

[
config_hash = SHA256(sorted(config.items()))
]

Ensures experiment reproducibility.

---

# 7️⃣ Logging Framework

File: `logging/logger.py`

All logs structured JSON.

Log schema:

```json
{
  "timestamp": "...",
  "level": "INFO",
  "run_id": "...",
  "component": "orchestrator",
  "message": "...",
  "metadata": {}
}
```

Use Python `logging` with JSON formatter.

---

# 8️⃣ Orchestrator Skeleton

File: `core/orchestrator.py`

Responsibilities:

* Manage async pipeline
* Call agents in order
* Catch exceptions
* Aggregate scoring
* Emit logs

Pseudo-flow:

```python
async def process_sample(sample, config):
    attack_output = await attacker.run(sample)
    model_output = await model.generate(attack_output.prompt)
    defense_output = await defender.run(model_output)
    judge_scores = await judge.run(model_output)
    final_score = aggregator.compute(judge_scores)
    return EvaluationResult(...)
```

No implementation yet.
Just skeleton + TODO markers.

---

# 9️⃣ Composite Score Aggregator (Initial)

File: `scoring/aggregator.py`

Mathematical implementation:

[
R = w_1(1 - H) + w_2(1 - T) + w_3(1 - B) + w_4 C
]

Constraints:

[
\sum w_i = 1
]

Add validation:

* All metrics in [0,1]
* Raise error otherwise

---

# 🔟 Experiment Artifact Structure

On run completion:

Create file:

```
experiments/runs/{run_id}.json
```

Structure:

```json
{
  "run_id": "...",
  "model": "...",
  "dataset_version": "...",
  "config_hash": "...",
  "aggregate_metrics": {...},
  "per_sample_results": [...]
}
```

---

# 11️⃣ Observability Design

Track:

* Mean processing time per sample
* Throughput
* Failure rate
* Exception types
* Memory usage (optional logging)

Add:

```
metrics: {
    latency_ms,
    tokens_generated,
    attack_chain_depth
}
```

---

# 12️⃣ HuggingFace Spaces Deployment Constraints

Important:

* HF Spaces GPU memory limited.
* Avoid loading multiple 7B models simultaneously.
* Implement lazy loading.
* Allow model switching via config.

Dockerfile must:

* Pin transformer version
* Pre-cache model weights
* Use slim base image

---

## Deliverables (End of Day 2)

1. Backend folder created
2. Database schema written
3. SQLAlchemy models defined
4. Orchestrator skeleton created
5. Model abstraction layer defined
6. Logging framework initialized
7. Config system implemented
8. Composite scoring module stubbed

No agent logic yet.

---

## Engineering Notes

* Keep agents independent modules.
* Avoid circular imports.
* Enforce type hints strictly.
* No inline business logic inside routes.
* Use dependency injection for model executor.

---

## Risks

* Async DB misconfiguration
* HF model memory overload
* Poor logging discipline
* Hardcoded configs

Mitigation:

* Strict config management
* Memory monitoring
* Unit tests for aggregator

---

## Validation Criteria

Day 2 is complete if:

* FastAPI app boots without error.
* DB migrations apply successfully.
* Orchestrator skeleton compiles.
* Logging emits structured JSON.
* Config hash generated correctly.
* Composite score formula implemented with constraints.

---

I
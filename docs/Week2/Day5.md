# ✅ Week 2 – Day 5

---

## Objective

Harden AegisLM for **production deployment on HuggingFace Spaces**:

* Optimize performance (CPU + GPU)
* Prevent memory leaks
* Add resource monitoring
* Finalize Docker deployment
* Add CI/CD checks
* Add runtime validation & startup health checks

This is infrastructure hardening — not feature work.

---

# 1️⃣ Performance Optimization – Model Execution Layer

## Problem

* Large HF models consume high GPU memory
* Re-loading models causes OOM
* Repeated embedding calls expensive

---

## Actions

### 1️⃣ Lazy Model Loading

Modify `model_registry.py`:

* Models loaded on first request
* Stored in singleton cache
* Re-used for entire process lifecycle

```python
_MODEL_CACHE = {}

def get_model(model_name):
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = load_model(model_name)
    return _MODEL_CACHE[model_name]
```

---

### 2️⃣ Controlled GPU Memory Usage

After each generation:

```python
torch.cuda.empty_cache()
```

Add memory usage logging:

[
GPU_{used} = torch.cuda.memory_allocated()
]

Store per-run snapshot.

---

### 3️⃣ Mixed Precision Inference

Enable:

```
torch_dtype=torch.float16
```

Reduces memory usage significantly.

---

### 4️⃣ Token Probability Optimization

Avoid computing full probability matrix when not required.

* Only compute token_probs if confidence scoring enabled
* Controlled via config flag

---

# 2️⃣ Embedding & Mutation Optimization

## Problem

Embedding model called repeatedly.

---

## Actions

* Load SentenceTransformer once
* Cache embeddings per prompt

```python
embedding_cache[prompt_hash]
```

* Use LRU cache (max size configurable)

---

# 3️⃣ Async Concurrency Hardening

Add:

* Global semaphore
* Per-model semaphore
* DB connection pool size limit

Prevent:

* Deadlocks
* DB exhaustion
* GPU overload

---

# 4️⃣ Memory Monitoring

Add system metrics logger:

```
backend/logging/system_metrics.py
```

Log periodically:

* RAM usage
* GPU usage
* Active tasks
* DB connections

Example:

```json
{
  "memory_mb": 4200,
  "gpu_memory_mb": 7200,
  "active_tasks": 3
}
```

Logged every X seconds.

---

# 5️⃣ Docker Productionization

Create final `Dockerfile`:

### Key Decisions

* Use slim Python base image
* Install minimal dependencies
* Pin versions
* Pre-download models (optional for HF Spaces)
* Use non-root user

---

## Dockerfile Structure

```
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

HF Spaces expects port 7860.

---

# 6️⃣ HuggingFace Spaces Constraints Handling

## GPU Memory

* Only load one large model at a time.
* Clear cache between cross-model benchmarks.
* Allow model switch via restart.

---

## File System

HF ephemeral storage.

Mitigation:

* Artifacts stored temporarily.
* Optionally expose download endpoint.

---

# 7️⃣ Health Check Endpoint

Add route:

```
GET /health
```

Returns:

```json
{
  "status": "ok",
  "model_loaded": true,
  "db_connected": true,
  "dataset_loaded": false
}
```

Validation logic:

* DB ping
* Model registry accessible
* Config valid

---

# 8️⃣ Startup Validation Script

On app startup:

1. Validate environment variables
2. Validate DB connection
3. Validate policy.yaml
4. Validate dataset registry integrity
5. Validate checksum of latest dataset

Abort startup if failure.

---

# 9️⃣ CI/CD Preparation

Since HF Spaces auto-builds from GitHub:

Add:

```
.github/workflows/ci.yml
```

Steps:

* Install dependencies
* Run unit tests
* Validate Pydantic schemas
* Lint code (flake8)
* Validate math constraints (weights sum to 1)

Fail build if:

[
\sum w_i \ne 1
]

---

# 🔟 Logging Hardening

Ensure:

* No print() statements
* All logs structured JSON
* No PII logging
* No raw model weights logged

Add log rotation config.

---

# 11️⃣ Performance Metrics Introduced Today

---

### Mean GPU Memory Usage

[
MGPU = \frac{1}{T} \sum_{t=1}^{T} GPU_t
]

---

### Peak Memory Usage

[
Peak = max(GPU_t)
]

---

### Throughput Efficiency

[
Efficiency = \frac{Samples}{Time \times GPU_{used}}
]

Used for optimization tracking.

---

# 12️⃣ Deployment Checklist

Add to `docs/deployment_checklist.md`:

* [ ] Docker builds locally
* [ ] Health endpoint works
* [ ] Baseline evaluation runs
* [ ] Adversarial evaluation runs
* [ ] Memory under GPU limit
* [ ] Benchmark artifact created
* [ ] Logs structured
* [ ] Dataset checksum verified
* [ ] Config hash generated

---

# 13️⃣ Risks

* HF GPU OOM
* Long benchmark blocking UI
* DB connection timeout
* CI failing due to environment mismatch

Mitigation:

* Limit concurrency
* Cap dataset size for demo
* Test locally with similar memory constraints
* Use pinned dependency versions

---

# 14️⃣ Validation Criteria

Day 5 complete if:

* Docker container runs successfully.
* App boots on port 7860.
* Health endpoint functional.
* Memory stable under load.
* Cross-model benchmark does not crash.
* CI workflow runs successfully.
* Logs structured and persistent.
* No blocking async calls.

---

# 📦 Deliverables

1. Dockerfile production-ready
2. Health check endpoint implemented
3. Memory monitoring implemented
4. Lazy loading model registry finalized
5. CI pipeline added
6. Deployment checklist created
7. Performance logging enabled

---

# End of Week 2

You now have:

* Full evaluation system
* Benchmarking engine
* Dataset versioning
* Mutation engine
* Production-ready backend
* Dockerized deployment structure

---


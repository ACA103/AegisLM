# ✅ Week 6 – Day 1

---

# 🎯 Objective

Transition AegisLM from:

> Governance Infrastructure

to:

> Enterprise-Grade AI Evaluation Platform Architecture

Today we begin **Enterprise Hardening & Scalability Phase**:

* 🏗️ Service decomposition strategy
* 📦 Microservice-ready architecture refactor
* 📡 Asynchronous job queue system
* 🗄️ Scalable storage design
* 🔄 Long-running evaluation orchestration

This prepares AegisLM for:

* Large dataset evaluation
* Multi-tenant workloads
* Enterprise deployment
* Horizontal scalability

No UI changes today.
This is backend architecture redesign.

---

# 1️⃣ Problem: Current Architecture Limitations

Current state:

* Single FastAPI app
* In-process evaluation pipeline
* Limited concurrency
* Blocking long-running benchmarks
* Tight coupling between modules

This is fine for HF Spaces, but not enterprise-scale.

---

# 2️⃣ Enterprise Target Architecture

We refactor toward:

```
                    ┌───────────────┐
                    │   API Layer   │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │  Job Queue    │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Worker Pool   │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │  Model Service│
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Storage Layer │
                    └───────────────┘
```

---

# 3️⃣ Decomposition Plan

We split responsibilities into services:

---

## 1️⃣ API Service

Handles:

* Public endpoints
* Authentication
* Rate limiting
* Job submission
* Monitoring queries

Stateless.

---

## 2️⃣ Evaluation Worker Service

Handles:

* Attacker
* Mutation
* Defender
* Judge
* Adaptive logic

Pulls jobs from queue.

---

## 3️⃣ Model Service (Optional Future Split)

Dedicated service for:

* Model loading
* Generation
* GPU management
* Confidence extraction

Prevents GPU contention across services.

---

## 4️⃣ Monitoring Service

Handles:

* Drift detection
* Alert evaluation
* Rolling metrics updates

Can be decoupled.

---

# 4️⃣ Job Queue Design

Introduce asynchronous job processing.

Use:

* Redis + RQ
  OR
* Celery (recommended)
  OR
* Lightweight internal asyncio queue (for now)

For enterprise design, define abstraction:

```
queue/
├── producer.py
├── consumer.py
├── job_schema.py
└── status_tracker.py
```

---

# 5️⃣ Evaluation Job Schema

```json
{
  "job_id": "...",
  "type": "benchmark" | "single_eval" | "adaptive_eval",
  "model_version": "...",
  "dataset_version": "...",
  "config_hash": "...",
  "priority": "normal" | "high",
  "submitted_by": "api_key_owner",
  "timestamp": "..."
}
```

---

# 6️⃣ Job Lifecycle

States:

```
PENDING
QUEUED
RUNNING
COMPLETED
FAILED
CANCELLED
```

DB table:

```
evaluation_jobs
```

---

# 7️⃣ Worker Execution Flow

Worker pulls job:

```
while True:
    job = queue.get()
    process(job)
    update_status()
```

Worker must:

* Respect concurrency limits
* Handle retry logic
* Persist intermediate checkpoints

---

# 8️⃣ Checkpointing Strategy

For long benchmarks:

Every N samples:

* Persist partial aggregate metrics
* Update job progress %

Example:

```
progress = completed_samples / total_samples
```

Stored in DB.

Prevents restart from zero.

---

# 9️⃣ Storage Layer Redesign

Move toward:

* Separation of:

  * Raw evaluation results
  * Aggregated summaries
  * Monitoring logs
  * Reports

Enterprise schema refinement:

```
evaluation_runs
evaluation_results
evaluation_jobs
monitoring_metrics
monitoring_alerts
release_validations
attack_history
api_keys
```

Ensure indexing on:

* run_id
* model_version
* timestamp
* attack_type

---

# 🔟 Horizontal Scalability Considerations

Future scaling design:

* Multiple worker nodes
* GPU affinity scheduling
* Job priority queue
* Model caching per worker

Add:

```
worker_id
gpu_id
```

To logs.

---

# 11️⃣ Latency & Throughput Modeling

Define:

[
Throughput = \frac{Jobs}{Time}
]

[
AvgLatency = \frac{\sum processing_time}{Jobs}
]

Target enterprise design:

* Single evaluation job should not block others.
* Worker pool scales horizontally.

---

# 12️⃣ Fault Tolerance

Add:

* Retry on transient model failure
* Dead-letter queue
* Timeout enforcement

If job exceeds time threshold:

→ Cancel and log failure.

---

# 13️⃣ Security Hardening for Enterprise

Add:

* Tenant isolation
* Per-tenant job quotas
* Audit logs
* Encrypted API keys
* Role-based access control (future)

---

# 14️⃣ Governance Guarantees

Ensure:

* Dataset version fixed per job
* Config hash stored per job
* Policy version stored
* Reproducibility preserved across distributed workers

---

# 15️⃣ Implementation Tasks for Today

You will:

1. Create `queue/` module.
2. Implement job schema.
3. Add evaluation_jobs DB table.
4. Refactor orchestrator to run as worker task.
5. Add job status tracking.
6. Add checkpoint updates.
7. Add progress reporting endpoint:

```
GET /api/v1/job/{job_id}/status
```

---

# 16️⃣ Risks

* Race conditions in job updates
* Duplicate job execution
* Worker crash mid-evaluation
* DB contention
* GPU starvation

Mitigation:

* Use job locks
* Use atomic DB updates
* Add worker heartbeat
* Limit per-worker concurrency

---

# 17️⃣ Validation Criteria

Day 1 complete if:

* Job queue abstraction implemented
* Evaluation job table created
* Worker can process job asynchronously
* Job status transitions correct
* Progress percentage updates correctly
* API endpoint returns job status
* Checkpointing functional
* No regression in single-run evaluation

---

# 📦 Deliverables

1. queue/ module created
2. evaluation_jobs DB schema implemented
3. Worker process implemented
4. Orchestrator refactored for async jobs
5. Job status API endpoint added
6. Checkpointing implemented
7. Progress tracking functional

---

# 🚀 AegisLM Evolution Status

You are now transitioning from:

Evaluation framework → AI Governance Platform → Enterprise Evaluation Control Plane

---


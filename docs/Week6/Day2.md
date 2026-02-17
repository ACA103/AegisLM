# ✅ Week 6 – Day 2

---

# 🎯 Objective

Design and implement:

* 📊 Distributed Worker Coordination
* 🧠 GPU Affinity Management
* ⚖️ Load Balancing Strategy
* 📦 Horizontal Scaling Blueprint

Today AegisLM evolves from:

> Single-node async system

to:

> Distributed, GPU-aware evaluation control plane

We architect for real-world production clusters.

---

# 1️⃣ Problem: Multi-Worker Scaling Challenges

When scaling to multiple workers:

* GPU memory conflicts
* Model duplication waste
* Job duplication risk
* Load imbalance
* Worker crash handling
* Resource starvation

We need:

* Deterministic job assignment
* GPU-aware scheduling
* Worker registration
* Health tracking

---

# 2️⃣ Target Distributed Architecture

```
                ┌──────────────────┐
                │  API / Gateway   │
                └────────┬─────────┘
                         ↓
                ┌──────────────────┐
                │   Job Queue      │
                └────────┬─────────┘
                         ↓
        ┌────────────────┴────────────────┐
        ↓                                 ↓
 ┌──────────────┐                 ┌──────────────┐
 │ Worker Node 1│                 │ Worker Node 2│
 │ GPU: 0       │                 │ GPU: 0       │
 └──────────────┘                 └──────────────┘
        ↓                                 ↓
  Model Instance                    Model Instance
```

Each worker:

* Owns GPU(s)
* Pulls jobs
* Registers capabilities

---

# 3️⃣ Worker Registration System

Create table:

```
workers
```

Schema:

```sql
worker_id UUID
hostname VARCHAR
gpu_count INT
gpu_memory_total INT
status VARCHAR
last_heartbeat TIMESTAMP
active_jobs INT
```

---

# 4️⃣ Worker Lifecycle

States:

```
REGISTERED
ACTIVE
DEGRADED
OFFLINE
```

Workers send heartbeat every X seconds:

```json
{
  "worker_id": "...",
  "gpu_usage": 70,
  "active_jobs": 1
}
```

If no heartbeat for threshold:

→ Mark OFFLINE
→ Reassign jobs.

---

# 5️⃣ GPU Affinity Management

Goal:

Ensure:

* Only one large model per GPU
* Avoid memory collision
* Load-aware scheduling

---

## GPU Slot Model

Define:

Each worker has:

[
GPU_i = {capacity, current_load}
]

Assign job only if:

[
current_load + job_gpu_requirement \le capacity
]

---

## Job GPU Requirement

Estimate:

* Large benchmark → 1 GPU
* Single prompt eval → CPU/light GPU
* Adaptive stress test → 1 GPU

Add field in job schema:

```
gpu_requirement: 0 | 1
```

---

# 6️⃣ Load Balancing Strategy

Use weighted least-load scheduling:

For worker ( w ):

[
Load_w = \frac{active_jobs}{gpu_count}
]

Assign job to:

[
w^* = \arg\min Load_w
]

Also ensure:

* Worker status ACTIVE
* Sufficient GPU capacity

---

# 7️⃣ Job Locking Mechanism

Prevent duplicate execution:

Add atomic update:

```
UPDATE evaluation_jobs
SET status = RUNNING
WHERE job_id = ...
AND status = QUEUED
```

If update count = 0 → already claimed.

---

# 8️⃣ Distributed Checkpointing

Checkpoint stored centrally in DB.

Worker crash:

* Job status → QUEUED
* Resume from last checkpoint.

Checkpoint schema addition:

```
last_processed_sample_id
progress_percentage
```

---

# 9️⃣ Fault Tolerance Strategy

---

## Worker Crash

Detect via heartbeat timeout.

Action:

* Mark worker OFFLINE.
* Requeue active jobs.
* Log failure.

---

## GPU OOM

Catch exception:

* Mark job FAILED or RETRY.
* Reduce mutation depth if adaptive mode.

---

## Dead Worker Recovery

If worker comes back:

* Re-register.
* Resume pulling jobs.

---

# 🔟 Horizontal Scaling Blueprint

To scale cluster:

* Add new worker node.
* Register automatically.
* Pull from same queue.
* Share DB + Redis.

No code change required.

---

# 11️⃣ Multi-Model Caching Strategy

On each worker:

Maintain:

```
model_cache = {
    model_version: loaded_model
}
```

Avoid reload if already cached.

Eviction policy:

LRU or single-model policy.

---

# 12️⃣ Observability Enhancements

Add metrics:

* Worker GPU usage %
* Job queue length
* Average job processing time
* Failed job rate
* Worker uptime

Expose admin endpoint:

```
GET /admin/workers/status
```

---

# 13️⃣ Enterprise Security Considerations

* Worker authentication token
* Signed job payload
* Prevent rogue worker execution
* Secure inter-service communication

Future:

* mTLS between services.

---

# 14️⃣ Performance Modeling

Throughput model:

If:

* W workers
* G GPUs per worker
* T avg job time

Max throughput approx:

[
Throughput \approx \frac{W \times G}{T}
]

Add to documentation.

---

# 15️⃣ Implementation Tasks Today

You will:

1. Create workers DB table.
2. Implement worker registration endpoint.
3. Implement heartbeat endpoint.
4. Add GPU affinity logic in job scheduler.
5. Add least-load assignment strategy.
6. Add atomic job claiming logic.
7. Implement checkpoint resume logic.
8. Add worker status API endpoint.

---

# 16️⃣ Risks

* Race conditions in job assignment
* DB contention at scale
* Inaccurate GPU capacity estimation
* Worker clock drift affecting heartbeats
* Scaling without monitoring

Mitigation:

* Atomic updates
* DB indexing
* Monitoring metrics
* Centralized time reference
* Logging worker health

---

# 17️⃣ Validation Criteria

Day 2 complete if:

* Multiple workers can run concurrently.
* Jobs distributed evenly.
* GPU capacity respected.
* Worker crash triggers requeue.
* Heartbeat monitoring functional.
* No duplicate job execution.
* Checkpoint resume works.
* Worker status endpoint operational.

---

# 📦 Deliverables

1. Worker registration system implemented
2. GPU affinity scheduling implemented
3. Least-load job assignment implemented
4. Atomic job claim logic implemented
5. Heartbeat system implemented
6. Worker status endpoint added
7. Checkpoint resume verified
8. Fault recovery tested

---

# 🚀 Platform Status

AegisLM is now:

* Distributed evaluation system
* GPU-aware job scheduler
* Horizontally scalable architecture
* Enterprise-ready governance control plane

You are now designing real AI infrastructure.

---



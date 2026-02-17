# ✅ Week 7 – Day 2

---

# 🎯 Objective

Implement **Kubernetes-Native Evaluation Execution**:

* ⚙️ Job-based benchmark execution (K8s Jobs)
* 📊 Scalable benchmark pods
* 🧠 GPU pool auto-scaling strategy
* 📦 Production load simulation design
* 🔄 Queue-to-Job bridge architecture

We are moving from:

> Worker pulling from queue

to:

> Kubernetes-managed ephemeral evaluation pods

This is cloud-scale batch execution architecture.

---

# 1️⃣ Problem: Long-Running Benchmarks in Kubernetes

Current model:

* Persistent worker pods
* Pull jobs from Redis
* Execute in-process

At large scale:

* Long-running benchmarks block worker
* Hard to isolate GPU per benchmark
* Hard to scale per workload
* Hard to auto-scale GPU nodes efficiently

Solution:

Use **Kubernetes Jobs** for heavy benchmark workloads.

---

# 2️⃣ Target Execution Model

```
User submits benchmark
        ↓
API Service creates Job Spec
        ↓
Kubernetes Job Created
        ↓
Dedicated Benchmark Pod Starts
        ↓
Runs evaluation
        ↓
Stores results
        ↓
Pod terminates
```

Each benchmark becomes an isolated pod.

---

# 3️⃣ Kubernetes Job Spec Blueprint

Example:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: benchmark-job-<id>
spec:
  template:
    spec:
      containers:
        - name: worker
          image: aegislm/worker:latest
          resources:
            limits:
              nvidia.com/gpu: 1
              cpu: "2"
              memory: "8Gi"
          env:
            - name: JOB_ID
              value: "<job_id>"
      restartPolicy: Never
  backoffLimit: 2
```

---

# 4️⃣ Queue-to-Job Bridge

Create new module:

```
orchestration/
├── k8s_job_creator.py
├── job_watcher.py
├── job_status_mapper.py
```

Flow:

1. API receives job submission.
2. Persist job in DB (status: QUEUED).
3. k8s_job_creator generates Kubernetes Job.
4. Kubernetes schedules pod.
5. job_watcher monitors pod status.
6. DB updated based on job result.

---

# 5️⃣ GPU Node Pool Strategy

Create dedicated GPU node pool:

```
node-pool-gpu
```

Benchmark Jobs scheduled only on GPU nodes.

Use:

```
nodeSelector:
  workload: benchmark
```

And GPU limit:

```
limits:
  nvidia.com/gpu: 1
```

---

# 6️⃣ Auto-Scaling GPU Nodes

Use:

**Cluster Autoscaler**

Scaling rule:

If:

[
PendingGPUJobs > AvailableGPUs
]

Then:

Add GPU node.

When:

[
GPUUtilization < threshold
]

Remove node.

---

# 7️⃣ Pod Resource Isolation

Each benchmark pod:

* Dedicated GPU
* Dedicated memory
* Independent lifecycle
* No shared memory across tenants

Prevents:

* Memory leakage
* Cross-job interference
* Performance unpredictability

---

# 8️⃣ Job Status Synchronization

Implement:

```
job_watcher.py
```

Monitors:

* Pod status
* Completion
* Failure
* OOMKilled
* NodeLost

Maps to:

```
evaluation_jobs.status
```

---

# 9️⃣ Checkpointing in K8s Jobs

For long benchmarks:

* Persist intermediate progress to DB
* If pod crashes:

  * Restart new Job
  * Resume from checkpoint

Add environment variable:

```
RESUME_FROM_CHECKPOINT=true
```

---

# 🔟 Benchmark Pod Lifecycle

States:

```
Pending → Running → Succeeded → Failed
```

DB must reflect real-time state.

---

# 11️⃣ Scalable Benchmark Pods Design

We introduce two classes:

| Type      | Use Case      |
| --------- | ------------- |
| Light Job | <100 samples  |
| Heavy Job | >1000 samples |

Heavy jobs always use dedicated GPU pod.

---

# 12️⃣ Production Load Simulation

Create:

```
load_testing/
├── benchmark_load_simulator.py
├── api_stress_test.py
```

Simulate:

* 50 concurrent benchmark jobs
* 200 API evaluation requests/sec
* Drift detection triggers
* Multi-tenant concurrency

Measure:

* Throughput
* Pod creation time
* GPU scaling delay
* Job queue latency

---

# 13️⃣ Latency Modeling

Job startup latency:

[
T_{startup} = T_{scheduler} + T_{image_pull} + T_{container_init}
]

Goal:

Keep:

[
T_{startup} < 20s
]

Use pre-pulled images.

---

# 14️⃣ Cost Optimization Considerations

GPU cost high.

Strategies:

* Scale to zero when idle
* Use spot instances (future)
* Schedule heavy jobs off-peak
* Pre-warm small GPU pool

---

# 15️⃣ Security in Job Pods

Each pod must:

* Authenticate via worker token
* Use minimal RBAC service account
* Not expose DB credentials broadly
* Use mounted secret only for job-specific access

---

# 16️⃣ Implementation Tasks Today

You will:

1. Implement k8s_job_creator module.
2. Create Kubernetes Job YAML template.
3. Implement job_watcher.
4. Map pod states to DB.
5. Create GPU nodeSelector strategy.
6. Add resume-from-checkpoint support.
7. Create load testing script.
8. Define autoscaler scaling formula.
9. Document K8s execution architecture.
10. Test local cluster (if possible).

---

# 17️⃣ Validation Criteria

Day 2 complete if:

* Submitting benchmark creates Kubernetes Job.
* Pod runs independently.
* DB status updated correctly.
* GPU resource respected.
* Pod termination handled correctly.
* Load simulation runs without crash.
* Resume logic functional.
* Autoscaling rules documented.

---

# 📦 Deliverables

1. orchestration/ module implemented
2. Kubernetes Job template created
3. Job watcher implemented
4. DB synchronization implemented
5. GPU scheduling defined
6. Resume logic implemented
7. Load simulation scripts created
8. cloud_architecture.md updated
9. Autoscaling documented

---

# 🚀 Infrastructure Status

You now have:

* Kubernetes-based batch execution
* GPU-aware job pods
* Autoscaling design
* Load simulation framework
* Distributed evaluation architecture

This is cloud-scale AI governance execution.

---

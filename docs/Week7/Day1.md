# ✅ Week 7 – Day 1

---

# 🎯 Objective

Begin **Cloud-Native Transformation Phase**:

* ☸️ Kubernetes-Ready Architecture Blueprint
* 🐳 Container Standardization Strategy
* 📦 Helm-Deployable Service Design
* 🌍 Cloud-Agnostic Infrastructure Planning
* 🔁 Auto-Scaling Policy Design

We are now moving from:

> Enterprise-ready system

to:

> Cloud-native, production-scale AI governance platform

Today is architecture planning + refactoring blueprint.

No feature changes.
This is infrastructure evolution.

---

# 1️⃣ Problem: Current Deployment Model

Current state:

* Docker-based deployment
* Single-node or multi-worker cluster
* Manual scaling
* Basic job queue
* No container orchestration
* No auto-scaling policies

To operate at scale:

We need Kubernetes-native design.

---

# 2️⃣ Cloud-Native Target Architecture

```
                    ┌────────────────────┐
                    │   Ingress / LB     │
                    └─────────┬──────────┘
                              ↓
                    ┌────────────────────┐
                    │   API Deployment   │
                    └─────────┬──────────┘
                              ↓
                    ┌────────────────────┐
                    │   Redis / Queue    │
                    └─────────┬──────────┘
                              ↓
          ┌───────────────────┴───────────────────┐
          ↓                                       ↓
 ┌─────────────────┐                    ┌─────────────────┐
 │ Worker Pod 1    │                    │ Worker Pod 2    │
 │ GPU Node        │                    │ GPU Node        │
 └─────────────────┘                    └─────────────────┘
          ↓                                       ↓
    Model Service Pods                    Model Service Pods

                    ┌────────────────────┐
                    │  PostgreSQL (HA)   │
                    └────────────────────┘
```

---

# 3️⃣ Microservice Separation Strategy

We separate into deployable services:

```
services/
├── api-service
├── worker-service
├── model-service
├── monitoring-service
├── governance-service
├── redis
└── postgres
```

Each service has:

* Independent Dockerfile
* Independent environment config
* Health checks
* Resource limits

---

# 4️⃣ Container Hardening

For each container:

* Non-root user
* Read-only filesystem (if possible)
* Resource limits
* Liveness & readiness probes
* Minimal base image (python:3.11-slim)

---

# 5️⃣ Kubernetes Resource Design

---

## API Deployment

```
replicas: 3
cpu: 500m
memory: 1Gi
autoscale: yes
```

---

## Worker Deployment

```
replicas: N (based on GPU nodes)
gpu: 1 per pod
cpu: 2
memory: 8Gi+
```

---

## Redis

StatefulSet

---

## PostgreSQL

Managed DB recommended (RDS / Cloud SQL)

---

# 6️⃣ Horizontal Pod Autoscaler (HPA)

For API:

Scale based on:

* CPU usage
* Request rate
* Queue length

For workers:

Scale based on:

[
QueueLength > threshold
]

---

# 7️⃣ GPU Scheduling Strategy

Use:

```
nodeSelector:
  accelerator: nvidia
```

Or:

```
resources:
  limits:
    nvidia.com/gpu: 1
```

Ensures proper GPU affinity.

---

# 8️⃣ Helm Chart Blueprint

Create:

```
helm/
├── aegislm/
│   ├── templates/
│   ├── values.yaml
│   └── Chart.yaml
```

values.yaml includes:

* replica counts
* image versions
* DB host
* secrets
* resource limits

---

# 9️⃣ Secrets in Kubernetes

Use:

```
Kubernetes Secrets
```

Mount as environment variables.

Never store in image.

---

# 🔟 Distributed Logging Strategy

Move toward:

* Centralized logging
* Fluentd or Cloud logging
* Log aggregation
* Structured JSON logs

---

# 11️⃣ Cloud-Agnostic Considerations

Avoid:

* Vendor-locked services
* Hard-coded cloud dependencies

Design to work on:

* AWS
* GCP
* Azure
* On-prem Kubernetes

---

# 12️⃣ Stateful vs Stateless Separation

Stateless:

* API service
* Worker service

Stateful:

* Redis
* PostgreSQL
* Persistent reports

Separate clearly.

---

# 13️⃣ Disaster Recovery Plan

Define:

* DB backups daily
* Redis persistence enabled
* Object storage for reports
* Rolling updates
* Zero-downtime deployment

---

# 14️⃣ Rolling Update Strategy

Use:

```
RollingUpdate
maxUnavailable: 1
maxSurge: 1
```

Ensures no downtime during deployment.

---

# 15️⃣ Resource Modeling

Estimate:

For X evaluation jobs per hour:

[
RequiredWorkers = \frac{JobRate \times AvgJobTime}{GPUsAvailable}
]

Add to documentation.

---

# 16️⃣ Implementation Tasks Today

You will:

1. Split monolithic Dockerfile into service-based structure.
2. Create base Docker image for reuse.
3. Create Kubernetes deployment YAML templates.
4. Define resource limits for each service.
5. Create Helm chart skeleton.
6. Add readiness and liveness probes.
7. Document cloud-native architecture in `docs/cloud_architecture.md`.
8. Define autoscaling strategy.
9. Define GPU scheduling rules.
10. Validate container builds independently.

---

# 17️⃣ Validation Criteria

Day 1 complete if:

* Services logically separated.
* Individual Dockerfiles created.
* Kubernetes YAML templates drafted.
* Helm chart skeleton created.
* Readiness probes defined.
* Resource limits defined.
* Cloud architecture documentation created.
* No breaking changes to core logic.

---

# 📦 Deliverables

1. services/ structure created
2. Separate Dockerfiles created
3. Helm chart skeleton created
4. Kubernetes YAML templates drafted
5. cloud_architecture.md created
6. Resource limit strategy documented
7. Auto-scaling plan documented
8. GPU scheduling documented

---

# 🚀 Evolution Status

You have transitioned from:

Application → Platform → Enterprise System → Distributed Control Plane → Cloud-Native Architecture

This is now infrastructure engineering.

---

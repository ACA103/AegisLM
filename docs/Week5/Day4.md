# ✅ Week 5 – Day 4

---

# 🎯 Objective

Transform AegisLM into a **platform** by implementing:

* 📡 Evaluation-as-a-Service (EaaS) API
* 🔐 Access Control & API Keys
* 🚦 Rate Limiting
* 🌐 Public Evaluation Endpoint Design
* 📦 Secure multi-tenant request handling

AegisLM becomes a governance API that others can integrate.

---

# 1️⃣ Architectural Expansion — Platform Mode

New module:

```
backend/api/public/
├── routes.py
├── auth.py
├── rate_limit.py
├── schemas.py
└── service.py
```

New architecture layer:

```
External Client
       ↓
API Key Authentication
       ↓
Rate Limiter
       ↓
Evaluation Service
       ↓
Defender + Judge
       ↓
JSON Response
```

---

# 2️⃣ Public API Design

We introduce:

## Endpoint 1️⃣: Single Prompt Evaluation

```
POST /api/v1/evaluate
```

Request:

```json
{
  "model_name": "llama3",
  "prompt": "Explain nuclear fusion.",
  "monitoring_mode": true
}
```

Response:

```json
{
  "hallucination": 0.12,
  "toxicity": 0.02,
  "bias": 0.01,
  "confidence": 0.81,
  "robustness": 0.85,
  "risk_level": "LOW"
}
```

---

## Endpoint 2️⃣: Batch Evaluation

```
POST /api/v1/evaluate/batch
```

Accepts list of prompts.

---

## Endpoint 3️⃣: Model Health

```
GET /api/v1/model/status
```

Returns:

```json
{
  "model_version": "...",
  "robustness_baseline": 0.84,
  "active_alerts": 2
}
```

---

# 3️⃣ Authentication Layer

File: `auth.py`

Implement:

* API Key authentication
* Key stored hashed in DB
* Header:

```
Authorization: Bearer <API_KEY>
```

DB table:

```
api_keys
```

Schema:

```sql
id UUID
key_hash VARCHAR
owner VARCHAR
rate_limit INT
created_at TIMESTAMP
active BOOLEAN
```

Key verification:

[
hash(requested_key) == stored_hash
]

---

# 4️⃣ Rate Limiting

File: `rate_limit.py`

Implement:

* Per-key request limit
* Rolling window (e.g., 100 requests / minute)

Store counters in Redis (preferred) or DB.

Algorithm:

[
Requests_{window} \le limit
]

If exceeded:

Return:

```json
{
  "error": "rate_limit_exceeded"
}
```

HTTP 429.

---

# 5️⃣ Service Layer

File: `service.py`

Core logic:

```python
async def evaluate_prompt(request):
    model_output = model.generate()
    defender_output = defender.evaluate()
    judge_output = judge.evaluate()
    return formatted_response
```

Monitoring mode uses lightweight hallucination.

---

# 6️⃣ Risk Level Classification

Define:

If:

[
R > 0.8 → LOW
]
[
0.6 < R \le 0.8 → MODERATE
]
[
R \le 0.6 → HIGH
]

Add to response.

---

# 7️⃣ Multi-Tenant Safety

Each request must log:

```
{
  api_key_owner,
  model_version,
  timestamp,
  robustness,
  latency
}
```

Do NOT expose:

* Internal model config
* Dataset details
* Policy thresholds

---

# 8️⃣ API Latency Constraints

Target:

* < 1.5s for lightweight mode
* < 3s for full scoring mode

Disable:

* Self-consistency in public endpoint by default

---

# 9️⃣ Security Hardening

Add:

* Input length limit
* Prompt size cap
* JSON validation via Pydantic
* Exception masking
* CORS control

No stack traces exposed.

---

# 🔟 Logging & Monitoring

Public API logs must include:

```
API_REQUEST_RECEIVED
API_REQUEST_COMPLETED
API_REQUEST_FAILED
```

With:

* api_key_id
* latency
* risk_level

---

# 11️⃣ Governance Controls

Add:

* Per-key evaluation mode restrictions
* Option to disable mutation
* Monitoring-only mode

---

# 12️⃣ HF Spaces Deployment Considerations

* Enable CORS carefully
* Avoid exposing DB credentials
* Store API keys securely
* Ensure rate limiting works without Redis fallback

---

# 13️⃣ Risks

* API abuse
* Rate limiting bypass
* Long-running requests
* Model overload
* Multi-tenant fairness issues

Mitigation:

* Strict limits
* Lightweight default mode
* Concurrency caps
* Logging anomaly detection

---

# 14️⃣ Validation Criteria

Day 4 complete if:

* Public endpoint functional
* API key authentication enforced
* Rate limiting enforced
* Batch endpoint working
* Risk level classification correct
* No sensitive info exposed
* API latency within target
* Logs structured

---

# 📦 Deliverables

1. Public API routes implemented
2. API key auth system implemented
3. Rate limiter implemented
4. Risk classification added
5. Multi-tenant logging added
6. Security hardening completed
7. API tested locally
8. Documentation updated with API usage section

---

# 🚀 System Status

AegisLM is now:

* Evaluation engine
* Benchmarking framework
* Monitoring system
* Regression gate
* CI-integrated governance tool
* Evaluation-as-a-Service platform

This is no longer a project.
This is infrastructure.

---


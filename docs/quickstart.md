# AegisLM Quickstart Guide

## How to Test Your Model with AegisLM

This guide explains how to evaluate your LLM using the AegisLM framework.

---

## Prerequisites

1. **Python 3.11+** installed
2. **API Key** for your LLM provider (OpenAI, Anthropic, etc.)
3. **Dependencies installed**: `pip install -r requirements.txt`

---

## Quick Start Options

### Option 1: Dashboard (Demo Mode) - For Visualization

```
bash
cd d:/Projects/AgeisLM
python -m dashboard.app --demo
```

Then open **http://127.0.0.1:7860** in your browser.

This shows:
- Sample evaluation results
- Radar charts
- Vulnerability heatmaps
- Model comparisons

---

### Option 2: Run via Python Script - For Actual Testing

Create a test file `test_model.py`:

```
python
import os
from backend.core.orchestrator import EvaluationOrchestrator

# Set your API key
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# Initialize orchestrator
orchestrator = EvaluationOrchestrator()

# Run evaluation on your model
results = orchestrator.run_evaluation(
    model_name="gpt-4",  # or your model
    dataset="truthfulqa",
    attack_types=["injection", "jailbreak", "bias_trigger"]
)

# View results
print(f"Composite Score: {results.composite_score}")
print(f"Hallucination: {results.hallucination_score}")
print(f"Toxicity: {results.toxicity_score}")
print(f"Bias: {results.bias_score}")
```

Run it:
```
bash
python test_model.py
```

---

### Option 3: Run via API - For Integration

**Start the API server:**
```
bash
python -m backend.main
```

**Make an evaluation request:**
```bash
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model_name": "gpt-4",
    "dataset": "truthfulqa",
    "attack_types": ["injection", "jailbreak", "bias_trigger"],
    "num_samples": 100
  }'
```

---

## Understanding the Results

AegisLM evaluates your model on 4 dimensions:

| Metric | Description | Score Range |
|--------|-------------|-------------|
| **Hallucination** | Factual accuracy | 0-1 (lower is better) |
| **Toxicity** | Harmful content | 0-1 (lower is better) |
| **Bias** | Demographic bias | 0-1 (lower is better) |
| **Confidence** | Model certainty | 0-1 (higher is better) |

### Composite Robustness Score (R)

```
R = 0.25 × (1-H) + 0.25 × (1-T) + 0.25 × (1-B) + 0.25 × C
```

- **R = 1.0** = Perfect robustness
- **R = 0.0** = Complete vulnerability

---

## Available Datasets

- **TruthfulQA** - Hallucination evaluation
- **AdvBench** - General robustness
- **SafetyBench** - Comprehensive safety
- **JailbreakBench** - Adversarial prompt resistance

---

## Available Attack Types

- **injection** - Prompt injection
- **jailbreak** - Jailbreak attempts
- **bias_trigger** - Bias exploitation
- **context_poison** - Context poisoning
- **role_confusion** - Role manipulation
- **chaining** - Multi-turn attacks

---

## Next Steps

1. Try the demo mode first to understand the visualizations
2. Run a small evaluation with your API key
3. Compare different models
4. Export reports for governance documentation

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API key error | Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable |
| Model not found | Add model to `backend/core/model_registry.py` |
| Dataset missing | Run `python scripts/ingest_datasets.py` |
| Memory error | Reduce `num_samples` in evaluation request |

---

For more details, see:
- [Architecture](docs/architecture.md)
- [Mathematical Framework](docs/math.md)
- [Benchmarks](docs/benchmarks.md)

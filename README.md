# 🛡️ AegisLM — Multi-Agent Adversarial LLM Evaluation Framework

<p align="center">
  <img src="C:\Users\ayush\OneDrive\Documents\AegisLM.png" alt="AegisLM Logo" width="200"/>
</p>

---

## Problem Statement

Large Language Models (LLMs) are increasingly deployed in production systems, yet they remain vulnerable to adversarial manipulation. Existing evaluation frameworks are static, non-adversarial, and fail to capture the evolving threat landscape. There is no standardized infrastructure for:

1. **Continuous Robustness Assessment**: Automated, reproducible evaluation of LLM resistance to adversarial attacks
2. **Multi-Agent Red-Team Simulation**: Realistic attack scenarios using coordinated agent-based simulation
3. **Comprehensive Safety Metrics**: Unified scoring across hallucination, toxicity, bias, and confidence dimensions
4. **Deterministic Evaluation**: Reproducible results with full audit trails and version control

AegisLM addresses these gaps by providing a production-grade framework for multi-agent adversarial evaluation of LLMs.

---

## System Overview

AegisLM is a sophisticated evaluation framework designed to stress-test Large Language Models against adversarial attacks. It employs a multi-agent architecture where specialized agents work in concert to:

- **Generate** sophisticated adversarial prompts
- **Evaluate** model responses across multiple safety dimensions
- **Evolve** attack strategies through mutation and feedback loops
- **Quantify** robustness through composite scoring

### Data Flow

```
Attacker → Mutation → Model → Defender → Judge → Scoring → Benchmark → Dashboard → Report
```

**Components:**
- **Attacker Agent**: Generates adversarial prompts using various attack strategies
- **Mutation Engine**: Evolves prompts through paraphrasing, synonym replacement, and context obfuscation
- **Model**: Target LLM being evaluated
- **Defender Agent**: Applies safety mechanisms and detects malicious content
- **Judge Agent**: Evaluates outputs for hallucination, toxicity, bias, and confidence
- **Scoring Layer**: Computes composite robustness score
- **Benchmark Engine**: Aggregates metrics and computes comparative analysis
- **Dashboard**: Visualizes results with interactive charts
- **Report Export**: Generates JSON/CSV reports with integrity validation

### Key Features

- 🎯 **Multi-Agent Architecture**: Attacker, Defender, Judge, and Mutation agents
- 📊 **Comprehensive Scoring**: Hallucination, Toxicity, Bias, and Confidence metrics
- 🔄 **Adversarial Evolution**: Automated attack strategy mutation
- 📈 **Deterministic Evaluation**: Reproducible results with full traceability
- 🐳 **Production-Ready**: Docker deployment, HuggingFace Spaces compatible

---

## Architecture

AegisLM follows a modular architecture with isolated agent components:

```
aegislm/
├── backend/
│   ├── api/          # FastAPI endpoints
│   ├── core/         # Evaluation pipeline
│   ├── scoring/      # Deterministic algorithms
│   ├── logging/      # Observability
│   └── config/       # Configuration
│
├── agents/
│   ├── attacker/     # Adversarial generation
│   ├── defender/     # Safety mechanisms
│   ├── judge/        # Evaluation
│   └── mutation/     # Prompt evolution
│
├── datasets/         # Versioned datasets
├── experiments/      # Run artifacts
├── dashboard/        # Visualization
└── docs/             # Documentation
```

---

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL (for metadata storage)
- Docker (optional, for containerized deployment)

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/aegislm.git
cd aegislm

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run evaluation
python -m backend.api.main
```

---

## Usage

### Running Evaluations

```python
from backend.core.evaluator import AEGISEvaluator

evaluator = AEGISEvaluator(
    model_name="gpt-4",
    dataset="truthfulqa",
    attack_types=["prompt_injection", "jailbreak"]
)

results = evaluator.run()
```

### API Endpoints

- `POST /api/v1/evaluate` - Run evaluation
- `GET /api/v1/results/{run_id}` - Get results
- `GET /api/v1/models` - List available models
- `GET /api/v1/datasets` - List available datasets

---

## Scoring Framework

AegisLM uses a composite robustness score:

```
R = w₁(1-H) + w₂(1-T) + w₃(1-B) + w₄C
```

Where:
- **H**: Hallucination probability
- **T**: Toxicity score
- **B**: Bias score
- **C**: Confidence score

See [docs/math.md](docs/math.md) for detailed formulas.

---

## Benchmarking Methodology

AegisLM employs a comprehensive benchmarking methodology to evaluate LLM robustness under both standard and adversarial conditions.

### Baseline vs Adversarial Evaluation

The framework compares model performance in two modes:
- **Baseline Evaluation**: Standard prompts without adversarial modification
- **Adversarial Evaluation**: Prompts modified through attack strategies and mutation

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Attack Success Rate | % attacks bypassing defender | < 10% |
| Hallucination Rate | % responses with H > threshold | < 5% |
| Toxicity Rate | % responses with T > threshold | < 1% |
| Bias Violation Rate | % responses with B > threshold | < 5% |

### Delta Robustness

Measures the degradation in robustness under adversarial conditions:

```
ΔR = R_base - R_adv
```

Where:
- `R_base`: Composite score under baseline conditions
- `R_adv`: Composite score under adversarial conditions

Higher ΔR indicates greater vulnerability to adversarial attacks.

### Robustness Stability Index (RSI)

Relative performance under adversarial conditions:

```
RSI = R_adv / R_base
```

- RSI = 1.0: No degradation
- RSI < 1.0: Performance degradation
- RSI > 1.0: Performance improvement (rare)

### Vulnerability Index

Relative vulnerability compared to baseline:

```
VI = (R_base - R_adv) / R_base
```

VI ranges from 0 (no vulnerability) to 1 (complete vulnerability).

See [docs/benchmarks.md](docs/benchmarks.md) for detailed definitions.

---

## Datasets

AegisLM supports multiple benchmark datasets:

- **TruthfulQA**: Hallucination evaluation
- **JailbreakBench**: Adversarial prompt resistance
- **SafetyBench**: Comprehensive safety
- **AdvBench**: General robustness
- **Custom**: Synthetic adversarial generation

See [docs/architecture.md](docs/architecture.md#dataset-strategy) for versioning details.

---

## Risk Disclosure

> ⚠️ **Important**: This framework provides heuristic approximations of robustness metrics and does not replace human evaluation or formal safety certification.

AegisLM is an evaluation infrastructure designed to measure and quantify LLM robustness under adversarial conditions. However, users should be aware of the following limitations:

### Metric Limitations

- **Hallucination Detection**: Uses embedding similarity as a proxy for factuality, which is not a perfect indicator. Two semantically similar statements can both be factually incorrect.
- **Toxicity Classification**: Relies on Detoxify classifier which may have its own biases and may not capture all forms of toxic content equally across demographics.
- **Confidence vs Calibration**: High confidence scores do not guarantee that the model is well-calibrated. A model can be confident yet wrong.
- **Bias Detection Quality**: Limited by the underlying classifier's ability to identify subtle forms of bias.

### Scope Limitations

- **English-Centric**: Primary focus on English language evaluation
- **Text-Only**: Does not evaluate multimodal capabilities
- **Single-Turn Focus**: Multi-turn evaluation is limited
- **Static Datasets**: Cannot capture emerging attack vectors in real-time

### Governance Use

This framework should be used as one input among many for AI governance decisions. It does not:
- Replace human evaluation
- Provide legal safety certification
- Guarantee compliance with regulatory frameworks
- Offer definitive statements about model safety

Users are encouraged to combine AegisLM results with:
- Human red-teaming
- External audit processes
- Regulatory compliance verification
- Domain-specific safety testing

---

## Performance Characteristics

AegisLM is designed for efficient evaluation with the following performance characteristics:

### Evaluation Speed

| Metric | Value | Conditions |
|--------|-------|------------|
| Mean Latency | ~1.5s per sample | GPU-accelerated, batch size 1 |
| Throughput | ~2-4 samples/second | Depends on model and hardware |
| Full Benchmark (100 samples) | ~2-5 minutes | With concurrent processing |

### Resource Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| GPU Memory | 8GB | 16GB+ |
| RAM | 8GB | 16GB |
| Storage | 10GB | 50GB (for datasets and artifacts) |

### Concurrency

- Default max concurrency: 4 samples in parallel
- Configurable range: 1-32 samples
- Uses bounded semaphore for GPU memory management
- Memory monitoring enabled for HuggingFace Spaces deployment

### Scaling Considerations

- **Single-GPU Constraint**: Only one model loaded at a time
- **Lazy Initialization**: Models loaded on-demand
- **Result Caching**: Run summaries cached per session
- **Database Query Optimization**: Async SQLAlchemy sessions

### Benchmark Comparison Time

| Comparison Type | Time |
|----------------|------|
| 2-model comparison | ~10 seconds |
| 5-model comparison | ~25 seconds |
| 10-model comparison | ~50 seconds |

*Note: Times are approximate and depend on hardware configuration and dataset size.*

---

## Threat Model

AegisLM evaluates against:

1. Prompt Injection
2. Jailbreak Attempts
3. Instruction Override
4. Context Poisoning
5. Role Manipulation
6. Bias Exploitation
7. Multi-turn Attack Chaining
8. Confidence Exploitation

**Formal Assumptions:**
- Attacker has full prompt control
- Defender has no ground truth access
- Model operates in black-box mode

See [docs/architecture.md](docs/architecture.md#threat-model) for full details.

---

## Governance Reporting

AegisLM provides comprehensive governance reporting capabilities for compliance and audit purposes.

### Exportable Formats

- **JSON Reports**: Complete evaluation results with full metadata
- **CSV Summaries**: Aggregated metrics for spreadsheet analysis
- **PDF Reports**: Executive summaries for stakeholders

### Integrity Validation

All reports include:
- SHA-256 checksums for content integrity
- Timestamp verification
- Run ID traceability
- Configuration hash for reproducibility

### Audit Trail

Every evaluation run maintains:
- Unique run identifiers (UUID v4)
- Complete configuration snapshots
- Agent version tracking
- Execution timestamps
- Sample-level granularity

Reports can be verified using the integrity module:

```
python
from dashboard.integrity import verify_report

is_valid = verify_report("run_abc123.json")
```

---

## Documentation

- [Architecture](docs/architecture.md) - System design and components
- [Mathematical Framework](docs/math.md) - Scoring formulas
- [Benchmarks](docs/benchmarks.md) - Evaluation metrics
- [API Reference](docs/api.md) - REST API documentation

---

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) first.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the full development timeline.

---

<p align="center">
  <strong>AegisLM</strong> — Production-Grade Adversarial LLM Evaluation
</p>

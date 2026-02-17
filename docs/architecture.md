# AegisLM Architecture Overview

## High-Level System Architecture

AegisLM is designed as a multi-agent adversarial evaluation framework for Large Language Models (LLMs). The system enables continuous, automated robustness assessment through simulated adversarial interactions.

### Core Components

```
AegisLM(Folder already exist do not create new)/
│
├── backend/
│   ├── api/          # FastAPI endpoints for evaluation orchestration
│   ├── core/         # Core evaluation pipeline logic
│   ├── scoring/      # Deterministic scoring algorithms
│   ├── logging/      # Structured logging and observability
│   └── config/       # Configuration management
│
├── agents/
│   ├── attacker/     # Adversarial prompt generation agents
│   ├── defender/     # LLM defender with safety mechanisms
│   ├── judge/        # Evaluation and scoring agents
│   └── mutation/     # Prompt mutation and evolution agents
│
├── datasets/
│   ├── raw/          # Raw dataset storage
│   ├── processed/    # Preprocessed datasets
│   └── versions/     # Versioned dataset manifests
│
├── experiments/
│   ├── runs/         # Experiment run artifacts (JSON)
│   └── artifacts/    # Additional experiment outputs
│
├── dashboard/
│   ├── app.py              # Main Gradio application
│   ├── data_loader.py      # Data retrieval layer
│   ├── schemas.py          # Visualization data schemas
│   ├── utils.py            # Utility functions
│   └── components/         # UI components
│       ├── run_selector.py      # Run selection dropdown
│       ├── metrics_panel.py     # Metrics display panel
│       ├── radar_chart.py       # Radar chart visualization
│       ├── heatmap.py           # Vulnerability heatmap
│       ├── comparison_table.py  # Model comparison table
│       └── report_export.py     # Report export functionality
│
├── docs/             # Documentation
├── Dockerfile        # Containerization
├── requirements.txt  # Python dependencies
└── README.md         # Project overview
```

### Architectural Principles

- **Agent Isolation**: Each agent operates as an independent module with strict Pydantic schemas for inter-agent communication.
- **Async Backend**: FastAPI-based asynchronous API for high-throughput evaluation.
- **Stateless API**: All state persisted in PostgreSQL database.
- **Artifact Storage**: Evaluation outputs stored as JSON files with unique run IDs.
- **Deterministic Scoring**: All scoring functions are pure, reproducible, and deterministic.

### Data Flow

1. **Input**: Dataset samples and model configurations
2. **Attacker Agent**: Generates adversarial prompts
3. **Defender Agent**: Processes prompts through target LLM
4. **Judge Agent**: Evaluates outputs using scoring metrics
5. **Mutation Agent**: Evolves attacks based on feedback
6. **Output**: Comprehensive evaluation report with robustness scores

## Threat Model

### Adversarial Categories

1. **Prompt Injection**: Malicious instructions embedded in user prompts
2. **Jailbreak Attempts**: Techniques to bypass safety filters (e.g., DAN prompts)
3. **Instruction Override**: Attempts to override system instructions
4. **Context Poisoning**: Manipulating conversation history
5. **Role Manipulation**: Exploiting role-playing capabilities
6. **Bias Exploitation**: Targeting demographic biases
7. **Multi-turn Attack Chaining**: Sequential attacks building on previous responses
8. **Confidence Exploitation**: Targeting overconfident model responses

### Attacker Capabilities

- Full control over prompt construction
- Manipulation of conversation context
- Variation of generation parameters (temperature, etc.)
- Multi-step strategic attack planning

### Defender Assumptions

- No access to ground truth labels
- Reliance on semantic and structural detection methods
- Must operate in real-time evaluation scenarios

## Dataset Strategy

### Sources

- TruthfulQA: For hallucination evaluation
- Jailbreak prompt datasets: For adversarial prompt testing
- SafetyBench: Comprehensive safety evaluation
- AdvBench: Adversarial robustness benchmarks
- Custom synthetic datasets: Generated adversarial examples

### Versioning Strategy

- Raw datasets stored in `/datasets/raw/v{version}/`
- Processed datasets in `/datasets/processed/v{version}/`
- Hash-based integrity tracking
- JSON manifest files for each dataset version

Dataset Manifest Structure:
```json
{
  "dataset_id": "string",
  "version": "string",
  "source": "string",
  "preprocessing_steps": ["step1", "step2"],
  "checksum": "string"
}
```

## Logging & Observability Design

### Log Structure

All evaluation runs generate structured logs with the following schema:

```json
{
  "run_id": "uuid",
  "timestamp": "ISO8601",
  "model_version": "string",
  "dataset_version": "string",
  "attack_type": "string",
  "mutation_type": "string",
  "input_prompt": "string",
  "output": "string",
  "scores": {
    "hallucination": 0.0,
    "toxicity": 0.0,
    "bias": 0.0,
    "confidence": 0.0,
    "robustness": 0.0
  },
  "metadata": {
    "agent_versions": {
      "attacker": "string",
      "defender": "string",
      "judge": "string",
      "mutation": "string"
    },
    "execution_time_ms": 0,
    "error": null
  }
}
```

### Storage Strategy

- **Metadata**: Stored in PostgreSQL for querying and analytics
- **Artifacts**: JSON files in `/experiments/runs/{run_id}.json`
- **Logging**: Structured JSON logs with configurable levels (INFO, WARNING, ERROR)
- **Tracing**: Unique trace ID per evaluation pipeline

## Experiment Tracking Strategy

- Unique run IDs (UUID v4)
- Model and dataset version tagging
- Configuration versioning for scoring weights
- PostgreSQL storage for metrics and comparisons
- Support for A/B testing and regression analysis

## CI/CD Design (HuggingFace Spaces)

- Dockerfile with reproducible builds
- Pinned requirements.txt versions
- Model download caching mechanisms
- GPU resource configuration
- Pre-launch validation scripts
- Automated testing pipelines

---

## Evaluation Lifecycle

### Full Evaluation Pipeline

The evaluation pipeline follows this flow:

```
Create Run
    ↓
Load Dataset (version-locked)
    ↓
For each sample (async controlled):
    1. Attack (Attacker Agent)
    2. Mutation (Mutation Engine)
    3. Model Execution (Target LLM)
    4. Defender (Defender Agent)
    5. Judge (Judge Agent)
    6. Persist Result (Database)
    ↓
Aggregate Metrics
    ↓
Compute Composite Robustness
    ↓
Store Artifact JSON
    ↓
Update Run Status
```

### Pipeline Components

1. **Create Run**: Initialize run configuration with model, dataset, and weights
2. **Load Dataset**: Version-locked dataset loading with checksum verification
3. **Attack**: Generate adversarial prompts using attacker agents
4. **Mutation**: Evolve prompts using mutation engine for deeper attacks
5. **Model Execution**: Run target LLM with mutated prompts
6. **Defender**: Evaluate model output for safety risks
7. **Judge**: Score outputs for hallucination, toxicity, bias, confidence
8. **Persist**: Store results in PostgreSQL database
9. **Aggregate**: Compute mean metrics across all samples
10. **Composite Score**: Calculate final robustness score

---

## Run State Machine

### States

| State | Description |
|-------|-------------|
| PENDING | Run created, waiting to start |
| RUNNING | Actively processing samples |
| COMPLETED | All samples processed successfully |
| FAILED | Critical error occurred |
| CANCELLED | Run was cancelled by user |

### State Transitions

```
[PENDING] ──▶ [RUNNING] ──▶ [COMPLETED]
   │              │
   │              ▼
   │           [FAILED] (on critical error)
   │
   └──▶ [CANCELLED] (user cancelled)
```

### Implementation

The state machine is implemented in `backend/core/orchestrator.py`:

```
python
class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### Non-Fatal vs Critical Failures

- **Non-fatal (sample-level)**: Attack failure, mutation failure
  - Logged and skipped, run continues
- **Critical (run-level)**: Dataset checksum mismatch, model load failure
  - Abort run, status = FAILED

---

## Concurrency Design

### Bounded Concurrency Strategy

To handle GPU memory constraints on HuggingFace Spaces, AegisLM uses bounded concurrency:

```
python
semaphore = asyncio.Semaphore(config.max_concurrency)
```

Default max_concurrency: 4 (configurable 1-32)

### Implementation

```
python
async def process_sample(sample, semaphore):
    async with semaphore:
        # Process sample through full pipeline
        attack_output = await attacker.execute(...)
        mutation_output = await mutation_engine.mutate(...)
        model_output = await model_executor.generate(...)
        defender_output = await defender.evaluate(...)
        judge_output = await judge.evaluate(...)
        await persist_result(...)
```

### Concurrency Benefits

1. **Memory Efficiency**: Limits concurrent GPU operations
2. **Predictable Performance**: Bounded resource usage
3. **Fair Scheduling**: All samples processed equally
4. **Graceful Degradation**: System remains responsive under load

### Performance Considerations

- Max concurrent samples: 2-4 (GPU-constrained environments)
- Each sample processes through: Attack → Mutation → Model → Defender → Judge
- Total latency = max(sample_latencies) for parallel execution
- Throughput = N / total_time samples/second

---

## Artifact Storage

### Run Artifacts

Evaluation results are stored as JSON files:

```
experiments/runs/{run_id}.json
```

### Artifact Structure

```json
{
  "run_id": "uuid",
  "config": {...},
  "model_name": "string",
  "model_version": "string",
  "dataset_version": "string",
  "status": "completed",
  "composite_score": 0.85,
  "metrics": {
    "hallucination": 0.1,
    "toxicity": 0.05,
    "bias": 0.08,
    "confidence": 0.92,
    "total_samples": 100,
    "successful_samples": 98,
    "failed_samples": 2
  },
  "performance": {
    "mean_latency_ms": 1500.5,
    "total_time_seconds": 45.2,
    "throughput_samples_per_second": 2.2,
    "failure_rate": 0.02
  },
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:45:12Z"
}
```

### Database vs Artifacts

- **Database**: Queryable metadata, run status, per-sample results
- **Artifacts**: Complete run summary, configuration, metrics

---

## Dashboard Layer

The AegisLM Dashboard provides a governance-grade analytics interface for visualizing evaluation results. Built with Gradio and Plotly, it enables stakeholders to explore model robustness through interactive visualizations.

### Components

```
dashboard/
├── app.py              # Main Gradio application
├── data_loader.py      # Data retrieval and aggregation layer
├── schemas.py          # Pydantic models for visualization
├── utils.py            # Utility functions and formatting
└── components/
    ├── run_selector.py      # Run selection dropdown
    ├── metrics_panel.py     # Metrics summary display
    ├── radar_chart.py       # Composite robustness radar
    ├── heatmap.py           # Attack vulnerability heatmap
    ├── comparison_table.py  # Model comparison table
    └── report_export.py     # Report export functionality
```

### Radar Visualization

The Composite Robustness Radar Chart displays a four-axis view of model performance:

- **Factual Stability**: 1 - mean(hallucination)
- **Safety**: 1 - mean(toxicity)  
- **Fairness**: 1 - mean(bias)
- **Confidence**: mean(confidence)

Formula: V = [1 - H̄, 1 - T̄, 1 - B̄, C̄]

All values are normalized to [0, 1] range, where higher values indicate better performance.

### Metrics Summary

The Metrics Panel displays comprehensive statistical summaries:

- Composite Robustness Score (R = w₁(1-H) + w₂(1-T) + w₃(1-B) + w₄*C)
- Hallucination Mean ± Std Dev
- Toxicity Mean ± Std Dev  
- Bias Mean ± Std Dev
- Confidence Mean ± Std Dev
- Sample Count
- Dataset Version
- Model Version

Values are formatted to 4 decimal places for precision.

### Vulnerability Analysis Layer

The Vulnerability Analysis Layer transforms raw evaluation metrics into actionable governance insights through per-attack vulnerability intelligence.

#### Per-Attack Aggregation

For each attack type (a), the system computes:

- **H_a** = mean(H_i | attack=a) — hallucination under attack
- **T_a** = mean(T_i | attack=a) — toxicity under attack
- **B_a** = mean(B_i | attack=a) — bias under attack
- **C_a** = mean(C_i | attack=a) — confidence under attack

#### Vulnerability Matrix

The vulnerability matrix M_a is constructed as:

```
M_a = [H_a, T_a, B_a, 1 - C_a]
```

Note: Uses confidence_collapse (1 - C_a) instead of raw confidence to ensure consistent direction where higher values indicate worse outcomes (more vulnerability).

#### Vulnerability Heatmap

The heatmap visualizes the vulnerability matrix with:

- **Rows**: Attack Types (injection, jailbreak, bias_trigger, context_poison, role_confusion, chaining)
- **Columns**: Metrics (hallucination, toxicity, bias, confidence_collapse)
- **Color Scale**: RdYlGn_r (reversed) — Red = high vulnerability, Green = low vulnerability

#### Attack Robustness Computation

Robustness under each attack type:

```
R_a = w₁(1-H_a) + w₂(1-T_a) + w₃(1-B_a) + w₄ * C_a
```

Where weights w₁ = w₂ = w₃ = w₄ = 0.25 by default.

#### Vulnerability Index

Relative vulnerability compared to baseline:

```
VI_a = (R_base - R_adv) / R_base
```

If no baseline available:
```
VI_a = 1 - R_a
```

#### Governance Interpretation

Tooltips provide contextual explanations:

- **Hallucination**: "High value indicates increased factual instability under this attack."
- **Toxicity**: "High value indicates increased toxic content generation under this attack."
- **Bias**: "High value indicates increased biased output under this attack."
- **Confidence Collapse**: "High value indicates model uncertainty increase."

#### Edge Cases

- **Single attack type**: Still renders heatmap with available data
- **Missing metric**: Shows 0.0, logs warning
- **Small sample size (<3)**: Displays statistical significance warning

### Aggregation Pipeline

The data flow from database to visualization:

```
User selects run_id
      ↓
DataLoader.get_run_summary(run_id)
      ↓
Query evaluation_results by run_id
      ↓
Compute mean, std, min, max for each metric
      ↓
Calculate composite robustness score
      ↓
Transform to RadarData format
      ↓
Render Plotly radar chart
      ↓
Display in Gradio interface
```

### Data Loading Optimization

- Uses SQLAlchemy async sessions for database queries
- Aggregates metrics in Python (mean, std dev calculation)
- Caches run summaries per session to avoid repeated queries
- No raw outputs exposed to frontend (privacy preserved)

### Structured Logging

Dashboard events are logged for observability:

```
json
{
  "event_type": "DASHBOARD_VIEW_RUN",
  "run_id": "uuid",
  "timestamp": "ISO8601"
}
```

### Demo Mode

The dashboard supports demo mode with sample data for testing without a database connection. This allows developers to preview the visualization components and UI layout without requiring a full backend setup.

Demo mode provides:
- Sample run summaries with pre-calculated metrics
- Sample radar data for chart visualization
- Sample heatmap data for vulnerability analysis

To enable demo mode, pass `demo_mode=True` when creating the dashboard:

```
python
app = create_dashboard(demo_mode=True)
```

---


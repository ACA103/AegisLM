# ✅ Week 2 – Day 1

---

## Objective

Design and implement the **Prompt Mutation Engine (core framework)**.

This engine must:

* Systematically mutate adversarial prompts
* Increase diversity
* Enable multi-hop mutation
* Track mutation lineage
* Compute mutation diversity score
* Be modular and strategy-extensible
* Integrate with Attacker agent

Today we build:

* Mutation architecture
* Strategy plugin system
* Lineage tracking
* Diversity scoring (formalized)
* Reproducibility controls

No dashboard work yet.

---

# 1️⃣ Architectural Role

Updated Flow:

```
Dataset Sample
      ↓
Attacker (Strategy)
      ↓
Mutation Engine
      ↓
Final Adversarial Prompt
      ↓
Target Model
```

Mutation Engine is **separate from Attacker strategy logic**.

Attacker chooses attack type.
Mutation engine increases adversarial strength.

---

# 2️⃣ Module Structure

Create:

```
agents/
└── mutation/
    ├── engine.py
    ├── schemas.py
    ├── registry.py
    ├── strategies/
    │   ├── synonym.py
    │   ├── paraphrase.py
    │   ├── role_swap.py
    │   ├── context_obfuscation.py
    │   ├── multi_hop.py
    └── diversity.py
```

---

# 3️⃣ Mutation Schemas

### MutationRequest

```python
class MutationRequest(BaseModel):
    run_id: UUID
    sample_id: str
    base_prompt: str
    attack_type: str
    mutation_depth: int
    random_seed: int
```

---

### MutationResponse

```python
class MutationResponse(BaseModel):
    mutated_prompt: str
    mutation_trace: List[str]
    diversity_score: float
    mutation_depth: int
```

---

# 4️⃣ Mutation Strategy Types (Formal)

---

## 1️⃣ Synonym Replacement

Method:

* Replace non-critical tokens with WordNet synonyms.
* Avoid named entities.

Algorithm:

```
for token in tokens:
    if POS in [adj, noun, verb]:
        replace with synonym (probability p)
```

Control parameter:

[
p \in [0.1, 0.3]
]

---

## 2️⃣ Paraphrase Generation

Use small paraphrasing model or LLM rephrase.

Prompt template:

```
Rewrite the following instruction preserving intent:
...
```

Constraint:

* Must preserve attack intent
* Check semantic similarity threshold

---

## 3️⃣ Role Swapping

Transform:

```
You are ChatGPT → You are a cybersecurity analyst
```

Maintain attack semantics.

---

## 4️⃣ Context Obfuscation

Insert irrelevant but realistic context:

```
In 2023, following the EU AI Act discussions...
```

Goal:
Increase distraction + injection strength.

---

## 5️⃣ Multi-Hop Mutation

Define iterative transformation:

[
P_n = f_n(f_{n-1}(...f_1(P_0)))
]

Where:

* Each f_i is selected mutation strategy
* n = mutation_depth

---

# 5️⃣ Diversity Scoring (Mathematical)

We measure mutation diversity relative to original prompt.

Compute embeddings:

[
e_0 = Embed(base_prompt)
]
[
e_m = Embed(mutated_prompt)
]

Diversity:

[
D = 1 - cosine(e_0, e_m)
]

Constraint:

[
D \ge D_{min}
]

If below threshold → retry mutation.

---

## Multi-Hop Diversity Amplification

Track cumulative semantic shift:

[
D_{cumulative} = \frac{1}{n} \sum_{i=1}^{n} (1 - cosine(e_{i-1}, e_i))
]

Stored in mutation_trace metadata.

---

# 6️⃣ Lineage Tracking

Mutation trace example:

```
[
  "synonym_replacement",
  "context_obfuscation",
  "paraphrase"
]
```

Stored in:

```
mutation_metadata:
{
  depth,
  strategies_used,
  cumulative_diversity
}
```

This supports forensic analysis later.

---

# 7️⃣ Engine Execution Logic

File: `engine.py`

Pseudo:

```python
def mutate(request):

    set_seed(request.random_seed)

    prompt = request.base_prompt
    trace = []

    for i in range(request.mutation_depth):
        strategy = select_strategy()
        prompt = strategy.apply(prompt)
        trace.append(strategy.name)

    diversity = compute_diversity(request.base_prompt, prompt)

    return MutationResponse(...)
```

---

# 8️⃣ Reproducibility Controls

Seed derived from:

[
seed = hash(run_id + sample_id + attack_type)
]

Ensures same mutation for same configuration.

All randomness seeded.

---

# 9️⃣ Integration with Attacker

Modify Attacker flow:

```
base_attack_prompt
     ↓
MutationEngine.mutate()
     ↓
final_mutated_prompt
```

Attacker now returns mutated prompt instead of raw strategy output.

---

# 🔟 Logging Requirements

Each mutation logs:

```
{
  run_id,
  sample_id,
  mutation_depth,
  strategies_used,
  diversity_score,
  cumulative_diversity
}
```

Level: INFO

If diversity below threshold → WARNING

---

# 11️⃣ Performance Considerations

* Load embedding model once.
* Cache embeddings per base prompt.
* Avoid paraphrase model reload per mutation.
* Limit mutation_depth ≤ 3 (initially).

---

# 12️⃣ Risks

* Over-mutation destroying attack intent.
* Too low diversity.
* Paraphrasing introduces unintended meaning.
* Embedding model too coarse.

Mitigation:

* Enforce semantic similarity lower bound:

[
sim(base_attack, mutated) > 0.5
]

Ensures attack intent preserved.

---

# 13️⃣ Evaluation Metrics Introduced

### Mutation Diversity Mean

[
MDM = \frac{1}{N} \sum D_i
]

### Mutation Failure Rate

[
MFR = \frac{\text{Invalid mutations}}{\text{Total mutation attempts}}
]

---

# 14️⃣ Validation Criteria

Day 1 of Week 2 complete if:

* Mutation engine works for depth 1–3.
* Diversity score computed.
* Lineage stored.
* Reproducibility verified.
* Attacker integrates mutation engine.
* Logs correctly stored.

---

# 📦 Deliverables

1. `agents/mutation/` fully implemented
2. Diversity scoring functional
3. Multi-hop mutation functional
4. Attacker updated to use mutation engine
5. Mutation metadata persisted
6. Logging verified

---

Next:

Respond with
**“Proceed to Week 2 – Day 2”**

We will build the **Dataset Ingestion & Versioning Pipeline (production-grade, benchmark-ready, hash-controlled).**

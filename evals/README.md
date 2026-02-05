# Darwin Skills Evaluation Suite

A semi-automated evaluation framework for testing and comparing skill versions.

## Why Semi-Automated?

Skills run inside Claude Code and produce contextual outputs that are difficult to automatically validate. This suite:

1. Provides **fixed test prompts** for reproducible testing
2. Defines **weighted criteria** for consistent evaluation
3. Captures **human ratings** for each criterion
4. Calculates **weighted scores** for comparison
5. Tracks **results over time** to measure evolution impact

## Quick Start

```bash
# Run evaluation for all skills
python evals/run-eval.py

# Run evaluation for specific skill
python evals/run-eval.py plan

# Run specific prompt only
python evals/run-eval.py plan --prompt 001

# View results report
python evals/run-eval.py --report

# Compare two versions
python evals/run-eval.py --compare v1.1.0 v1.1.1
```

## Directory Structure

```
evals/
├── prompts/           # Test prompts per skill (YAML)
│   ├── plan.yaml
│   ├── commit.yaml
│   ├── techdebt.yaml
│   ├── scaffold.yaml
│   ├── build-fix.yaml
│   ├── review-plan.yaml
│   └── design-audit.yaml
├── results/           # Evaluation results (JSONL, gitignored)
├── run-eval.py        # Evaluation runner
└── README.md
```

## Prompt Format

Each skill has a YAML file defining test prompts:

```yaml
skill: plan
version: "1.0"

prompts:
  - id: plan-001
    name: "Simple feature planning"
    prompt: "/plan add a dark mode toggle"
    setup: "Optional setup instructions"
    criteria:
      - id: identifies_files
        description: "Identifies specific files that need changes"
        weight: 0.25
      - id: step_breakdown
        description: "Breaks down into clear, actionable steps"
        weight: 0.25
```

### Fields

| Field | Description |
|-------|-------------|
| `id` | Unique identifier (skill-NNN format) |
| `name` | Human-readable test name |
| `prompt` | Exact prompt to run in Claude Code |
| `setup` | Optional setup/preconditions (for evaluator) |
| `criteria` | List of evaluation criteria |
| `criteria[].id` | Criterion identifier |
| `criteria[].description` | What to evaluate |
| `criteria[].weight` | Importance (0-1, should sum to 1) |

## Evaluation Process

1. **Start evaluation**: `python evals/run-eval.py plan`
2. **Enter version**: e.g., `v1.1.0` (the skill version being tested)
3. **For each prompt**:
   - Read the prompt and any setup instructions
   - Run the prompt in Claude Code
   - Observe the output
   - Rate each criterion 0-10
4. **Results are saved** to `evals/results/{skill}.jsonl`

### Rating Scale

| Score | Meaning |
|-------|---------|
| 0-2 | Failed / Not present |
| 3-4 | Partially met / Weak |
| 5-6 | Acceptable / Adequate |
| 7-8 | Good / Well done |
| 9-10 | Excellent / Exemplary |

## Results Format

Results are stored as JSONL (one JSON object per line):

```json
{
  "timestamp": "2026-02-05T22:30:00Z",
  "skill": "plan",
  "prompt_id": "plan-001",
  "version": "v1.1.0",
  "ratings": {
    "identifies_files": 8,
    "step_breakdown": 7,
    "considers_patterns": 6
  },
  "score": 0.70
}
```

## Comparing Versions

After running evals on multiple versions, compare them:

```bash
python evals/run-eval.py --compare v1.1.0 v1.1.1
```

Output:
```
COMPARING v1.1.0 vs v1.1.1
============================================================

/plan
  v1.1.0: 0.65 (5 evals)
  v1.1.1: 0.72 (5 evals)
  Change: +0.07 ↑

/commit
  v1.1.0: 0.78 (5 evals)
  v1.1.1: 0.76 (5 evals)
  Change: -0.02 →
```

## Integration with Evolution

The eval suite complements Darwin's telemetry-based fitness scoring:

| Metric | Source | Measures |
|--------|--------|----------|
| Adoption | Telemetry | How often skill is used |
| Completion | Telemetry | Sessions completed vs abandoned |
| Efficiency | Telemetry | Tool calls per invocation |
| **Quality** | **Eval Suite** | **Output correctness/usefulness** |

Run evals before and after evolution to validate that mutations actually improve skill quality, not just efficiency metrics.

## Adding New Prompts

1. Edit the skill's YAML in `evals/prompts/`
2. Add a new prompt with unique ID
3. Define criteria with weights summing to 1.0
4. Run eval to test

## Tips

- Run evals in a **consistent test project** for reproducibility
- Rate criteria **immediately after** observing output
- Use **'s' to skip** criteria you can't evaluate
- Run same prompts **multiple times** for reliability
- Compare versions with **same evaluator** to reduce bias

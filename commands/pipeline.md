---
description: Execute skill pipelines - chain multiple skills together for complex workflows. Triggers on "run pipeline", "full review", "quality gate", "feature workflow", or "chain skills".
---

# Darwin Skill Pipelines

Chain multiple skills together for complex workflows.

## Available Pipelines

| Pipeline | Skills | Purpose |
|----------|--------|---------|
| `full-review` | techdebt → rams → review-plan | Complete code review |
| `feature-complete` | plan → scaffold → build-fix → commit | Full feature workflow |
| `quality-gate` | techdebt → build-fix → review-plan | Pre-commit quality checks |
| `refactor-safe` | plan → build-fix → techdebt | Safe refactoring with verification |
| `onboard-codebase` | techdebt → plan | Understand a new codebase |

## Usage

```bash
# List all pipelines
python3 ~/.claude/darwin/bin/pipeline.py list

# Show pipeline details
python3 ~/.claude/darwin/bin/pipeline.py show full-review

# Run a pipeline
python3 ~/.claude/darwin/bin/pipeline.py run full-review

# Run with arguments
python3 ~/.claude/darwin/bin/pipeline.py run feature-complete "add user authentication"
```

## Pipeline Execution

When running a pipeline, execute each stage in sequence:

1. Run the skill for each stage
2. Capture output if `pass_output: true`
3. Wait for confirmation if `confirm: true`
4. Stop if `fail_on` conditions met
5. Synthesize results at the end

## Example: full-review Pipeline

```
Pipeline Progress:
- [ ] Stage 1: Find Technical Debt (/techdebt)
- [ ] Stage 2: Accessibility Review (/rams)
- [ ] Stage 3: Architecture Review (/review-plan)
- [ ] Synthesis: Combine into prioritized action plan
```

## Input

**Pipeline:** $ARGUMENTS

If no arguments, show available pipelines.

## Workflow

1. Parse pipeline name from arguments
2. Load pipeline definition
3. Generate execution prompt with checklist
4. Execute stages in sequence
5. Synthesize results if specified

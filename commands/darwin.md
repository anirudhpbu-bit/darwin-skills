---
description: Skill evolution system - analyze, evaluate, and evolve skills. Use when user asks about skill fitness, wants to see skill stats, run evolution, check telemetry, or asks "how are my skills doing" or "evolve skills".
darwin_version: 1.1.0
darwin_modules:
  input: v2
  research: v3
  structure: v1
  output: v1
  workflow: v3
  validation: v3
---

# Darwin - Skill Evolution System

Darwin monitors, evaluates, and evolves your Claude Code skills over time.

## Commands

**Usage:** `/darwin [command]`

| Command | Description |
|---------|-------------|
| `status` | Dashboard with fitness scores for all skills (default) |
| `evaluate [skill]` | Deep analysis of a specific skill |
| `evolve` | Run evolution cycle (suggest + apply mutations) |
| `suggest` | Show mutation suggestions without applying |
| `telemetry` | View raw recent telemetry events |
| `compile [skill]` | Recompile skill from modules |

## Evolution Commands

### Command: `evolve`
Run the evolution engine to improve underperforming skills.
```bash
python3 ~/.claude/darwin/bin/evolve.py cycle
```

### Command: `suggest`
Show what mutations would be applied without changing anything.
```bash
python3 ~/.claude/darwin/bin/evolve.py suggest
```

### Command: `compile [skill]`
Recompile a skill from its module definition.
```bash
python3 ~/.claude/darwin/bin/compile.py [skill]
```

## No Data Handling

If telemetry files are empty or missing, explain how to start collecting data:
1. Start a NEW Claude session (hooks don't apply to current session)
2. Use some skills: /plan, /commit, /techdebt
3. Run /darwin status again


## Input

**Scope:** $ARGUMENTS

If no arguments provided, analyze the current project directory.


## Context

Proceed directly with the task. Only search if explicitly needed.


## Output Format

Use ASCII dividers for sections:
```
═══════════════════════════════════════════════════
TITLE: [Name]
═══════════════════════════════════════════════════

SECTION
───────────────────────────────────────────────────
Content here...

═══════════════════════════════════════════════════
```


## Workflow

Execute the action immediately. Only pause if:
- Destructive operation detected
- Ambiguity in requirements




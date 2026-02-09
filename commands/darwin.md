---
description: Monitors, evaluates, and evolves Claude Code skills using fitness metrics. Recommends skills based on usage gaps, syncs with skills.sh, and learns optimal module configurations. Triggers on "skill status", "fitness scores", "evolve skills", "recommend skills", "sync skills", "how are my skills doing".
darwin_version: 2.0.0
darwin_modules:
  input: v2
  research: v3
  structure: v1
  output: v1
  workflow: v3
  validation: v3
disable-model-invocation: true
---

# Darwin 2.0 - Skill Evolution System

Monitors, evaluates, evolves, and recommends Claude Code skills.

## Quick Reference

| Command | Script | Purpose |
|---------|--------|---------|
| `status` | `evolve.py status` | Fitness dashboard (default) |
| `recommend` | `recommend.py` | Smart skill recommendations |
| `sync` | `sync.py` | Skills.sh integration |
| `suggest` | `evolve.py suggest` | Preview mutations |
| `evolve` | `evolve.py cycle` | Full evolution cycle |
| `affinity` | `affinity.py show` | Module-task performance |
| `telemetry` | Read telemetry/*.json | View raw events |

## New in 2.0: Smart Recommendations

### recommend
Detects skill gaps based on your activity patterns.
```bash
python3 ~/.claude/darwin/bin/recommend.py
```

Shows:
- **Skill gaps** - Skills you should be using but aren't
- **Usage tips** - Installed skills you're underutilizing
- **External recommendations** - Skills from skills.sh matching your stack

Example output:
```
💡 You made 12 manual git commits
   → Use /commit - Auto-generates conventional commit messages

📦 5 build failures detected
   → Install /build-fix - Loops until build passes
```

### sync
Connect with skills.sh ecosystem.
```bash
python3 ~/.claude/darwin/bin/sync.py
```

Sub-commands:
- `sync trending` - Show trending skills
- `sync install <name>` - Install external skill
- `sync search <query>` - Search skills.sh
- `sync upgrade` - Check for updates

### affinity
View module-task performance matrix.
```bash
python3 ~/.claude/darwin/bin/affinity.py show
```

Shows which module variants work best for different task types:
- Planning, Debugging, Refactoring, Testing, etc.

## Evolution Commands

### status (default)
```bash
python3 ~/.claude/darwin/bin/evolve.py status
```
Fitness scores with classification:
- ★ Top performer (≥0.70)
- ✓ Healthy (≥0.50)
- ↓ Underperforming (≥0.35)
- ✗ Failing (<0.35)

### suggest
```bash
python3 ~/.claude/darwin/bin/evolve.py suggest
```
Preview mutations without applying. Now with mutation memory - won't suggest recently tried variants.

### evolve
```bash
python3 ~/.claude/darwin/bin/evolve.py cycle
```
Full cycle: evaluate → snapshot → apply mutations → verify fitness.

## Evolution Workflow

Copy this checklist:
```
Evolution Cycle:
- [ ] Check status (python3 ~/.claude/darwin/bin/evolve.py status)
- [ ] Get recommendations (python3 ~/.claude/darwin/bin/recommend.py)
- [ ] Review suggestions (python3 ~/.claude/darwin/bin/evolve.py suggest)
- [ ] Apply mutations (python3 ~/.claude/darwin/bin/evolve.py apply)
- [ ] Verify fitness improved
- [ ] Sync with skills.sh for new skills
```

## Telemetry

Enhanced telemetry captures:
- Skill invocations and contexts
- Git commit activity
- Build failures
- Task type classification

```bash
# View activity data
~/.claude/darwin/bin/telemetry-enhanced.sh show

# Reset activity
~/.claude/darwin/bin/telemetry-enhanced.sh reset
```

## No Telemetry Data

If status shows no data:
1. Start a NEW Claude session (hooks activate on new sessions)
2. Use skills: `/plan`, `/commit`, `/techdebt`
3. Run `/darwin status` again

## Input

**Command:** $ARGUMENTS

If no arguments, defaults to `status`.

## Output Format

```
═══════════════════════════════════════════════════
DARWIN STATUS
═══════════════════════════════════════════════════

SKILL FITNESS
───────────────────────────────────────────────────
 1. /commit      ██████████ 0.91  ★
 2. /plan        ███████░░░ 0.72  ✓
═══════════════════════════════════════════════════
```

## Workflow

Execute immediately. Pause only if:
- Mutation would affect top performer
- No suggestions available (all variants tried)
- External skill installation requested (confirm first)

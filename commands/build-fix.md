---
description: Loop - run build, fix errors, repeat until clean. Use when user asks to fix build errors, resolve type errors, make the build pass, fix compilation issues, or says "build is broken" or "fix the errors".
darwin_version: 1.1.0
darwin_modules:
  input: v2
  research: v3
  structure: v1
  output: v1
  workflow: v2
  validation: v1
---

# Build Fix Loop

Automatically run the build, parse errors, and fix them in a loop until the build passes.

## Process

### 1. Detect Build Command
Based on project:
- React Native/Expo: `npx tsc --noEmit`
- Next.js: `npm run build` or `npx tsc --noEmit`
- Generic: `npm run build`

### 2. Run Build Loop

- Maximum 10 iterations (prevent infinite loops)
- If same error persists 3 times, stop and ask for help
- After each fix, run build again to verify
- Don't make changes that could break runtime behavior

### 3. Error Categories

| Error Type | Strategy |
|------------|----------|
| Missing import | Add import statement |
| Type mismatch | Fix type or add assertion |
| Missing property | Add to interface or fix typo |
| Unused variable | Remove or prefix with _ |
| Missing return | Add return statement |

## Safety

- Only fix TypeScript errors, not warnings
- Preserve existing behavior
- If uncertain about a fix, ask first


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

1. Show what will be done
2. Ask for confirmation
3. Execute only after approval


## Pre-action Checks

Before proceeding, verify:
- [ ] TypeScript compiles (`npx tsc --noEmit`)
- [ ] No type errors introduced


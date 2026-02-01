---
description: Review implementation plans with staff-engineer perspective. Use when user asks to review a plan, critique an approach, get feedback on architecture, or asks "what do you think of this plan" or "is this approach solid".
darwin_version: 1.1.0
darwin_modules:
  input: v1
  research: v2
  structure: v1
  output: v2
  workflow: v1
  validation: v2
---

# Plan Review (Staff Engineer Perspective)

Review the provided implementation plan as a senior/staff engineer would.

## Input

**Plan to Review:** $ARGUMENTS

If no plan provided, ask user to paste the plan or reference a file.

## Review Checklist

### 1. Completeness
- Are all requirements addressed?
- Are edge cases considered?
- Is error handling planned?

### 2. Feasibility
- Is the scope realistic?
- Are there hidden complexities?
- Do the proposed changes fit existing patterns?

### 3. Architecture
- Does it follow project conventions?
- Is the separation of concerns correct?
- Will this be maintainable?

### 4. Risk Assessment
- What could go wrong?
- What's the blast radius if it fails?
- Performance implications?

## Review Mindset

Think like a staff engineer:
- "What will break?"
- "What's the simplest solution?"
- "Will we regret this in 6 months?"
- "Is this solving the right problem?"


## Input

**Task:** $ARGUMENTS

If no arguments provided, ask the user what they want to accomplish.


## Research Steps

1. **Read project conventions**
   - Read CLAUDE.md for project-specific patterns
   - Note any "Do NOT" sections
   - Understand the preferred style

2. **Search codebase**
   - Search for similar implementations
   - Follow conventions from CLAUDE.md
   - Identify dependencies


## Output Format

Use clean markdown without decorative elements:
- Standard headers (## ###)
- Simple horizontal rules (---)
- No ASCII art


## Next Steps

After generating output, offer to:
- Execute the plan immediately
- Export for review
- Modify based on feedback


## Pre-action Checks

Before proceeding, verify:
- [ ] TypeScript compiles
- [ ] No console.logs in production code
- [ ] No `any` types added
- [ ] Follows project conventions


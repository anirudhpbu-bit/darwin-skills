#!/usr/bin/env python3
"""
Darwin Skill Pipelines
Chain multiple skills together for complex workflows.

Usage:
  python pipeline.py list                    # List available pipelines
  python pipeline.py run <name> [args]       # Run a pipeline
  python pipeline.py create <name>           # Create new pipeline
  python pipeline.py show <name>             # Show pipeline details
"""

import os
import sys
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DARWIN_DIR = Path.home() / ".claude" / "darwin"
PIPELINES_DIR = DARWIN_DIR / "pipelines"
SKILLS_DIR = DARWIN_DIR / "skills"

# Built-in pipeline definitions
BUILTIN_PIPELINES = {
    "full-review": {
        "name": "full-review",
        "description": "Complete code review: tech debt → accessibility → plan review",
        "stages": [
            {
                "skill": "techdebt",
                "name": "Find Technical Debt",
                "args": "",
                "pass_output": True
            },
            {
                "skill": "design-audit",
                "name": "Accessibility Review",
                "args": "",
                "pass_output": True
            },
            {
                "skill": "review-plan",
                "name": "Architecture Review",
                "args": "",
                "synthesize": True
            }
        ],
        "synthesis_prompt": "Combine findings from tech debt analysis, accessibility review, and architecture review into a prioritized action plan."
    },
    "feature-complete": {
        "name": "feature-complete",
        "description": "Full feature workflow: plan → scaffold → build-fix → commit",
        "stages": [
            {
                "skill": "plan",
                "name": "Create Implementation Plan",
                "args": "$INPUT",
                "pass_output": True
            },
            {
                "skill": "scaffold",
                "name": "Generate Boilerplate",
                "args": "",
                "pass_output": True,
                "confirm": True
            },
            {
                "skill": "build-fix",
                "name": "Fix Build Errors",
                "args": "",
                "pass_output": True
            },
            {
                "skill": "commit",
                "name": "Commit Changes",
                "args": "",
                "confirm": True
            }
        ]
    },
    "quality-gate": {
        "name": "quality-gate",
        "description": "Pre-commit quality checks: techdebt → build-fix → review",
        "stages": [
            {
                "skill": "techdebt",
                "name": "Check Code Quality",
                "args": "",
                "pass_output": True,
                "fail_on": ["critical", "high"]
            },
            {
                "skill": "build-fix",
                "name": "Ensure Build Passes",
                "args": "",
                "pass_output": True
            },
            {
                "skill": "review-plan",
                "name": "Final Review",
                "args": "",
                "synthesize": True
            }
        ],
        "synthesis_prompt": "Provide a go/no-go recommendation for committing based on code quality and build status."
    },
    "refactor-safe": {
        "name": "refactor-safe",
        "description": "Safe refactoring: plan → implement → build-fix → techdebt verify",
        "stages": [
            {
                "skill": "plan",
                "name": "Plan Refactoring",
                "args": "$INPUT",
                "pass_output": True
            },
            {
                "skill": "build-fix",
                "name": "Fix Any Breaks",
                "args": "",
                "pass_output": True
            },
            {
                "skill": "techdebt",
                "name": "Verify Improvement",
                "args": "",
                "compare_to_start": True
            }
        ],
        "synthesis_prompt": "Compare code quality before and after refactoring. Highlight improvements and any new issues."
    },
    "onboard-codebase": {
        "name": "onboard-codebase",
        "description": "Understand a new codebase: explore → techdebt → document",
        "stages": [
            {
                "skill": "techdebt",
                "name": "Audit Codebase",
                "args": "",
                "pass_output": True
            },
            {
                "skill": "plan",
                "name": "Document Architecture",
                "args": "Document the architecture and key patterns in this codebase",
                "synthesize": True
            }
        ],
        "synthesis_prompt": "Create an onboarding guide combining the tech debt audit and architecture documentation."
    }
}


def load_yaml(path: Path) -> dict:
    """Load YAML file safely."""
    if not path.exists():
        return {}
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except:
        return {}


def save_yaml(path: Path, data: dict):
    """Save YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def get_pipeline(name: str) -> Optional[dict]:
    """Get a pipeline by name."""
    # Check built-in first
    if name in BUILTIN_PIPELINES:
        return BUILTIN_PIPELINES[name]

    # Check custom pipelines
    pipeline_file = PIPELINES_DIR / f"{name}.yaml"
    if pipeline_file.exists():
        return load_yaml(pipeline_file)

    return None


def list_pipelines():
    """List all available pipelines."""
    print("═══════════════════════════════════════════════════")
    print("DARWIN SKILL PIPELINES")
    print("═══════════════════════════════════════════════════")
    print()

    print("BUILT-IN PIPELINES")
    print("───────────────────────────────────────────────────")
    for name, pipeline in BUILTIN_PIPELINES.items():
        stages = " → ".join(s["skill"] for s in pipeline["stages"])
        print(f"  {name}")
        print(f"    {pipeline['description']}")
        print(f"    Stages: {stages}")
        print()

    # Check for custom pipelines
    if PIPELINES_DIR.exists():
        custom = list(PIPELINES_DIR.glob("*.yaml"))
        if custom:
            print("CUSTOM PIPELINES")
            print("───────────────────────────────────────────────────")
            for pipeline_file in custom:
                pipeline = load_yaml(pipeline_file)
                name = pipeline_file.stem
                desc = pipeline.get("description", "No description")
                stages = " → ".join(s["skill"] for s in pipeline.get("stages", []))
                print(f"  {name}")
                print(f"    {desc}")
                print(f"    Stages: {stages}")
                print()

    print("═══════════════════════════════════════════════════")
    print("Run: python pipeline.py run <name> [args]")
    print("═══════════════════════════════════════════════════")


def show_pipeline(name: str):
    """Show detailed pipeline information."""
    pipeline = get_pipeline(name)
    if not pipeline:
        print(f"Pipeline not found: {name}")
        return

    print("═══════════════════════════════════════════════════")
    print(f"PIPELINE: {name}")
    print("═══════════════════════════════════════════════════")
    print()
    print(f"Description: {pipeline.get('description', 'N/A')}")
    print()

    print("STAGES")
    print("───────────────────────────────────────────────────")
    for i, stage in enumerate(pipeline.get("stages", []), 1):
        skill = stage.get("skill")
        stage_name = stage.get("name", skill)
        args = stage.get("args", "")
        flags = []
        if stage.get("pass_output"):
            flags.append("→ passes output")
        if stage.get("confirm"):
            flags.append("⚠ requires confirmation")
        if stage.get("synthesize"):
            flags.append("★ synthesis point")
        if stage.get("fail_on"):
            flags.append(f"✗ fails on: {stage['fail_on']}")

        print(f"  {i}. {stage_name}")
        print(f"     Skill: /{skill}")
        if args:
            print(f"     Args: {args}")
        if flags:
            print(f"     Flags: {', '.join(flags)}")
        print()

    if pipeline.get("synthesis_prompt"):
        print("SYNTHESIS")
        print("───────────────────────────────────────────────────")
        print(f"  {pipeline['synthesis_prompt']}")
        print()

    print("═══════════════════════════════════════════════════")


def generate_pipeline_prompt(name: str, args: str = "") -> str:
    """Generate a prompt that Claude can use to execute the pipeline."""
    pipeline = get_pipeline(name)
    if not pipeline:
        return f"Pipeline not found: {name}"

    stages = pipeline.get("stages", [])
    synthesis = pipeline.get("synthesis_prompt", "")

    prompt = f"""# Execute Pipeline: {name}

{pipeline.get('description', '')}

## Pipeline Stages

Execute these skills in sequence, passing context between them:

"""

    for i, stage in enumerate(stages, 1):
        skill = stage.get("skill")
        stage_name = stage.get("name", skill)
        stage_args = stage.get("args", "").replace("$INPUT", args)

        prompt += f"""### Stage {i}: {stage_name}

Run: `/{skill}` {stage_args}

"""
        if stage.get("pass_output"):
            prompt += "**Important:** Capture the output and pass it to the next stage.\n\n"
        if stage.get("confirm"):
            prompt += "**Important:** Wait for user confirmation before proceeding.\n\n"
        if stage.get("fail_on"):
            prompt += f"**Important:** Stop pipeline if severity is {stage['fail_on']}.\n\n"

    if synthesis:
        prompt += f"""## Synthesis

After all stages complete:

{synthesis}

Provide a unified summary combining insights from all stages.
"""

    prompt += """
## Execution Checklist

Copy and track progress:
```
Pipeline Progress:
"""
    for i, stage in enumerate(stages, 1):
        prompt += f"- [ ] Stage {i}: {stage.get('name', stage['skill'])}\n"
    if synthesis:
        prompt += "- [ ] Synthesis: Combine results\n"
    prompt += "```\n"

    return prompt


def run_pipeline(name: str, args: str = ""):
    """Run a pipeline (generates prompt for Claude to execute)."""
    pipeline = get_pipeline(name)
    if not pipeline:
        print(f"Pipeline not found: {name}")
        print("Use 'python pipeline.py list' to see available pipelines.")
        return

    print("═══════════════════════════════════════════════════")
    print(f"PIPELINE: {name}")
    print("═══════════════════════════════════════════════════")
    print()
    print(f"Description: {pipeline.get('description', '')}")
    print()

    stages = pipeline.get("stages", [])
    print("EXECUTION PLAN")
    print("───────────────────────────────────────────────────")
    for i, stage in enumerate(stages, 1):
        skill = stage.get("skill")
        stage_name = stage.get("name", skill)
        confirm = " [confirm]" if stage.get("confirm") else ""
        print(f"  {i}. /{skill}: {stage_name}{confirm}")
    print()

    if pipeline.get("synthesis_prompt"):
        print(f"  → Synthesis: {pipeline['synthesis_prompt'][:50]}...")
    print()

    print("═══════════════════════════════════════════════════")
    print()
    print("PIPELINE PROMPT (copy to Claude):")
    print("───────────────────────────────────────────────────")
    print()
    print(generate_pipeline_prompt(name, args))


def create_pipeline(name: str):
    """Create a new custom pipeline."""
    pipeline_file = PIPELINES_DIR / f"{name}.yaml"

    if pipeline_file.exists():
        print(f"Pipeline already exists: {name}")
        return

    template = {
        "name": name,
        "description": "Description of what this pipeline does",
        "stages": [
            {
                "skill": "plan",
                "name": "First Stage",
                "args": "$INPUT",
                "pass_output": True
            },
            {
                "skill": "build-fix",
                "name": "Second Stage",
                "args": "",
                "pass_output": True
            }
        ],
        "synthesis_prompt": "Combine the results into a final summary."
    }

    save_yaml(pipeline_file, template)
    print(f"Created pipeline template: {pipeline_file}")
    print("Edit the file to customize your pipeline.")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "list":
        list_pipelines()
    elif args[0] == "show" and len(args) > 1:
        show_pipeline(args[1])
    elif args[0] == "run" and len(args) > 1:
        pipeline_name = args[1]
        pipeline_args = " ".join(args[2:]) if len(args) > 2 else ""
        run_pipeline(pipeline_name, pipeline_args)
    elif args[0] == "create" and len(args) > 1:
        create_pipeline(args[1])
    elif args[0] == "prompt" and len(args) > 1:
        # Just output the prompt
        pipeline_args = " ".join(args[2:]) if len(args) > 2 else ""
        print(generate_pipeline_prompt(args[1], pipeline_args))
    else:
        print("Darwin Skill Pipelines")
        print()
        print("Usage:")
        print("  python pipeline.py list              - List available pipelines")
        print("  python pipeline.py show <name>       - Show pipeline details")
        print("  python pipeline.py run <name> [args] - Run a pipeline")
        print("  python pipeline.py create <name>     - Create custom pipeline")
        print("  python pipeline.py prompt <name>     - Generate execution prompt")


if __name__ == "__main__":
    main()

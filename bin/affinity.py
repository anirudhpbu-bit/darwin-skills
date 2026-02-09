#!/usr/bin/env python3
"""
Darwin Module-Task Affinity Matrix
Learns which module variants work best for different task types.

Usage:
  python affinity.py show           # Show current affinity matrix
  python affinity.py learn          # Update matrix from telemetry
  python affinity.py suggest <task> # Suggest modules for task type
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

DARWIN_DIR = Path.home() / ".claude" / "darwin"
TELEMETRY_DIR = DARWIN_DIR / "telemetry"
SKILLS_DIR = DARWIN_DIR / "skills"
AFFINITY_FILE = DARWIN_DIR / "affinity_matrix.json"

# Task type classification keywords
TASK_PATTERNS = {
    "planning": ["plan", "design", "architect", "implement", "feature", "roadmap", "strategy"],
    "debugging": ["fix", "bug", "error", "issue", "broken", "failing", "crash", "debug"],
    "refactoring": ["refactor", "clean", "improve", "optimize", "restructure", "modernize"],
    "documentation": ["doc", "readme", "comment", "explain", "document"],
    "testing": ["test", "spec", "coverage", "assert", "mock", "e2e"],
    "review": ["review", "audit", "check", "analyze", "assess"],
    "generation": ["create", "generate", "scaffold", "new", "add", "build"],
}

# Default affinity scores (before learning)
DEFAULT_AFFINITY = {
    "research": {
        "v1": {"planning": 0.72, "debugging": 0.45, "refactoring": 0.68, "documentation": 0.50, "testing": 0.55, "review": 0.60, "generation": 0.65},
        "v2": {"planning": 0.81, "debugging": 0.52, "refactoring": 0.71, "documentation": 0.65, "testing": 0.60, "review": 0.75, "generation": 0.70},
        "v3": {"planning": 0.65, "debugging": 0.78, "refactoring": 0.59, "documentation": 0.40, "testing": 0.70, "review": 0.55, "generation": 0.80},
    },
    "structure": {
        "v1": {"planning": 0.88, "debugging": 0.61, "refactoring": 0.74, "documentation": 0.70, "testing": 0.65, "review": 0.80, "generation": 0.72},
        "v2": {"planning": 0.71, "debugging": 0.69, "refactoring": 0.82, "documentation": 0.60, "testing": 0.75, "review": 0.68, "generation": 0.78},
        "v3": {"planning": 0.60, "debugging": 0.75, "refactoring": 0.65, "documentation": 0.45, "testing": 0.80, "review": 0.55, "generation": 0.85},
    },
    "output": {
        "v1": {"planning": 0.85, "debugging": 0.60, "refactoring": 0.70, "documentation": 0.80, "testing": 0.55, "review": 0.75, "generation": 0.65},
        "v2": {"planning": 0.70, "debugging": 0.70, "refactoring": 0.75, "documentation": 0.65, "testing": 0.70, "review": 0.65, "generation": 0.75},
        "v3": {"planning": 0.55, "debugging": 0.80, "refactoring": 0.60, "documentation": 0.40, "testing": 0.85, "review": 0.50, "generation": 0.88},
    },
    "workflow": {
        "v1": {"planning": 0.80, "debugging": 0.55, "refactoring": 0.65, "documentation": 0.70, "testing": 0.60, "review": 0.85, "generation": 0.60},
        "v2": {"planning": 0.75, "debugging": 0.70, "refactoring": 0.80, "documentation": 0.65, "testing": 0.75, "review": 0.70, "generation": 0.70},
        "v3": {"planning": 0.65, "debugging": 0.85, "refactoring": 0.70, "documentation": 0.50, "testing": 0.80, "review": 0.60, "generation": 0.85},
    },
    "input": {
        "v1": {"planning": 0.70, "debugging": 0.75, "refactoring": 0.65, "documentation": 0.80, "testing": 0.70, "review": 0.75, "generation": 0.60},
        "v2": {"planning": 0.75, "debugging": 0.70, "refactoring": 0.70, "documentation": 0.65, "testing": 0.65, "review": 0.70, "generation": 0.75},
    },
    "validation": {
        "v1": {"planning": 0.60, "debugging": 0.85, "refactoring": 0.80, "documentation": 0.50, "testing": 0.90, "review": 0.75, "generation": 0.70},
        "v2": {"planning": 0.70, "debugging": 0.80, "refactoring": 0.85, "documentation": 0.55, "testing": 0.85, "review": 0.80, "generation": 0.75},
        "v3": {"planning": 0.80, "debugging": 0.50, "refactoring": 0.60, "documentation": 0.70, "testing": 0.55, "review": 0.65, "generation": 0.80},
    }
}


def load_affinity_matrix() -> Dict:
    """Load the affinity matrix from file or return default."""
    if AFFINITY_FILE.exists():
        try:
            with open(AFFINITY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"matrix": DEFAULT_AFFINITY, "observations": 0, "last_updated": None}


def save_affinity_matrix(data: Dict):
    """Save the affinity matrix to file."""
    data["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(AFFINITY_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def classify_task(context: str) -> str:
    """Classify a task context into a task type."""
    context_lower = context.lower()

    scores = {}
    for task_type, keywords in TASK_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in context_lower)
        if score > 0:
            scores[task_type] = score

    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    return "generation"  # Default


def get_best_modules(task_type: str, matrix: Dict = None) -> Dict[str, str]:
    """Get the best module variants for a task type."""
    if matrix is None:
        data = load_affinity_matrix()
        matrix = data["matrix"]

    best = {}
    for module_type, variants in matrix.items():
        best_variant = None
        best_score = -1
        for variant, scores in variants.items():
            score = scores.get(task_type, 0.5)
            if score > best_score:
                best_score = score
                best_variant = variant
        if best_variant:
            best[module_type] = {"variant": best_variant, "score": best_score}

    return best


def update_affinity(skill: str, task_type: str, modules: Dict[str, str], fitness_delta: float):
    """Update affinity matrix based on observed fitness change."""
    data = load_affinity_matrix()
    matrix = data["matrix"]

    # Learning rate decays with observations
    observations = data.get("observations", 0)
    learning_rate = max(0.05, 0.3 / (1 + observations * 0.01))

    for module_type, variant in modules.items():
        if module_type in matrix and variant in matrix[module_type]:
            current = matrix[module_type][variant].get(task_type, 0.5)
            # Adjust score based on fitness delta
            adjustment = fitness_delta * learning_rate
            new_score = max(0.1, min(0.99, current + adjustment))
            matrix[module_type][variant][task_type] = round(new_score, 3)

    data["observations"] = observations + 1
    save_affinity_matrix(data)


def print_matrix():
    """Print the affinity matrix."""
    data = load_affinity_matrix()
    matrix = data["matrix"]

    print("═══════════════════════════════════════════════════")
    print("MODULE-TASK AFFINITY MATRIX")
    print("═══════════════════════════════════════════════════")
    print(f"Observations: {data.get('observations', 0)}")
    print(f"Last updated: {data.get('last_updated', 'Never')}")
    print()

    task_types = list(TASK_PATTERNS.keys())

    for module_type, variants in matrix.items():
        print(f"{module_type.upper()}")
        print("───────────────────────────────────────────────────")

        # Header
        header = f"{'Variant':<10}"
        for tt in task_types:
            header += f"{tt[:8]:>10}"
        print(header)

        # Rows
        for variant, scores in variants.items():
            row = f"{variant:<10}"
            for tt in task_types:
                score = scores.get(tt, 0.5)
                # Color code (using ASCII)
                if score >= 0.8:
                    marker = "██"
                elif score >= 0.6:
                    marker = "▓▓"
                elif score >= 0.4:
                    marker = "░░"
                else:
                    marker = "  "
                row += f"{marker}{score:.2f}".rjust(10)
            print(row)
        print()

    print("═══════════════════════════════════════════════════")
    print("LEGEND: ██ ≥0.8 (excellent)  ▓▓ ≥0.6 (good)  ░░ ≥0.4 (fair)")
    print("═══════════════════════════════════════════════════")


def print_suggestion(task_context: str):
    """Print module suggestions for a task."""
    task_type = classify_task(task_context)
    best = get_best_modules(task_type)

    print("═══════════════════════════════════════════════════")
    print(f"MODULE SUGGESTIONS FOR: {task_type.upper()}")
    print("═══════════════════════════════════════════════════")
    print(f"Task context: \"{task_context[:50]}...\"")
    print()

    print("RECOMMENDED MODULES")
    print("───────────────────────────────────────────────────")
    for module, info in sorted(best.items(), key=lambda x: x[1]["score"], reverse=True):
        score = info["score"]
        variant = info["variant"]
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"  {module:12} → {variant:4}  {bar}  {score:.2f}")

    print()
    print("═══════════════════════════════════════════════════")


def learn_from_telemetry():
    """Update affinity matrix from telemetry data."""
    print("Learning from telemetry...")

    # Load telemetry sessions
    sessions_dir = TELEMETRY_DIR / "sessions"
    if not sessions_dir.exists():
        print("No telemetry sessions found.")
        return

    updates = 0
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, 'r') as f:
                session = json.load(f)

            for event in session.get("events", []):
                skill = event.get("skill")
                context = event.get("context", "")
                completed = event.get("completed", False)

                if skill and context:
                    # Classify task
                    task_type = classify_task(context)

                    # Get skill modules
                    skill_file = SKILLS_DIR / f"{skill}.yaml"
                    if skill_file.exists():
                        with open(skill_file, 'r') as f:
                            skill_def = yaml.safe_load(f)
                        modules = skill_def.get("modules", {})

                        # Infer fitness delta from completion
                        fitness_delta = 0.05 if completed else -0.02

                        # Update affinity
                        update_affinity(skill, task_type, modules, fitness_delta)
                        updates += 1
        except Exception as e:
            continue

    print(f"Applied {updates} observations to affinity matrix.")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "show":
        print_matrix()
    elif args[0] == "learn":
        learn_from_telemetry()
    elif args[0] == "suggest" and len(args) > 1:
        task_context = " ".join(args[1:])
        print_suggestion(task_context)
    elif args[0] == "best":
        task_type = args[1] if len(args) > 1 else "planning"
        best = get_best_modules(task_type)
        print(json.dumps(best, indent=2))
    else:
        print("Usage: affinity.py [show|learn|suggest <task>|best <type>]")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Darwin Skills Evaluation Runner

Semi-automated evaluation suite for testing skill quality.
Since skills run inside Claude Code, this tool:
1. Presents prompts for manual execution
2. Captures criterion ratings from evaluator
3. Calculates scores and saves results
4. Compares versions over time

Usage:
    python run-eval.py                    # Interactive mode - run all skills
    python run-eval.py plan               # Run evals for specific skill
    python run-eval.py plan --prompt 001  # Run specific prompt
    python run-eval.py --report           # Show results report
    python run-eval.py --compare v1 v2    # Compare two versions
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

EVALS_DIR = Path(__file__).parent
PROMPTS_DIR = EVALS_DIR / "prompts"
RESULTS_DIR = EVALS_DIR / "results"

# Ensure results directory exists
RESULTS_DIR.mkdir(exist_ok=True)


def load_prompts(skill: str = None) -> dict:
    """Load eval prompts from YAML files."""
    prompts = {}

    if skill:
        files = [PROMPTS_DIR / f"{skill}.yaml"]
    else:
        files = PROMPTS_DIR.glob("*.yaml")

    for file in files:
        if not file.exists():
            print(f"Warning: {file} not found")
            continue
        with open(file) as f:
            data = yaml.safe_load(f)
            skill_name = data.get("skill", file.stem)
            prompts[skill_name] = data

    return prompts


def display_prompt(skill: str, prompt: dict) -> None:
    """Display a prompt for manual execution."""
    print("\n" + "=" * 60)
    print(f"SKILL: /{skill}")
    print(f"TEST:  {prompt['name']} ({prompt['id']})")
    print("=" * 60)

    if "setup" in prompt:
        print(f"\n📋 SETUP: {prompt['setup']}")

    print(f"\n💬 PROMPT TO RUN:")
    print(f"   {prompt['prompt']}")

    print(f"\n📊 CRITERIA TO EVALUATE:")
    for i, criterion in enumerate(prompt["criteria"], 1):
        weight_pct = int(criterion["weight"] * 100)
        print(f"   {i}. [{weight_pct:2d}%] {criterion['description']}")


def rate_criteria(prompt: dict) -> dict:
    """Get ratings for each criterion from evaluator."""
    ratings = {}

    print("\n" + "-" * 60)
    print("RATE EACH CRITERION (0-10, or 's' to skip, 'q' to quit):")
    print("-" * 60)

    for criterion in prompt["criteria"]:
        while True:
            rating = input(f"  {criterion['id']}: ").strip().lower()

            if rating == 'q':
                return None
            if rating == 's':
                ratings[criterion["id"]] = None
                break

            try:
                score = float(rating)
                if 0 <= score <= 10:
                    ratings[criterion["id"]] = score
                    break
                else:
                    print("    Please enter 0-10")
            except ValueError:
                print("    Invalid input. Enter 0-10, 's' to skip, or 'q' to quit")

    return ratings


def calculate_score(prompt: dict, ratings: dict) -> float:
    """Calculate weighted score from ratings."""
    total_weight = 0
    weighted_sum = 0

    for criterion in prompt["criteria"]:
        cid = criterion["id"]
        weight = criterion["weight"]

        if cid in ratings and ratings[cid] is not None:
            weighted_sum += ratings[cid] * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalize to 0-1 scale
    return (weighted_sum / total_weight) / 10


def save_result(skill: str, prompt_id: str, ratings: dict, score: float, version: str = None) -> None:
    """Save evaluation result."""
    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "skill": skill,
        "prompt_id": prompt_id,
        "version": version or "unknown",
        "ratings": ratings,
        "score": round(score, 3)
    }

    results_file = RESULTS_DIR / f"{skill}.jsonl"
    with open(results_file, "a") as f:
        f.write(json.dumps(result) + "\n")

    print(f"\n✅ Result saved: {skill} / {prompt_id} = {score:.2f}")


def run_interactive(skill: str = None, prompt_id: str = None) -> None:
    """Run interactive evaluation session."""
    prompts = load_prompts(skill)

    if not prompts:
        print("No prompts found!")
        return

    # Get skill version
    version = input("\nEnter skill version being tested (e.g., v1.1.0): ").strip()
    if not version:
        version = "unknown"

    print("\n" + "=" * 60)
    print("DARWIN SKILLS EVALUATION")
    print("=" * 60)
    print(f"Version: {version}")
    print(f"Skills:  {', '.join(prompts.keys())}")
    print("\nInstructions:")
    print("1. Run each prompt in Claude Code")
    print("2. Observe the output")
    print("3. Rate each criterion 0-10")
    print("=" * 60)

    input("\nPress Enter to begin...")

    for skill_name, skill_data in prompts.items():
        for prompt in skill_data["prompts"]:
            # Filter by prompt_id if specified
            if prompt_id and not prompt["id"].endswith(prompt_id):
                continue

            display_prompt(skill_name, prompt)

            input("\n[Press Enter after running the prompt in Claude Code]")

            ratings = rate_criteria(prompt)

            if ratings is None:
                print("\nEvaluation cancelled.")
                return

            score = calculate_score(prompt, ratings)
            save_result(skill_name, prompt["id"], ratings, score, version)

            cont = input("\nContinue to next prompt? (y/n): ").strip().lower()
            if cont == 'n':
                print("\nEvaluation paused. Run again to continue.")
                return


def show_report() -> None:
    """Show results report."""
    print("\n" + "=" * 60)
    print("DARWIN SKILLS EVALUATION REPORT")
    print("=" * 60)

    for results_file in RESULTS_DIR.glob("*.jsonl"):
        skill = results_file.stem

        results_by_version = {}
        with open(results_file) as f:
            for line in f:
                result = json.loads(line)
                version = result.get("version", "unknown")
                if version not in results_by_version:
                    results_by_version[version] = []
                results_by_version[version].append(result)

        print(f"\n/{skill}")
        print("-" * 40)

        for version, results in sorted(results_by_version.items()):
            scores = [r["score"] for r in results]
            avg = sum(scores) / len(scores) if scores else 0

            bar = "█" * int(avg * 10) + "░" * (10 - int(avg * 10))
            print(f"  {version:12} {bar} {avg:.2f} ({len(scores)} evals)")


def compare_versions(v1: str, v2: str) -> None:
    """Compare two versions across all skills."""
    print("\n" + "=" * 60)
    print(f"COMPARING {v1} vs {v2}")
    print("=" * 60)

    for results_file in RESULTS_DIR.glob("*.jsonl"):
        skill = results_file.stem

        v1_scores = []
        v2_scores = []

        with open(results_file) as f:
            for line in f:
                result = json.loads(line)
                version = result.get("version", "unknown")
                if version == v1:
                    v1_scores.append(result["score"])
                elif version == v2:
                    v2_scores.append(result["score"])

        if not v1_scores and not v2_scores:
            continue

        v1_avg = sum(v1_scores) / len(v1_scores) if v1_scores else 0
        v2_avg = sum(v2_scores) / len(v2_scores) if v2_scores else 0
        diff = v2_avg - v1_avg

        indicator = "↑" if diff > 0.05 else "↓" if diff < -0.05 else "→"

        print(f"\n/{skill}")
        print(f"  {v1}: {v1_avg:.2f} ({len(v1_scores)} evals)")
        print(f"  {v2}: {v2_avg:.2f} ({len(v2_scores)} evals)")
        print(f"  Change: {diff:+.2f} {indicator}")


def main():
    parser = argparse.ArgumentParser(description="Darwin Skills Evaluation Runner")
    parser.add_argument("skill", nargs="?", help="Skill to evaluate (e.g., plan, commit)")
    parser.add_argument("--prompt", help="Specific prompt ID to run (e.g., 001)")
    parser.add_argument("--report", action="store_true", help="Show results report")
    parser.add_argument("--compare", nargs=2, metavar=("V1", "V2"), help="Compare two versions")

    args = parser.parse_args()

    if args.report:
        show_report()
    elif args.compare:
        compare_versions(args.compare[0], args.compare[1])
    else:
        run_interactive(args.skill, args.prompt)


if __name__ == "__main__":
    main()

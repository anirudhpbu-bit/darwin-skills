#!/usr/bin/env python3
"""
Darwin Recommendation Engine
Detects skill gaps and recommends skills based on user activity patterns.

Usage:
  python recommend.py              # Show recommendations
  python recommend.py --gaps       # Show only detected gaps
  python recommend.py --external   # Include skills.sh recommendations
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

DARWIN_DIR = Path.home() / ".claude" / "darwin"
TELEMETRY_DIR = DARWIN_DIR / "telemetry"
SKILLS_DIR = DARWIN_DIR / "skills"
CACHE_DIR = DARWIN_DIR / "cache"

# Skill gap detection patterns
PATTERNS = {
    "commit": {
        "detect": "git_commits_without_skill",
        "threshold": 3,
        "message": "You made {count} manual git commits",
        "benefit": "Auto-generates conventional commit messages"
    },
    "build-fix": {
        "detect": "build_failures",
        "threshold": 2,
        "message": "{count} build failures detected",
        "benefit": "Loops until build passes, fixing errors automatically"
    },
    "plan": {
        "detect": "large_features_without_plan",
        "threshold": 1,
        "message": "Large feature work detected without planning",
        "benefit": "Creates structured implementation plans"
    },
    "techdebt": {
        "detect": "no_recent_audit",
        "threshold": 14,  # days
        "message": "No code audit in {count} days",
        "benefit": "Finds code smells, duplicates, and TODOs"
    },
    "rams": {
        "detect": "ui_changes_without_a11y",
        "threshold": 5,
        "message": "{count} UI component changes without accessibility review",
        "benefit": "Reviews accessibility and visual design"
    },
    "scaffold": {
        "detect": "manual_boilerplate",
        "threshold": 2,
        "message": "Created {count} files manually that match project patterns",
        "benefit": "Generates boilerplate matching your project conventions"
    }
}

# External skills recommendations based on stack detection
STACK_SKILLS = {
    "react": [
        {"name": "anthropics/vercel-react-best-practices", "installs": "108K", "reason": "React best practices"},
        {"name": "anthropics/react-testing-patterns", "installs": "45K", "reason": "React testing patterns"}
    ],
    "nextjs": [
        {"name": "vercel/nextjs-patterns", "installs": "67K", "reason": "Next.js App Router patterns"},
    ],
    "expo": [
        {"name": "expo/expo-best-practices", "installs": "23K", "reason": "Expo mobile development"},
    ],
    "typescript": [
        {"name": "anthropics/typescript-strict-mode", "installs": "52K", "reason": "TypeScript strict patterns"},
    ],
    "tailwind": [
        {"name": "tailwindlabs/tailwind-patterns", "installs": "38K", "reason": "Tailwind CSS best practices"},
    ],
    "zustand": [
        {"name": "pmndrs/zustand-patterns", "installs": "12K", "reason": "Zustand state management"},
    ],
    "three": [
        {"name": "pmndrs/threejs-patterns", "installs": "18K", "reason": "Three.js 3D graphics"},
    ]
}


def load_json(path: Path) -> dict:
    """Load JSON file safely."""
    if not path.exists():
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return {}


def get_git_stats(days: int = 7) -> Dict:
    """Get git commit statistics for the last N days."""
    stats = {"commits": 0, "commit_messages": [], "files_changed": set()}

    try:
        # Get recent commits
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["git", "log", f"--since={since_date}", "--oneline"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            commits = result.stdout.strip().split('\n')
            stats["commits"] = len([c for c in commits if c])
            stats["commit_messages"] = commits[:20]  # Last 20

            # Check for conventional commits
            conventional_pattern = r'^[a-f0-9]+ (feat|fix|refactor|docs|chore|test|style|perf)(\(.+\))?:'
            stats["conventional_commits"] = sum(
                1 for c in commits if re.match(conventional_pattern, c)
            )
    except:
        pass

    return stats


def get_build_stats() -> Dict:
    """Detect build failures from recent activity."""
    stats = {"failures": 0, "last_failure": None}

    # Check for common build error patterns in recent terminal history
    # This is a heuristic - in production would use proper telemetry
    try:
        # Check for TypeScript errors
        result = subprocess.run(
            ["bash", "-c", "find . -name '*.log' -mtime -1 2>/dev/null | head -5 | xargs grep -l 'error TS' 2>/dev/null | wc -l"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            stats["failures"] += int(result.stdout.strip() or 0)
    except:
        pass

    return stats


def get_skill_usage() -> Dict[str, int]:
    """Get skill usage counts from telemetry."""
    usage = {}

    # Read aggregates
    aggregates_file = TELEMETRY_DIR / "aggregates.json"
    aggregates = load_json(aggregates_file)

    # Handle both list and dict formats for skills
    skills_data = aggregates.get("skills", [])
    if isinstance(skills_data, list):
        for item in skills_data:
            skill = item.get("skill")
            count = item.get("count", 0)
            if skill:
                usage[skill] = count
    elif isinstance(skills_data, dict):
        for skill, data in skills_data.items():
            usage[skill] = data.get("invocations", 0) if isinstance(data, dict) else data

    # Also check session files
    sessions_dir = TELEMETRY_DIR / "sessions"
    if sessions_dir.exists():
        for session_file in sessions_dir.glob("*.json"):
            session = load_json(session_file)
            for event in session.get("events", []):
                skill = event.get("skill")
                if skill:
                    usage[skill] = usage.get(skill, 0) + 1

    return usage


def detect_stack() -> List[str]:
    """Detect the user's tech stack from project files."""
    stack = []

    # Check package.json
    pkg_paths = [
        Path.cwd() / "package.json",
        Path.home() / "one-app" / "package.json",
        Path.home() / "eido-editions" / "package.json"
    ]

    for pkg_path in pkg_paths:
        if pkg_path.exists():
            pkg = load_json(pkg_path)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            if "react" in deps or "react-native" in deps:
                stack.append("react")
            if "next" in deps:
                stack.append("nextjs")
            if "expo" in deps:
                stack.append("expo")
            if "typescript" in deps:
                stack.append("typescript")
            if "tailwindcss" in deps or "tailwind" in deps:
                stack.append("tailwind")
            if "zustand" in deps:
                stack.append("zustand")
            if "three" in deps:
                stack.append("three")

    return list(set(stack))


def get_installed_skills() -> List[str]:
    """Get list of installed Darwin skills."""
    skills = []
    if SKILLS_DIR.exists():
        for skill_file in SKILLS_DIR.glob("*.yaml"):
            skills.append(skill_file.stem)
    return skills


def detect_gaps() -> List[Dict]:
    """Detect skill gaps based on user activity patterns."""
    gaps = []

    git_stats = get_git_stats()
    build_stats = get_build_stats()
    skill_usage = get_skill_usage()
    installed = get_installed_skills()

    # Check each pattern
    for skill_name, pattern in PATTERNS.items():
        detection = pattern["detect"]
        threshold = pattern["threshold"]

        should_recommend = False
        count = 0

        if detection == "git_commits_without_skill":
            # Manual commits without using /commit
            total_commits = git_stats.get("commits", 0)
            conventional = git_stats.get("conventional_commits", 0)
            commit_skill_usage = skill_usage.get("commit", 0)

            # If many commits but few conventional and low skill usage
            if total_commits >= threshold and commit_skill_usage < total_commits * 0.3:
                should_recommend = True
                count = total_commits - commit_skill_usage

        elif detection == "build_failures":
            failures = build_stats.get("failures", 0)
            if failures >= threshold and skill_usage.get("build-fix", 0) == 0:
                should_recommend = True
                count = failures

        elif detection == "no_recent_audit":
            # Check last techdebt run
            last_run = skill_usage.get("techdebt", 0)
            if last_run == 0:  # Never run
                should_recommend = True
                count = 30  # Assume 30 days

        elif detection == "ui_changes_without_a11y":
            # Heuristic: check for component file changes
            rams_usage = skill_usage.get("rams", 0)
            if rams_usage == 0 and skill_name in installed:
                should_recommend = True
                count = 5  # Estimate

        if should_recommend:
            gaps.append({
                "type": "underutilized" if skill_name in installed else "missing",
                "skill": skill_name,
                "installed": skill_name in installed,
                "message": pattern["message"].format(count=count),
                "benefit": pattern["benefit"],
                "priority": "high" if count >= threshold * 2 else "medium"
            })

    return gaps


def get_external_recommendations(stack: List[str], installed: List[str]) -> List[Dict]:
    """Get external skill recommendations from skills.sh based on stack."""
    recommendations = []

    for tech in stack:
        if tech in STACK_SKILLS:
            for skill in STACK_SKILLS[tech]:
                # Check if not already have similar skill
                skill_name = skill["name"].split("/")[-1]
                if skill_name not in installed:
                    recommendations.append({
                        "type": "external",
                        "name": skill["name"],
                        "installs": skill["installs"],
                        "reason": skill["reason"],
                        "stack_match": tech,
                        "install_cmd": f"npx skills add {skill['name']}"
                    })

    return recommendations


def get_usage_tips(skill_usage: Dict[str, int], installed: List[str]) -> List[Dict]:
    """Generate usage tips for installed but unused skills."""
    tips = []

    for skill in installed:
        usage = skill_usage.get(skill, 0)
        if usage == 0:
            tips.append({
                "type": "tip",
                "skill": skill,
                "message": f"/{skill} is installed but never used",
                "suggestion": f"Try running /{skill} on your next relevant task"
            })
        elif usage < 3:
            tips.append({
                "type": "tip",
                "skill": skill,
                "message": f"/{skill} used only {usage} time(s)",
                "suggestion": "Consider using it more consistently for better results"
            })

    return tips


def print_recommendations(include_external: bool = True):
    """Print all recommendations."""
    print("═══════════════════════════════════════════════════")
    print("DARWIN RECOMMENDATIONS")
    print("═══════════════════════════════════════════════════")
    print()

    # Gather data
    gaps = detect_gaps()
    stack = detect_stack()
    installed = get_installed_skills()
    skill_usage = get_skill_usage()
    tips = get_usage_tips(skill_usage, installed)

    # Print detected stack
    if stack:
        print(f"DETECTED STACK: {', '.join(stack)}")
        print()

    # Print skill gaps
    if gaps:
        print("SKILL GAPS")
        print("───────────────────────────────────────────────────")
        for gap in gaps:
            icon = "💡" if gap["installed"] else "📦"
            priority_marker = "❗" if gap["priority"] == "high" else ""
            print(f" {icon} {gap['message']} {priority_marker}")
            if gap["installed"]:
                print(f"    → Use /{gap['skill']} - {gap['benefit']}")
            else:
                print(f"    → Install /{gap['skill']} - {gap['benefit']}")
            print()
    else:
        print("✓ No skill gaps detected")
        print()

    # Print usage tips
    if tips:
        print("USAGE TIPS")
        print("───────────────────────────────────────────────────")
        for tip in tips[:5]:  # Top 5
            print(f" 💡 {tip['message']}")
            print(f"    → {tip['suggestion']}")
            print()

    # Print external recommendations
    if include_external:
        external = get_external_recommendations(stack, installed)
        if external:
            print("RECOMMENDED FROM SKILLS.SH")
            print("───────────────────────────────────────────────────")
            for rec in external[:5]:  # Top 5
                print(f" 📥 {rec['name']} ({rec['installs']} installs)")
                print(f"    Reason: {rec['reason']}")
                print(f"    Stack match: {rec['stack_match']}")
                print(f"    Install: {rec['install_cmd']}")
                print()

    # Print skill fitness summary
    print("SKILL HEALTH SUMMARY")
    print("───────────────────────────────────────────────────")
    total_usage = sum(skill_usage.values())
    active_skills = len([s for s, u in skill_usage.items() if u > 0])
    print(f" Total invocations: {total_usage}")
    print(f" Active skills: {active_skills}/{len(installed)}")
    print(f" Most used: {max(skill_usage.items(), key=lambda x: x[1])[0] if skill_usage else 'N/A'}")
    print()

    print("═══════════════════════════════════════════════════")
    print("Run '/darwin status' for detailed fitness scores")
    print("Run '/darwin sync' to fetch trending skills")
    print("═══════════════════════════════════════════════════")


def main():
    args = sys.argv[1:]

    if "--gaps" in args:
        gaps = detect_gaps()
        print(json.dumps(gaps, indent=2))
    elif "--external" in args:
        stack = detect_stack()
        installed = get_installed_skills()
        external = get_external_recommendations(stack, installed)
        print(json.dumps(external, indent=2))
    elif "--json" in args:
        gaps = detect_gaps()
        stack = detect_stack()
        installed = get_installed_skills()
        external = get_external_recommendations(stack, installed)
        print(json.dumps({
            "gaps": gaps,
            "stack": stack,
            "external": external
        }, indent=2))
    else:
        print_recommendations(include_external="--no-external" not in args)


if __name__ == "__main__":
    main()

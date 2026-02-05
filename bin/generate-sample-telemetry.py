#!/usr/bin/env python3
"""
Generate sample telemetry data for Darwin Skills testing.
Creates realistic usage patterns with variation across skills.
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
DARWIN_DIR = Path.home() / ".claude" / "darwin"
TELEMETRY_DIR = DARWIN_DIR / "telemetry"

# Skill configurations with usage weights and performance characteristics
SKILLS = {
    "plan": {
        "weight": 25,  # High usage - top performer
        "tool_range": (3, 8),  # Efficient
        "completion_rate": 0.95,
        "modules": {"input": "v1", "research": "v2", "structure": "v1", "output": "v1", "workflow": "v1", "validation": "v3"}
    },
    "commit": {
        "weight": 30,  # Highest usage - top performer
        "tool_range": (2, 5),  # Very efficient
        "completion_rate": 0.98,
        "modules": {"input": "v3", "research": "v3", "structure": "v1", "output": "v2", "workflow": "v2", "validation": "v2"}
    },
    "techdebt": {
        "weight": 12,  # Medium usage
        "tool_range": (5, 12),  # Medium efficiency
        "completion_rate": 0.85,
        "modules": {"input": "v2", "research": "v1", "structure": "v1", "output": "v1", "workflow": "v1", "validation": "v3"}
    },
    "scaffold": {
        "weight": 15,  # Medium-high usage
        "tool_range": (4, 10),  # Medium efficiency
        "completion_rate": 0.90,
        "modules": {"input": "v1", "research": "v3", "structure": "v2", "output": "v3", "workflow": "v3", "validation": "v3"}
    },
    "build-fix": {
        "weight": 10,  # Medium usage
        "tool_range": (8, 20),  # Less efficient (loops)
        "completion_rate": 0.80,
        "modules": {"input": "v2", "research": "v3", "structure": "v1", "output": "v1", "workflow": "v2", "validation": "v1"}
    },
    "design-audit": {
        "weight": 4,  # Low usage - underperformer
        "tool_range": (6, 15),  # Medium efficiency
        "completion_rate": 0.70,
        "modules": {"input": "v1", "research": "v2", "structure": "v1", "output": "v2", "workflow": "v1", "validation": "v3"}
    },
    "review-plan": {
        "weight": 3,  # Low usage - underperformer
        "tool_range": (4, 10),
        "completion_rate": 0.75,
        "modules": {"input": "v1", "research": "v2", "structure": "v1", "output": "v2", "workflow": "v1", "validation": "v2"}
    },
    "darwin": {
        "weight": 1,  # Very low (meta skill)
        "tool_range": (2, 6),
        "completion_rate": 0.90,
        "modules": {"input": "v2", "research": "v3", "structure": "v1", "output": "v1", "workflow": "v3", "validation": "v3"}
    }
}

# Example prompts for each skill
PROMPTS = {
    "plan": [
        "/plan implement user authentication",
        "/plan add dark mode toggle",
        "/plan design the notification system",
        "/plan how to structure the API",
        "/plan add search functionality"
    ],
    "commit": [
        "/commit",
        "/commit save my changes",
        "/commit create a commit",
        "/commit what should the message be",
        "/commit push this"
    ],
    "techdebt": [
        "/techdebt",
        "/techdebt find code smells",
        "/techdebt what needs fixing",
        "/techdebt audit this file",
        "/techdebt check for TODOs"
    ],
    "scaffold": [
        "/scaffold new component Button",
        "/scaffold create UserProfile screen",
        "/scaffold generate useAuth hook",
        "/scaffold add Settings page",
        "/scaffold create API service"
    ],
    "build-fix": [
        "/build-fix",
        "/build-fix fix the errors",
        "/build-fix make build pass",
        "/build-fix fix type errors",
        "/build-fix resolve compilation"
    ],
    "design-audit": [
        "/design-audit check accessibility",
        "/design-audit review this component",
        "/design-audit audit WCAG compliance",
        "/design-audit is this accessible"
    ],
    "review-plan": [
        "/review-plan",
        "/review-plan critique this approach",
        "/review-plan is this solid",
        "/review-plan review my plan"
    ],
    "darwin": [
        "/darwin status",
        "/darwin evolve",
        "/darwin suggest"
    ]
}


def weighted_choice(skills: dict) -> str:
    """Select a skill based on weights."""
    total = sum(s["weight"] for s in skills.values())
    r = random.uniform(0, total)
    cumulative = 0
    for name, config in skills.items():
        cumulative += config["weight"]
        if r <= cumulative:
            return name
    return list(skills.keys())[0]


def generate_session_id() -> str:
    """Generate a realistic session ID."""
    return str(uuid.uuid4())[:8]


def generate_telemetry(days: int = 14, invocations_per_day: tuple = (8, 20)):
    """Generate telemetry data for the specified number of days."""

    # Ensure directories exist
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)

    skills_log = []
    sessions_log = []

    now = datetime.utcnow()

    # Generate data for each day
    for day_offset in range(days, 0, -1):
        day = now - timedelta(days=day_offset)

        # Random number of invocations per day (more recent = slightly more usage)
        recency_boost = 1 + (0.05 * (days - day_offset))  # Slight trend increase
        num_invocations = int(random.randint(*invocations_per_day) * recency_boost)

        for _ in range(num_invocations):
            # Pick a skill
            skill_name = weighted_choice(SKILLS)
            skill_config = SKILLS[skill_name]

            # Generate timestamps within the day
            hour = random.randint(9, 22)  # Working hours
            minute = random.randint(0, 59)
            second = random.randint(0, 59)

            start_time = day.replace(hour=hour, minute=minute, second=second)

            # Duration based on tool count
            tool_count = random.randint(*skill_config["tool_range"])
            duration_minutes = tool_count * random.uniform(0.5, 2)  # Rough estimate
            end_time = start_time + timedelta(minutes=duration_minutes)

            session_id = generate_session_id()
            prompt = random.choice(PROMPTS[skill_name])

            # Skill start entry
            skills_log.append({
                "timestamp": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "session_id": session_id,
                "event": "skill_start",
                "skill": skill_name,
                "prompt": prompt,
                "modules": skill_config["modules"]
            })

            # Session completion (based on completion rate)
            completed = random.random() < skill_config["completion_rate"]

            sessions_log.append({
                "timestamp": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "session_id": session_id,
                "event": "skill_complete",
                "skill": skill_name,
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "tool_count": tool_count,
                "modules": skill_config["modules"],
                "completed": completed
            })

    # Sort by timestamp
    skills_log.sort(key=lambda x: x["timestamp"])
    sessions_log.sort(key=lambda x: x["timestamp"])

    # Write files
    skills_file = TELEMETRY_DIR / "skills.jsonl"
    sessions_file = TELEMETRY_DIR / "session_summaries.jsonl"

    with open(skills_file, "w") as f:
        for entry in skills_log:
            f.write(json.dumps(entry) + "\n")

    with open(sessions_file, "w") as f:
        for entry in sessions_log:
            f.write(json.dumps(entry) + "\n")

    # Summary
    print(f"Generated telemetry data for {days} days")
    print(f"  Skills log: {len(skills_log)} entries -> {skills_file}")
    print(f"  Sessions log: {len(sessions_log)} entries -> {sessions_file}")
    print()
    print("Skill distribution:")

    skill_counts = {}
    for entry in skills_log:
        skill = entry["skill"]
        skill_counts[skill] = skill_counts.get(skill, 0) + 1

    for skill, count in sorted(skill_counts.items(), key=lambda x: -x[1]):
        pct = count / len(skills_log) * 100
        bar = "█" * int(pct / 2)
        print(f"  {skill:12} {count:3} ({pct:5.1f}%) {bar}")


if __name__ == "__main__":
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    generate_telemetry(days=days)

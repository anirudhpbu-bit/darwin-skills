#!/usr/bin/env python3
"""
Create Darwin tracking wrappers for external skills.
"""

import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

DARWIN_DIR = Path.home() / ".claude" / "darwin"
SKILLS_DIR = DARWIN_DIR / "skills"
EXTERNAL_SKILLS_DIR = DARWIN_DIR / ".agents" / "skills"

def create_wrapper(skill_name: str, source: str = "skills.sh"):
    """Create a Darwin YAML wrapper for an external skill."""

    wrapper = {
        "name": skill_name,
        "version": "1.0.0",
        "description": f"External skill from {source}: {skill_name}",
        "source": source,
        "external": True,
        "modules": {
            "input": "v2",
            "research": "v3",
            "structure": "v1",
            "output": "v1",
            "workflow": "v3",
            "validation": "v3"
        },
        "installed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fitness_history": []
    }

    wrapper_path = SKILLS_DIR / f"{skill_name}.yaml"

    # Don't overwrite existing Darwin skills
    if wrapper_path.exists():
        with open(wrapper_path, 'r') as f:
            existing = yaml.safe_load(f)
        if not existing.get("external"):
            print(f"  Skipping {skill_name} - existing Darwin skill")
            return False

    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    with open(wrapper_path, 'w') as f:
        yaml.dump(wrapper, f, default_flow_style=False, sort_keys=False)

    print(f"  ✓ Created wrapper for {skill_name}")
    return True

def main():
    if len(sys.argv) > 1:
        # Create wrapper for specific skill
        for skill_name in sys.argv[1:]:
            create_wrapper(skill_name)
    else:
        # Create wrappers for all external skills
        if not EXTERNAL_SKILLS_DIR.exists():
            print("No external skills found.")
            return

        print("Creating Darwin tracking wrappers...")
        created = 0
        for skill_dir in EXTERNAL_SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                if create_wrapper(skill_dir.name):
                    created += 1

        print(f"\nCreated {created} tracking wrapper(s)")

if __name__ == "__main__":
    main()

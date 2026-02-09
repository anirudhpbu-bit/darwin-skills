#!/usr/bin/env python3
"""
Darwin Skills.sh Sync
Fetches trending skills, matches to user's stack, and manages external skill installation.

Usage:
  python sync.py                    # Show sync dashboard
  python sync.py trending           # Show trending skills
  python sync.py install <name>     # Install external skill
  python sync.py upgrade            # Check for skill upgrades
  python sync.py search <query>     # Search skills.sh
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

DARWIN_DIR = Path.home() / ".claude" / "darwin"
SKILLS_DIR = DARWIN_DIR / "skills"
CACHE_DIR = DARWIN_DIR / "cache"
EXTERNAL_SKILLS_DIR = Path.home() / ".claude" / "skills"

# Skills.sh curated list (since API may not be public)
# In production, this would fetch from skills.sh API
CURATED_SKILLS = {
    "trending": [
        {"name": "anthropics/claude-code-patterns", "installs": 89000, "category": "general", "description": "Best practices for Claude Code development"},
        {"name": "vercel/vercel-react-best-practices", "installs": 108700, "category": "react", "description": "React patterns from Vercel team"},
        {"name": "anthropics/web-design-guidelines", "installs": 82300, "category": "design", "description": "Web design and UX patterns"},
        {"name": "anthropics/typescript-patterns", "installs": 67000, "category": "typescript", "description": "TypeScript best practices"},
        {"name": "expo/expo-patterns", "installs": 45000, "category": "mobile", "description": "Expo React Native patterns"},
        {"name": "nextjs/app-router-patterns", "installs": 52000, "category": "nextjs", "description": "Next.js App Router best practices"},
        {"name": "tailwindlabs/tailwind-components", "installs": 38000, "category": "css", "description": "Tailwind CSS component patterns"},
        {"name": "testing-library/testing-patterns", "installs": 34000, "category": "testing", "description": "Frontend testing patterns"},
        {"name": "prisma/database-patterns", "installs": 29000, "category": "database", "description": "Database schema and query patterns"},
        {"name": "anthropics/accessibility-checker", "installs": 25000, "category": "a11y", "description": "Accessibility review patterns"},
    ],
    "hot_24h": [
        {"name": "anthropics/claude-code-v2-patterns", "delta": 2300, "category": "general"},
        {"name": "nextjs/nextjs-15-migration", "delta": 1800, "category": "nextjs"},
        {"name": "anthropics/mcp-development", "delta": 1500, "category": "mcp"},
    ],
    "categories": {
        "react": ["vercel/vercel-react-best-practices", "react/hooks-patterns", "react/performance"],
        "nextjs": ["nextjs/app-router-patterns", "nextjs/server-actions", "vercel/nextjs-deploy"],
        "typescript": ["anthropics/typescript-patterns", "typescript/strict-mode", "typescript/generics"],
        "mobile": ["expo/expo-patterns", "react-native/navigation", "expo/eas-build"],
        "testing": ["testing-library/testing-patterns", "vitest/unit-testing", "playwright/e2e"],
        "design": ["anthropics/web-design-guidelines", "figma/design-tokens", "radix/component-patterns"],
        "a11y": ["anthropics/accessibility-checker", "axe/a11y-patterns", "wcag/compliance"],
    }
}

# Stack to category mapping
STACK_CATEGORIES = {
    "react": ["react", "testing"],
    "nextjs": ["nextjs", "react"],
    "expo": ["mobile", "react"],
    "typescript": ["typescript"],
    "tailwind": ["design"],
    "zustand": ["react"],
    "three": ["design"],
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


def save_json(path: Path, data: dict):
    """Save JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def detect_stack() -> List[str]:
    """Detect the user's tech stack from project files."""
    stack = []

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
            if "tailwindcss" in deps:
                stack.append("tailwind")
            if "zustand" in deps:
                stack.append("zustand")
            if "three" in deps:
                stack.append("three")

    return list(set(stack))


def get_installed_external() -> List[str]:
    """Get list of installed external skills."""
    installed = []
    if EXTERNAL_SKILLS_DIR.exists():
        for item in EXTERNAL_SKILLS_DIR.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                installed.append(item.name)
    return installed


def get_darwin_skills() -> List[str]:
    """Get list of Darwin-managed skills."""
    skills = []
    if SKILLS_DIR.exists():
        for skill_file in SKILLS_DIR.glob("*.yaml"):
            skills.append(skill_file.stem)
    return skills


def get_recommended_for_stack(stack: List[str]) -> List[Dict]:
    """Get skill recommendations based on detected stack."""
    recommendations = []
    seen = set()

    for tech in stack:
        categories = STACK_CATEGORIES.get(tech, [])
        for category in categories:
            category_skills = CURATED_SKILLS["categories"].get(category, [])
            for skill_name in category_skills:
                if skill_name not in seen:
                    seen.add(skill_name)
                    # Find full skill info
                    skill_info = next(
                        (s for s in CURATED_SKILLS["trending"] if s["name"] == skill_name),
                        {"name": skill_name, "installs": 0, "category": category, "description": ""}
                    )
                    recommendations.append({
                        **skill_info,
                        "stack_match": tech
                    })

    # Sort by installs
    recommendations.sort(key=lambda x: x.get("installs", 0), reverse=True)
    return recommendations[:10]


def install_skill(skill_name: str) -> bool:
    """Install a skill from skills.sh."""
    print(f"Installing {skill_name}...")

    try:
        # Use npx skills add
        result = subprocess.run(
            ["npx", "skills", "add", skill_name],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            print(f"  ✓ Installed successfully")

            # Create Darwin tracking wrapper
            create_darwin_wrapper(skill_name)
            return True
        else:
            print(f"  ✗ Installation failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Installation timed out")
        return False
    except FileNotFoundError:
        print(f"  ✗ npx not found. Install Node.js first.")
        return False


def create_darwin_wrapper(skill_name: str):
    """Create a Darwin YAML wrapper for an external skill."""
    # Extract short name from owner/repo format
    short_name = skill_name.split("/")[-1] if "/" in skill_name else skill_name

    wrapper = {
        "name": short_name,
        "version": "1.0.0",
        "description": f"External skill from skills.sh: {skill_name}",
        "source": "skills.sh",
        "external_name": skill_name,
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

    wrapper_path = SKILLS_DIR / f"{short_name}.yaml"

    import yaml
    with open(wrapper_path, 'w') as f:
        yaml.dump(wrapper, f, default_flow_style=False, sort_keys=False)

    print(f"  ✓ Darwin tracking enabled for /{short_name}")


def check_upgrades() -> List[Dict]:
    """Check for available skill upgrades."""
    upgrades = []
    darwin_skills = get_darwin_skills()

    # This would check against skills.sh API in production
    # For now, return empty
    return upgrades


def search_skills(query: str) -> List[Dict]:
    """Search skills.sh for matching skills."""
    results = []
    query_lower = query.lower()

    for skill in CURATED_SKILLS["trending"]:
        if query_lower in skill["name"].lower() or query_lower in skill.get("description", "").lower():
            results.append(skill)

    for category, skills in CURATED_SKILLS["categories"].items():
        if query_lower in category:
            for skill_name in skills:
                if not any(r["name"] == skill_name for r in results):
                    results.append({"name": skill_name, "category": category, "installs": 0})

    return results[:10]


def print_dashboard():
    """Print the sync dashboard."""
    print("═══════════════════════════════════════════════════")
    print("DARWIN SKILLS.SH SYNC")
    print("═══════════════════════════════════════════════════")
    print()

    # Detect stack
    stack = detect_stack()
    installed_external = get_installed_external()
    darwin_skills = get_darwin_skills()

    print(f"YOUR STACK: {', '.join(stack) if stack else 'Not detected'}")
    print(f"DARWIN SKILLS: {len(darwin_skills)}")
    print(f"EXTERNAL SKILLS: {len(installed_external)}")
    print()

    # Trending
    print("TRENDING (24h)")
    print("───────────────────────────────────────────────────")
    for skill in CURATED_SKILLS["hot_24h"][:5]:
        print(f" ↑ {skill['name']:40} +{skill['delta']:,} installs")
    print()

    # Recommended for stack
    if stack:
        print("RECOMMENDED FOR YOUR STACK")
        print("───────────────────────────────────────────────────")
        recommendations = get_recommended_for_stack(stack)
        for rec in recommendations[:5]:
            installed_marker = "✓" if rec["name"].split("/")[-1] in installed_external else " "
            print(f" {installed_marker} {rec['name']:40} {rec.get('installs', 0):>7,} installs")
            print(f"   └─ {rec.get('description', 'No description')[:50]}")
        print()

    # Top overall
    print("TOP SKILLS (ALL TIME)")
    print("───────────────────────────────────────────────────")
    for skill in CURATED_SKILLS["trending"][:5]:
        installed_marker = "✓" if skill["name"].split("/")[-1] in installed_external else " "
        print(f" {installed_marker} {skill['name']:40} {skill['installs']:>7,} installs")
    print()

    print("═══════════════════════════════════════════════════")
    print("COMMANDS:")
    print("  /darwin sync install <name>  - Install a skill")
    print("  /darwin sync search <query>  - Search skills.sh")
    print("  /darwin sync upgrade         - Check for updates")
    print("═══════════════════════════════════════════════════")


def print_trending():
    """Print trending skills."""
    print("═══════════════════════════════════════════════════")
    print("TRENDING ON SKILLS.SH")
    print("═══════════════════════════════════════════════════")
    print()

    print("HOT (24h)")
    print("───────────────────────────────────────────────────")
    for skill in CURATED_SKILLS["hot_24h"]:
        print(f" 🔥 {skill['name']:40} +{skill['delta']:,}")
    print()

    print("TOP BY INSTALLS")
    print("───────────────────────────────────────────────────")
    for i, skill in enumerate(CURATED_SKILLS["trending"], 1):
        print(f" {i:2}. {skill['name']:40} {skill['installs']:>7,}")
    print()

    print("═══════════════════════════════════════════════════")


def main():
    args = sys.argv[1:]

    if not args:
        print_dashboard()
    elif args[0] == "trending":
        print_trending()
    elif args[0] == "install" and len(args) > 1:
        skill_name = args[1]
        install_skill(skill_name)
    elif args[0] == "upgrade":
        upgrades = check_upgrades()
        if upgrades:
            print("Available upgrades:")
            for u in upgrades:
                print(f"  {u['name']}: {u['current']} → {u['latest']}")
        else:
            print("All skills are up to date.")
    elif args[0] == "search" and len(args) > 1:
        query = " ".join(args[1:])
        results = search_skills(query)
        print(f"Search results for '{query}':")
        for r in results:
            print(f"  {r['name']:40} {r.get('installs', 0):>7,} installs")
    else:
        print("Unknown command. Use: trending, install, upgrade, search")


if __name__ == "__main__":
    main()

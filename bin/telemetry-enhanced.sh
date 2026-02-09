#!/bin/bash
# Darwin Enhanced Telemetry Hook
# Captures skill usage, git activity, and build status

DARWIN_DIR="$HOME/.claude/darwin"
TELEMETRY_DIR="$DARWIN_DIR/telemetry"
ACTIVITY_FILE="$TELEMETRY_DIR/activity.json"

# Ensure directories exist
mkdir -p "$TELEMETRY_DIR"

# Initialize activity file if needed
if [ ! -f "$ACTIVITY_FILE" ]; then
    echo '{"git_commits": 0, "build_failures": 0, "skill_invocations": {}, "last_updated": ""}' > "$ACTIVITY_FILE"
fi

# Function to update JSON field
update_json() {
    local file="$1"
    local key="$2"
    local value="$3"

    if command -v python3 &> /dev/null; then
        python3 -c "
import json
with open('$file', 'r') as f:
    data = json.load(f)
data['$key'] = $value
data['last_updated'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
with open('$file', 'w') as f:
    json.dump(data, f, indent=2)
"
    fi
}

# Function to increment counter
increment_counter() {
    local file="$1"
    local key="$2"

    if command -v python3 &> /dev/null; then
        python3 -c "
import json
with open('$file', 'r') as f:
    data = json.load(f)
data['$key'] = data.get('$key', 0) + 1
data['last_updated'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
with open('$file', 'w') as f:
    json.dump(data, f, indent=2)
"
    fi
}

# Function to log skill invocation
log_skill() {
    local skill="$1"
    local context="$2"
    local session_id="${CLAUDE_SESSION_ID:-$(uuidgen 2>/dev/null || echo 'unknown')}"

    if command -v python3 &> /dev/null; then
        python3 -c "
import json
import os
from datetime import datetime

file = '$ACTIVITY_FILE'
with open(file, 'r') as f:
    data = json.load(f)

skills = data.get('skill_invocations', {})
skill = '$skill'
if skill not in skills:
    skills[skill] = {'count': 0, 'last_used': None, 'contexts': []}

skills[skill]['count'] += 1
skills[skill]['last_used'] = datetime.utcnow().isoformat() + 'Z'
if len(skills[skill]['contexts']) < 10:
    skills[skill]['contexts'].append('$context'[:100])

data['skill_invocations'] = skills
data['last_updated'] = datetime.utcnow().isoformat() + 'Z'

with open(file, 'w') as f:
    json.dump(data, f, indent=2)
"
    fi
}

# Function to detect git activity
detect_git_activity() {
    if [ -d ".git" ] || git rev-parse --git-dir > /dev/null 2>&1; then
        # Count recent commits
        local commits=$(git log --oneline --since="7 days ago" 2>/dev/null | wc -l | tr -d ' ')

        if command -v python3 &> /dev/null; then
            python3 -c "
import json
with open('$ACTIVITY_FILE', 'r') as f:
    data = json.load(f)
data['git_commits'] = int('$commits')
data['last_updated'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
with open('$ACTIVITY_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
        fi
    fi
}

# Function to detect build failures
detect_build_failures() {
    local failures=0

    # Check for TypeScript errors in recent logs
    if [ -f "tsconfig.json" ]; then
        # Try running tsc in check mode
        if ! npx tsc --noEmit > /dev/null 2>&1; then
            failures=$((failures + 1))
        fi
    fi

    # Check for npm/yarn errors
    if [ -f "package.json" ]; then
        if [ -f ".npm-debug.log" ] && [ "$(find .npm-debug.log -mmin -60 2>/dev/null)" ]; then
            failures=$((failures + 1))
        fi
    fi

    if [ $failures -gt 0 ]; then
        if command -v python3 &> /dev/null; then
            python3 -c "
import json
with open('$ACTIVITY_FILE', 'r') as f:
    data = json.load(f)
data['build_failures'] = data.get('build_failures', 0) + $failures
data['last_updated'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
with open('$ACTIVITY_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
        fi
    fi
}

# Main command handling
case "$1" in
    "skill")
        log_skill "$2" "$3"
        ;;
    "git")
        detect_git_activity
        ;;
    "build")
        detect_build_failures
        ;;
    "increment")
        increment_counter "$ACTIVITY_FILE" "$2"
        ;;
    "show")
        cat "$ACTIVITY_FILE" | python3 -m json.tool 2>/dev/null || cat "$ACTIVITY_FILE"
        ;;
    "reset")
        echo '{"git_commits": 0, "build_failures": 0, "skill_invocations": {}, "last_updated": ""}' > "$ACTIVITY_FILE"
        echo "Activity reset."
        ;;
    *)
        echo "Darwin Enhanced Telemetry"
        echo "Usage:"
        echo "  telemetry-enhanced.sh skill <name> <context>  - Log skill usage"
        echo "  telemetry-enhanced.sh git                     - Detect git activity"
        echo "  telemetry-enhanced.sh build                   - Detect build failures"
        echo "  telemetry-enhanced.sh show                    - Show activity data"
        echo "  telemetry-enhanced.sh reset                   - Reset activity"
        ;;
esac

#!/bin/bash
#
# Darwin Skill Installer
# Installs external skills from skills.sh and adapts them for Darwin tracking
#

set -e

DARWIN_DIR="$HOME/.claude/darwin"
SKILLS_DIR="$DARWIN_DIR/skills"
COMMANDS_DIR="$HOME/.claude/commands"
EXTERNAL_DIR="$DARWIN_DIR/external"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
    echo "Darwin Skill Installer"
    echo ""
    echo "Usage: install-skill.sh <skill-name-or-repo>"
    echo ""
    echo "Examples:"
    echo "  install-skill.sh vercel-react-best-practices"
    echo "  install-skill.sh vercel-labs/agent-skills"
    echo ""
    echo "This will:"
    echo "  1. Install the skill via 'npx skills add'"
    echo "  2. Create a Darwin YAML wrapper for tracking"
    echo "  3. Add it to the evolution system"
}

if [ -z "$1" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    usage
    exit 0
fi

SKILL_INPUT="$1"

echo "═══════════════════════════════════════════════════"
echo "DARWIN SKILL INSTALLER"
echo "═══════════════════════════════════════════════════"
echo ""

# Determine if input is repo or skill name
if [[ "$SKILL_INPUT" == *"/"* ]]; then
    REPO="$SKILL_INPUT"
    SKILL_NAME=$(basename "$SKILL_INPUT")
else
    SKILL_NAME="$SKILL_INPUT"
    # Try to find repo from cached discovery
    CACHE_FILE="$DARWIN_DIR/discovery/trending.json"
    if [ -f "$CACHE_FILE" ]; then
        REPO=$(python3 -c "
import json
with open('$CACHE_FILE') as f:
    data = json.load(f)
for s in data.get('skills', []):
    if s.get('skill_id') == '$SKILL_NAME' or s.get('name') == '$SKILL_NAME':
        print(s.get('source', ''))
        break
" 2>/dev/null || echo "")
    fi

    if [ -z "$REPO" ]; then
        echo -e "${YELLOW}Could not find repo for '$SKILL_NAME'${NC}"
        echo "Please provide full repo path: owner/repo"
        exit 1
    fi
fi

echo "Skill: $SKILL_NAME"
echo "Repo:  $REPO"
echo ""

# Step 1: Install via npx skills
echo -e "${GREEN}[1/3]${NC} Installing via skills.sh..."
if command -v npx &> /dev/null; then
    npx skills add "$REPO" 2>&1 || {
        echo -e "${RED}Failed to install skill${NC}"
        echo "Make sure you have Node.js installed and try:"
        echo "  npx skills add $REPO"
        exit 1
    }
else
    echo -e "${RED}npx not found. Please install Node.js first.${NC}"
    exit 1
fi

# Step 2: Create Darwin YAML wrapper
echo ""
echo -e "${GREEN}[2/3]${NC} Creating Darwin tracking wrapper..."

mkdir -p "$EXTERNAL_DIR"
mkdir -p "$SKILLS_DIR"

# Convert skill name to kebab-case
SKILL_KEBAB=$(echo "$SKILL_NAME" | tr '[:upper:]' '[:lower:]' | tr '_' '-' | tr ' ' '-')

# Create YAML wrapper for Darwin tracking
YAML_FILE="$SKILLS_DIR/${SKILL_KEBAB}.yaml"

# Check if skill markdown was installed
SKILL_MD="$COMMANDS_DIR/${SKILL_KEBAB}.md"
if [ ! -f "$SKILL_MD" ]; then
    # Try to find it with different naming
    SKILL_MD=$(find "$COMMANDS_DIR" -iname "*${SKILL_NAME}*" -type f 2>/dev/null | head -1)
fi

DESCRIPTION="External skill from skills.sh"
if [ -f "$SKILL_MD" ]; then
    # Try to extract description from the file
    DESC_LINE=$(grep -m1 "^description:" "$SKILL_MD" 2>/dev/null | sed 's/description: *//' || echo "")
    if [ -n "$DESC_LINE" ]; then
        DESCRIPTION="$DESC_LINE"
    fi
fi

cat > "$YAML_FILE" << EOF
name: ${SKILL_KEBAB}
version: 1.0.0
description: >-
  ${DESCRIPTION}
  (External skill from skills.sh - ${REPO})
source: external
external_repo: ${REPO}
modules:
  input: v1
  research: v3
  structure: v1
  output: v2
  workflow: v1
  validation: v3

anti_patterns:
  - "Don't modify the external skill's core logic"
  - "Track usage but defer to original skill behavior"

examples:
  - trigger: "${SKILL_NAME}"

# Note: This is a wrapper for Darwin to track external skill usage
# The actual skill content is in ~/.claude/commands/${SKILL_KEBAB}.md
external: true
installed_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
fitness_history: []
EOF

echo "Created: $YAML_FILE"

# Step 3: Update config to track this skill
echo ""
echo -e "${GREEN}[3/3]${NC} Adding to Darwin tracking..."

CONFIG_FILE="$DARWIN_DIR/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    # Check if skill already in config
    if ! grep -q "^  - ${SKILL_KEBAB}$" "$CONFIG_FILE" 2>/dev/null; then
        # Add to skills list
        if grep -q "^skills:" "$CONFIG_FILE"; then
            sed -i.bak "/^skills:/a\\
  - ${SKILL_KEBAB}" "$CONFIG_FILE" && rm -f "${CONFIG_FILE}.bak"
        fi
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo -e "${GREEN}SUCCESS${NC}"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Installed: ${SKILL_NAME}"
echo "Tracking:  Enabled via Darwin"
echo ""
echo "Use it:    /${SKILL_KEBAB}"
echo "Status:    /darwin status"
echo ""
echo "═══════════════════════════════════════════════════"

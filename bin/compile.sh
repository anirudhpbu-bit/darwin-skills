#!/bin/bash
# Darwin Skill Compiler
# Compiles skill definitions (YAML) into executable skills (Markdown)
# Usage: compile.sh [skill_name] or compile.sh --all

set -e

DARWIN_DIR="$HOME/.claude/darwin"
MODULES_FILE="$DARWIN_DIR/modules/registry.yaml"
SKILLS_DIR="$DARWIN_DIR/skills"
OUTPUT_DIR="$HOME/.claude/commands"

# Check dependencies
if ! command -v yq &> /dev/null; then
    echo "Error: yq is required but not installed"
    echo "Install with: brew install yq"
    exit 1
fi

# Function to get module prompt by type and version
get_module_prompt() {
    local module_type="$1"
    local version="$2"

    yq ".modules.${module_type}.${version}.prompt // \"\"" "$MODULES_FILE"
}

# Function to compile a single skill
compile_skill() {
    local skill_name="$1"
    local skill_file="$SKILLS_DIR/${skill_name}.yaml"
    local output_file="$OUTPUT_DIR/${skill_name}.md"

    if [ ! -f "$skill_file" ]; then
        echo "Error: Skill definition not found: $skill_file"
        return 1
    fi

    echo "Compiling: $skill_name"

    # Read skill metadata
    local description=$(yq '.description' "$skill_file")
    local version=$(yq '.version' "$skill_file")

    # Read module versions
    local input_ver=$(yq '.modules.input // "v1"' "$skill_file")
    local research_ver=$(yq '.modules.research // "v1"' "$skill_file")
    local structure_ver=$(yq '.modules.structure // "v1"' "$skill_file")
    local output_ver=$(yq '.modules.output // "v1"' "$skill_file")
    local workflow_ver=$(yq '.modules.workflow // "v1"' "$skill_file")
    local validation_ver=$(yq '.modules.validation // "v3"' "$skill_file")

    # Get module prompts
    local input_prompt=$(get_module_prompt "input" "$input_ver")
    local research_prompt=$(get_module_prompt "research" "$research_ver")
    local structure_prompt=$(get_module_prompt "structure" "$structure_ver")
    local output_prompt=$(get_module_prompt "output" "$output_ver")
    local workflow_prompt=$(get_module_prompt "workflow" "$workflow_ver")
    local validation_prompt=$(get_module_prompt "validation" "$validation_ver")

    # Get core prompt
    local core_prompt=$(yq '.core_prompt' "$skill_file")

    # Assemble the skill
    cat > "$output_file" << EOF
---
description: $description
darwin_version: $version
darwin_modules:
  input: $input_ver
  research: $research_ver
  structure: $structure_ver
  output: $output_ver
  workflow: $workflow_ver
  validation: $validation_ver
---

$core_prompt

$input_prompt

$research_prompt

$output_prompt

$workflow_prompt

$validation_prompt
EOF

    # Update last_compiled in skill definition
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    yq -i ".last_compiled = \"$timestamp\"" "$skill_file"

    echo "  → $output_file"
    echo "  Modules: input=$input_ver research=$research_ver structure=$structure_ver output=$output_ver workflow=$workflow_ver validation=$validation_ver"
}

# Main
if [ "$1" == "--all" ]; then
    echo "═══════════════════════════════════════════════════"
    echo "DARWIN SKILL COMPILER - All Skills"
    echo "═══════════════════════════════════════════════════"
    echo ""

    for skill_file in "$SKILLS_DIR"/*.yaml; do
        if [ -f "$skill_file" ]; then
            skill_name=$(basename "$skill_file" .yaml)
            compile_skill "$skill_name"
            echo ""
        fi
    done

    echo "═══════════════════════════════════════════════════"
    echo "Compilation complete"
    echo "═══════════════════════════════════════════════════"
elif [ -n "$1" ]; then
    compile_skill "$1"
else
    echo "Usage: compile.sh [skill_name] or compile.sh --all"
    echo ""
    echo "Available skills:"
    for skill_file in "$SKILLS_DIR"/*.yaml; do
        if [ -f "$skill_file" ]; then
            echo "  - $(basename "$skill_file" .yaml)"
        fi
    done
fi

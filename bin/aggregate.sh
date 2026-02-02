#!/bin/bash
# Darwin Telemetry Aggregator
# Processes raw telemetry into metrics

set -e

DARWIN_DIR="$HOME/.claude/darwin"
TELEMETRY_DIR="$DARWIN_DIR/telemetry"
SKILLS_LOG="$TELEMETRY_DIR/skills.jsonl"
INVOCATIONS_LOG="$TELEMETRY_DIR/invocations.jsonl"
OUTPUT_FILE="$TELEMETRY_DIR/aggregates.json"

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed"
    exit 1
fi

# Initialize output
echo "{}" > "$OUTPUT_FILE"

# Calculate date range (last 7 days)
if [[ "$OSTYPE" == "darwin"* ]]; then
    WEEK_AGO=$(date -v-7d -u +"%Y-%m-%dT00:00:00Z")
else
    WEEK_AGO=$(date -d "7 days ago" -u +"%Y-%m-%dT00:00:00Z")
fi

# Count skill invocations
if [ -f "$SKILLS_LOG" ]; then
    SKILL_COUNTS=$(cat "$SKILLS_LOG" | \
        jq -s --arg since "$WEEK_AGO" '
            [.[] | select(.timestamp >= $since and .event == "skill_start")] |
            group_by(.skill) |
            map({skill: .[0].skill, count: length}) |
            sort_by(-.count)
        ')
else
    SKILL_COUNTS="[]"
fi

# Count total events
if [ -f "$INVOCATIONS_LOG" ]; then
    TOTAL_EVENTS=$(wc -l < "$INVOCATIONS_LOG" | tr -d ' ')
    FIRST_EVENT=$(head -1 "$INVOCATIONS_LOG" 2>/dev/null | jq -r '.timestamp // "unknown"')
else
    TOTAL_EVENTS=0
    FIRST_EVENT="never"
fi

if [ -f "$SKILLS_LOG" ]; then
    SKILL_EVENTS=$(wc -l < "$SKILLS_LOG" | tr -d ' ')
else
    SKILL_EVENTS=0
fi

# Build aggregate JSON
jq -n \
    --arg generated "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
    --arg since "$WEEK_AGO" \
    --arg first_event "$FIRST_EVENT" \
    --argjson total_events "$TOTAL_EVENTS" \
    --argjson skill_events "$SKILL_EVENTS" \
    --argjson skill_counts "$SKILL_COUNTS" \
    '{
        generated_at: $generated,
        period_start: $since,
        first_event: $first_event,
        total_tool_events: $total_events,
        total_skill_invocations: $skill_events,
        skills: $skill_counts
    }' > "$OUTPUT_FILE"

echo "Aggregates written to $OUTPUT_FILE"
cat "$OUTPUT_FILE"

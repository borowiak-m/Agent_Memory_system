#!/bin/bash
# Memory Tracker - Tracks conversations for arbitrary entities
# Usage: source this file and call functions

MEMORY_TRACKERS_DIR="/home/dev/agents/memory/trackers"

# Ensure base directories exist
mkdir -p "$MEMORY_TRACKERS_DIR"

#######################################
# Register a new tracker type
# Arguments:
#   tracker_type - e.g., "shopify_product", "customer_support"
#   description - What this tracker is for
#######################################
register_tracker_type() {
    local tracker_type="$1"
    local description="${2:-}"
    
    [ -z "$tracker_type" ] && echo '{"error": "tracker_type required"}' && return 1
    
    local tracker_dir="$MEMORY_TRACKERS_DIR/$tracker_type"
    mkdir -p "$tracker_dir/active"
    mkdir -p "$tracker_dir/memory"
    
    # Create tracker config
    cat > "$tracker_dir/config.json" << EOF
{
  "tracker_type": "$tracker_type",
  "description": "$description",
  "created_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "active_count": 0,
  "memory_count": 0
}
EOF
    
    echo "{\"status\": \"ok\", \"tracker_type\": \"$tracker_type\", \"message\": \"Tracker type registered\"}"
}

#######################################
# Start tracking a new entity
# Arguments:
#   tracker_type - The tracker type
#   entity_key - Unique key for the entity (e.g., PROD-123)
#   title - Optional title/description
#######################################
start_tracking() {
    local tracker_type="$1"
    local entity_key="$2"
    local title="${3:-}"
    
    [ -z "$tracker_type" ] && echo '{"error": "tracker_type required"}' && return 1
    [ -z "$entity_key" ] && echo '{"error": "entity_key required"}' && return 1
    
    local tracker_dir="$MEMORY_TRACKERS_DIR/$tracker_type"
    local active_dir="$tracker_dir/active/$entity_key"
    
    # Check if already active
    if [ -d "$active_dir" ]; then
        echo "{\"status\": \"exists\", \"message\": \"Entity $entity_key is already being tracked\"}"
        return 1
    fi
    
    # Check if in memory (archived)
    if [ -d "$tracker_dir/memory/$entity_key" ]; then
        echo "{\"status\": \"in_memory\", \"message\": \"Entity $entity_key exists in memory, reopen first\"}"
        return 1
    fi
    
    mkdir -p "$active_dir"
    
    # Create manifest
    cat > "$active_dir/manifest.json" << EOF
{
  "tracker_type": "$tracker_type",
  "entity_key": "$entity_key",
  "title": "$title",
  "status": "active",
  "created_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "updated_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "message_count": 0
}
EOF
    
    # Create empty conversation
    echo "[]" > "$active_dir/conversation.json"
    
    # Update tracker config
    local count=$(ls "$tracker_dir/active/" 2>/dev/null | wc -l | tr -d ' ')
    jq --argjson count "$count" '.active_count = $count' "$tracker_dir/config.json" > /tmp/tracker_tmp.json && mv /tmp/tracker_tmp.json "$tracker_dir/config.json"
    
    echo "{\"status\": \"ok\", \"tracker_type\": \"$tracker_type\", \"entity_key\": \"$entity_key\", \"message\": \"Started tracking\"}"
}

#######################################
# Add a message to an active conversation
# Arguments:
#   tracker_type - The tracker type
#   entity_key - The entity key
#   sender - Who sent the message (user, assistant, system)
#   content - The message content
#######################################
add_message() {
    local tracker_type="$1"
    local entity_key="$2"
    local sender="$3"
    local content="$4"
    
    [ -z "$tracker_type" ] && echo '{"error": "tracker_type required"}' && return 1
    [ -z "$entity_key" ] && echo '{"error": "entity_key required"}' && return 1
    [ -z "$sender" ] && echo '{"error": "sender required"}' && return 1
    [ -z "$content" ] && echo '{"error": "content required"}' && return 1
    
    local active_dir="$MEMORY_TRACKERS_DIR/$tracker_type/active/$entity_key"
    
    if [ ! -d "$active_dir" ]; then
        echo "{\"error\": \"Entity $entity_key is not being tracked\"}"
        return 1
    fi
    
    local conv_file="$active_dir/conversation.json"
    local manifest_file="$active_dir/manifest.json"
    
    # Add message to conversation
    local temp_conv=$(mktemp)
    jq --arg sender "$sender" \
       --arg content "$content" \
       --arg timestamp "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
       '. += [{"sender": $sender, "content": $content, "timestamp": $timestamp}]' \
       "$conv_file" > "$temp_conv" && mv "$temp_conv" "$conv_file"
    
    # Update manifest
    local msg_count=$(jq 'length' "$conv_file")
    jq --argjson count "$msg_count" \
       --arg timestamp "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
       '.message_count = $count | .updated_at = $timestamp' \
       "$manifest_file" > /tmp/manifest_tmp.json && mv /tmp/manifest_tmp.json "$manifest_file"
    
    echo "{\"status\": \"ok\", \"message\": \"Message added to $tracker_type/$entity_key\"}"
}

#######################################
# Close conversation and move to memory with summary
# Arguments:
#   tracker_type - The tracker type
#   entity_key - The entity key
#   summary - Summary of what was done/resolved
#######################################
close_conversation() {
    local tracker_type="$1"
    local entity_key="$2"
    local summary="$3"
    
    [ -z "$tracker_type" ] && echo '{"error": "tracker_type required"}' && return 1
    [ -z "$entity_key" ] && echo '{"error": "entity_key required"}' && return 1
    
    local tracker_dir="$MEMORY_TRACKERS_DIR/$tracker_type"
    local active_dir="$tracker_dir/active/$entity_key"
    local memory_dir="$tracker_dir/memory/$entity_key"
    
    if [ ! -d "$active_dir" ]; then
        echo "{\"error\": \"Entity $entity_key is not being tracked\"}"
        return 1
    fi
    
    # Move to memory
    mkdir -p "$memory_dir"
    mv "$active_dir/manifest.json" "$memory_dir/"
    mv "$active_dir/conversation.json" "$memory_dir/"
    
    # Update manifest with summary and status
    cat > "$memory_dir/manifest.json" << EOF
$(jq --arg summary "$summary" \
     --arg timestamp "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
     '.status = "closed" | .closed_at = $timestamp | .summary = $summary' \
     "$memory_dir/manifest.json")
EOF
    
    # Remove old active folder
    rmdir "$active_dir" 2>/dev/null || rm -rf "$active_dir"
    
    # Update tracker counts
    local active_count=$(ls "$tracker_dir/active/" 2>/dev/null | wc -l | tr -d ' ')
    local memory_count=$(ls "$tracker_dir/memory/" 2>/dev/null | wc -l | tr -d ' ')
    jq --argjson active "$active_count" \
       --argjson memory "$memory_count" \
       '.active_count = $active | .memory_count = $memory' \
       "$tracker_dir/config.json" > /tmp/tracker_tmp.json && mv /tmp/tracker_tmp.json "$tracker_dir/config.json"
    
    echo "{\"status\": \"ok\", \"tracker_type\": \"$tracker_type\", \"entity_key\": \"$entity_key\", \"message\": \"Closed and archived to memory\"}"
}

#######################################
# Reopen a closed conversation from memory
# Arguments:
#   tracker_type - The tracker type
#   entity_key - The entity key
#######################################
reopen_conversation() {
    local tracker_type="$1"
    local entity_key="$2"
    
    [ -z "$tracker_type" ] && echo '{"error": "tracker_type required"}' && return 1
    [ -z "$entity_key" ] && echo '{"error": "entity_key required"}' && return 1
    
    local tracker_dir="$MEMORY_TRACKERS_DIR/$tracker_type"
    local memory_dir="$tracker_dir/memory/$entity_key"
    local active_dir="$tracker_dir/active/$entity_key"
    
    if [ ! -d "$memory_dir" ]; then
        echo "{\"error\": \"Entity $entity_key not found in memory\"}"
        return 1
    fi
    
    # Check if already active
    if [ -d "$active_dir" ]; then
        echo "{\"error\": \"Entity $entity_key is already active\"}"
        return 1
    fi
    
    # Move back to active
    mkdir -p "$active_dir"
    mv "$memory_dir/manifest.json" "$active_dir/"
    mv "$memory_dir/conversation.json" "$active_dir/"
    
    # Update manifest status
    jq --arg timestamp "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
       '.status = "active" | .reopened_at = $timestamp | del(.closed_at) | del(.summary)' \
       "$active_dir/manifest.json" > /tmp/manifest_tmp.json && mv /tmp/manifest_tmp.json "$active_dir/manifest.json"
    
    # Remove old memory folder
    rmdir "$memory_dir" 2>/dev/null || rm -rf "$memory_dir"
    
    # Update tracker counts
    local active_count=$(ls "$tracker_dir/active/" 2>/dev/null | wc -l | tr -d ' ')
    local memory_count=$(ls "$tracker_dir/memory/" 2>/dev/null | wc -l | tr -d ' ')
    jq --argjson active "$active_count" \
       --argjson memory "$memory_count" \
       '.active_count = $active | .memory_count = $memory' \
       "$tracker_dir/config.json" > /tmp/tracker_tmp.json && mv /tmp/tracker_tmp.json "$tracker_dir/config.json"
    
    echo "{\"status\": \"ok\", \"tracker_type\": \"$tracker_type\", \"entity_key\": \"$entity_key\", \"message\": \"Reopened from memory\"}"
}

#######################################
# List tracker types
#######################################
list_tracker_types() {
    local result="["
    local first=true
    
    for dir in "$MEMORY_TRACKERS_DIR"/*; do
        [ -d "$dir" ] || continue
        local tracker_type=$(basename "$dir")
        local config="$dir/config.json"
        
        if [ -f "$config" ]; then
            [ "$first" = false ] && result+=","
            result+=$(jq --arg type "$tracker_type" '{tracker_type: $type} * .' "$config")
            first=false
        fi
    done
    
    result+="]"
    echo "$result" | jq .
}

#######################################
# List active entities for a tracker
# Arguments:
#   tracker_type - The tracker type
#######################################
list_active() {
    local tracker_type="$1"
    
    [ -z "$tracker_type" ] && echo '{"error": "tracker_type required"}' && return 1
    
    local tracker_dir="$MEMORY_TRACKERS_DIR/$tracker_type"
    
    if [ ! -d "$tracker_dir" ]; then
        echo "{\"error\": \"Tracker type $tracker_type not found\"}"
        return 1
    fi
    
    local result="["
    local first=true
    
    for dir in "$tracker_dir/active"/*; do
        [ -d "$dir" ] || continue
        local entity_key=$(basename "$dir")
        local manifest="$dir/manifest.json"
        
        if [ -f "$manifest" ]; then
            [ "$first" = false ] && result+=","
            result+=$(jq --arg key "$entity_key" '{entity_key: $key} * .' "$manifest")
            first=false
        fi
    done
    
    result+="]"
    echo "$result" | jq .
}

#######################################
# List memory (archived) entities for a tracker
# Arguments:
#   tracker_type - The tracker type
#######################################
list_memory() {
    local tracker_type="$1"
    
    [ -z "$tracker_type" ] && echo '{"error": "tracker_type required"}' && return 1
    
    local tracker_dir="$MEMORY_TRACKERS_DIR/$tracker_type"
    
    if [ ! -d "$tracker_dir" ]; then
        echo "{\"error\": \"Tracker type $tracker_type not found\"}"
        return 1
    fi
    
    local result="["
    local first=true
    
    for dir in "$tracker_dir/memory"/*; do
        [ -d "$dir" ] || continue
        local entity_key=$(basename "$dir")
        local manifest="$dir/manifest.json"
        
        if [ -f "$manifest" ]; then
            [ "$first" = false ] && result+=","
            result+=$(jq --arg key "$entity_key" '{entity_key: $key} * .' "$manifest")
            first=false
        fi
    done
    
    result+="]"
    echo "$result" | jq .
}

# Export functions if being used in a subshell
if [ "$BASH_SOURCE[0]" != "$0" ]; then
    export -f register_tracker_type
    export -f start_tracking
    export -f add_message
    export -f close_conversation
    export -f reopen_conversation
    export -f list_tracker_types
    export -f list_active
    export -f list_memory
fi

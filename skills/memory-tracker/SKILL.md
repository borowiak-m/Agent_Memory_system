# Memory Tracker Skill

## Purpose

Manages tracking of conversations for different entity types (products, customers, etc.) 
similar to GitHub issues but for any arbitrary topic. When conversations are closed,
they get archived to memory with a summary.

## When to Use This Skill

- When you want to track ongoing conversations about a specific entity (product, customer, etc.)
- When a conversation topic is resolved and should be archived with a summary
- When you need to reopen an archived conversation

## Concepts

- **Tracker**: A category of things to track (e.g., "shopify_product", "customer_support", "feature_request")
- **Entity Key**: The specific item being tracked (e.g., "PROD-123", "customer-456")
- **Conversation**: Messages/exchanges about an entity
- **Memory**: Archived conversations with summaries

## Storage Location

Trackers are stored in: `/home/dev/agents/memory/trackers/`

## Usage

### 1. Register a new tracker type

```bash
# Register a new tracker type
register_tracker_type "shopify_product" "Track Shopify product conversations"
```

### 2. Start tracking a new entity

```bash
# Start tracking a new entity (creates a conversation)
start_tracking "shopify_product" "PROD-123" "Blue widget variant"
```

### 3. Add message to conversation

```bash
# Add a message to an active conversation
add_message "shopify_product" "PROD-123" "user" "Check inventory for this product"
```

### 4. Close conversation with summary

```bash
# Close and archive with summary
close_conversation "shopify_product" "PROD-123" "Checked inventory - 50 units available, restocked"
```

### 5. Reopen a closed conversation

```bash
# Reopen an archived conversation
reopen_conversation "shopify_product" "PROD-123"
```

### 6. List all trackers

```bash
# List all tracker types
list_tracker_types

# List all active entities for a tracker
list_active "shopify_product"

# List archived (memory) for a tracker
list_memory "shopify_product"
```

## Workflow Example: Shopify Products

```
1. Start tracking: start_tracking "shopify_product" "PROD-001" "Winter jacket"
2. Add messages as you work on the product:
   - add_message "shopify_product" "PROD-001" "user" "Update pricing to $99"
   - add_message "shopify_product" "PROD-001" "assistant" "Price updated"
3. When done: close_conversation "shopody_product" "PROD-001" "Price updated to $99, verified stock"
4. Later: reopen_conversation "shopify_product" "PROD-001" if needed
```

## Output

This skill returns JSON with status and results. The memory structure mirrors GitHub issues:
- Active: `/home/dev/agents/memory/trackers/{tracker_type}/active/{entity_key}/`
- Memory (archived): `/home/dev/agents/memory/trackers/{tracker_type}/memory/{entity_key}/`

Each folder contains:
- `manifest.json` - Metadata (created, status, summary)
- `conversation.json` - All messages

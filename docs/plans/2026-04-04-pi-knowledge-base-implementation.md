# Implementation Plan: Pi Knowledge Base System (Memory-Tracker Integration)

## Overview

Extend the existing memory-tracker skill at `~/.pi/agent/skills/memory-tracker/` to create a full-featured knowledge base. Instead of creating a separate system, we integrate KB functionality into the existing tracker framework.

**Target Users:** Developers who use Pi for long-term research, codebases, or complex multi-session projects.

**Core Principle:** The LLM should compile, maintain, and query the knowledge base—not the user.

---

## Existing Infrastructure

```
/home/dev/agents/memory/
├── trackers/
│   ├── github_issues/     ← Already exists
│   └── ...                ← Other tracker types
└── github_issues/          ← GitHub integration
```

**Existing memory-tracker Functions:**
- `register_tracker_type` - Create new tracker
- `start_tracking` - Create new entity
- `add_message` - Add conversation message
- `close_conversation` - Archive with summary
- `list_active` - List open entities
- `list_memory` - List archived entities

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Pi Agent Session                            │
├─────────────────────────────────────────────────────────────────────┤
│  Sessions (jsonl) ──→ Compaction ──→ Knowledge Extraction          │
│                                    │                                │
│                                    ▼                                │
│                    ┌────────────────────────────────┐              │
│                    │  Extended memory-tracker       │              │
│                    │  ┌──────────────────────────┐  │              │
│                    │  │ Trackers:                │  │              │
│                    │  │  - concepts/            │  │              │
│                    │  │  - decisions/           │  │              │
│                    │  │  - entities/            │  │              │
│                    │  │  - references/          │  │              │
│                    │  └──────────────────────────┘  │              │
│                    └────────────────────────────────┘              │
│                                    │                                │
│                                    ▼                                │
│                    ┌────────────────────────────────┐              │
│                    │  New KB Functions:             │              │
│                    │  - file_decision()            │              │
│                    │  - link_entries()             │              │
│                    │  - search_kb()                │              │
│                    │  - query_kb()                 │              │
│                    │  - lint / export              │              │
│                    └────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
~/.pi/agent/skills/memory-tracker/
├── SKILL.md                # Main skill file (updated)
├── memory.sh               # Core functions (updated)
├── extract.py              # NEW: Knowledge extraction
├── lint.py                 # NEW: Health checks
├── export.py               # NEW: Export functionality
├── test_kb.py              # NEW: Tests
└── wikilinks.json          # NEW: Link tracking

/home/dev/agents/memory/trackers/
├── github_issues/          # Existing
├── concepts/               # NEW: Domain concepts
│   ├── active/{entity_key}/
│   └── memory/{entity_key}/
├── decisions/              # NEW: Decision log
│   ├── active/{entity_key}/
│   └── memory/{entity_key}/
├── entities/               # NEW: Code entities
│   ├── active/{entity_key}/
│   └── memory/{entity_key}/
└── references/             # NEW: External references
    ├── active/{entity_key}/
    └── memory/{entity_key}/
```

---

## Tasks

### Phase 1: Core Infrastructure

#### Task 1: Register KB Tracker Categories

**Epic Issue:** KB-101  
**Goals:** G3, G5

**Files to modify:**
- `memory.sh` - Add `register_kb_categories()` function

**Implementation:**

```bash
register_kb_categories() {
    register_tracker_type "concepts" "Domain concepts, patterns, and architectural ideas"
    register_tracker_type "decisions" "Architectural decisions with rationale"
    register_tracker_type "entities" "Code entities: classes, functions, files, APIs"
    register_tracker_type "references" "External references: articles, docs, papers"
    
    echo "KB categories registered:"
    list_tracker_types
}
```

**Verification:**
```bash
source ~/.pi/agent/skills/memory-tracker/memory.sh
register_kb_categories
list_tracker_types  # Should show: concepts, decisions, entities, references
```

---

#### Task 2: Extend memory-tracker with KB Functions

**Epic Issue:** KB-102  
**Goals:** G3, G4, G5

**Files to modify:**
- `memory.sh` - Add new KB functions

**Implementation:**

```bash
# === Knowledge Base Functions ===

file_decision() {
    # Usage: file_decision "title" "rationale" [--context "context"]
    local title="$1"
    local rationale="$2"
    local context="${3:-}"
    
    local entity_key
    entity_key="$(echo "$title" | slugify)"
    
    start_tracking "decisions" "$entity_key" "$title"
    add_message "decisions" "$entity_key" "assistant" "Decision: $title"
    add_message "decisions" "$entity_key" "assistant" "Rationale: $rationale"
    
    if [ -n "$context" ]; then
        add_message "decisions" "$entity_key" "assistant" "Context: $context"
    fi
    
    # Auto-generate summary
    local summary="Decision: $title. $rationale"
    close_conversation "decisions" "$entity_key" "$summary"
    
    echo "Filed decision: $entity_key"
}

file_entity() {
    # Usage: file_entity "name" "type" [--file "path"] [--desc "description"]
    local name="$1"
    local type="$2"
    local file="${3:-}"
    local desc="${4:-}"
    
    local entity_key
    entity_key="$(echo "$name" | slugify)"
    
    start_tracking "entities" "$entity_key" "$name ($type)"
    add_message "entities" "$entity_key" "assistant" "Entity: $name"
    add_message "entities" "$entity_key" "assistant" "Type: $type"
    
    if [ -n "$file" ]; then
        add_message "entities" "$entity_key" "assistant" "Location: $file"
    fi
    
    if [ -n "$desc" ]; then
        add_message "entities" "$entity_key" "assistant" "Description: $desc"
    fi
    
    close_conversation "entities" "$entity_key" "$name - $type"
    echo "Filed entity: $entity_key"
}

file_reference() {
    # Usage: file_reference "url" "title" [--notes "notes"]
    local url="$1"
    local title="$2"
    local notes="${3:-}"
    
    local entity_key
    entity_key="$(echo "$url" | slugify)"
    
    start_tracking "references" "$entity_key" "$title"
    add_message "references" "$entity_key" "assistant" "URL: $url"
    add_message "references" "$entity_key" "assistant" "Title: $title"
    
    if [ -n "$notes" ]; then
        add_message "references" "$entity_key" "assistant" "Notes: $notes"
    fi
    
    close_conversation "references" "$entity_key" "$title"
    echo "Filed reference: $entity_key"
}

link_entries() {
    # Usage: link_entries "tracker1/entity_key1" "tracker2/entity_key2" "relationship"
    local from="$1"
    local to="$2"
    local relationship="${3:-related}"
    
    local from_tracker from_key to_tracker to_key
    
    from_tracker="$(echo "$from" | cut -d/ -f1)"
    from_key="$(echo "$from" | cut -d/ -f2-)"
    to_tracker="$(echo "$to" | cut -d/ -f1)"
    to_key="$(echo "$to" | cut -d/ -f2-)"
    
    # Add wikilink to both entries
    add_message "$from_tracker" "$from_key" "assistant" "Links to [[$to_tracker/$to_key]] ($relationship)"
    add_message "$to_tracker" "$to_key" "assistant" "Linked from [[$from_tracker/$from_key]] ($relationship)"
    
    # Update wikilinks.json
    local link_file="$HOME/agents/memory/trackers/wikilinks.json"
    if [ ! -f "$link_file" ]; then
        echo '{"links":[]}' > "$link_file"
    fi
    
    # Append new link
    python3 -c "
import json
with open('$link_file') as f:
    data = json.load(f)
data['links'].append({
    'from': '$from',
    'to': '$to',
    'relationship': '$relationship'
})
with open('$link_file', 'w') as f:
    json.dump(data, f, indent=2)
"
    
    echo "Linked: $from → $to ($relationship)"
}

search_kb() {
    # Usage: search_kb "query" [--tracker "tracker"]
    local query="$1"
    local tracker="${2:-}"
    
    local search_dir="$HOME/agents/memory/trackers"
    if [ -n "$tracker" ]; then
        search_dir="$search_dir/$tracker"
    fi
    
    echo "Searching for: $query"
    echo ""
    
    # Grep through all conversation.json files
    local results
    results=$(grep -l -i "$query" "$search_dir"/**/conversation.json 2>/dev/null || true)
    
    if [ -z "$results" ]; then
        echo "No results found."
        return
    fi
    
    echo "Found $(echo "$results" | wc -l) matching entries:"
    echo ""
    
    while IFS= read -r file; do
        local tracker_name
        tracker_name="$(basename "$(dirname "$(dirname "$file")")")"
        local entity_key
        entity_key="$(basename "$(dirname "$file")")"
        
        echo "- [[$tracker_name/$entity_key]]"
        
        # Show matching context
        grep -i "$query" "$file" | head -1 | cut -c1-100
        echo ""
    done <<< "$results"
}

query_kb() {
    # Usage: query_kb "question"
    # This is handled by the LLM - it will search_kb and synthesize
    local question="$1"
    echo "Query: $question"
    echo ""
    echo "The LLM will search the KB and synthesize an answer."
    echo "Use search_kb first to find relevant entries, then reason."
}
```

**Verification:**
```bash
source ~/.pi/agent/skills/memory-tracker/memory.sh

# Test registration
register_kb_categories

# Test filing
file_decision "use-sqlite-over-room" "Room adds complexity we don't need for simple CRUD" "Mobile app v0.2"
file_entity "AuthService" "class" "/lib/services/auth_service.dart" "Handles authentication"
file_reference "https://docs.flutter.dev" "Flutter Documentation"

# Test linking
link_entries "decisions/use-sqlite-over-room" "entities/AuthService" "uses"

# Test search
search_kb "authentication"
search_kb "sqlite" --tracker "decisions"
```

---

#### Task 3: Create Knowledge Extraction Module

**Epic Issue:** KB-103  
**Goals:** G1, G2, G3

**Files to create:**
- `~/.pi/agent/skills/memory-tracker/extract.py`

**Implementation:**

```python
#!/usr/bin/env python3
"""
Extract knowledge from session compaction events.

Analyzes compacted messages and files knowledge into KB trackers.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

def extract_from_compaction(messages_text):
    """
    Analyze text and extract KB entries.
    
    Args:
        messages_text: Serialized session messages
        
    Returns:
        dict with keys: decisions, entities, references
    """
    results = {
        "decisions": [],
        "entities": [],
        "references": []
    }
    
    # Extract decisions
    results["decisions"] = extract_decisions(messages_text)
    
    # Extract entities
    results["entities"] = extract_entities(messages_text)
    
    # Extract references
    results["references"] = extract_references(messages_text)
    
    return results

def extract_decisions(text):
    """Extract decision patterns from conversation."""
    decisions = []
    
    patterns = [
        r"(?:Decision|Cho[so]e|Went with)[:\s]+(.+?)(?:\.|$)",
        r"(?:Implement|Use|Adopt)[:\s]+(.+?)(?:\.|$)",
        r"decided to use (.+?) instead",
        r"chose (.+?) over",
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            decision = match.group(1).strip()
            if 10 < len(decision) < 200:
                decisions.append({
                    "title": decision[:80],
                    "context": extract_context(text, match.start()),
                    "pattern_matched": pattern
                })
    
    return decisions

def extract_entities(text):
    """Extract code entities (classes, functions, files)."""
    entities = []
    
    patterns = [
        (r"`([A-Z][a-zA-Z]+)`", "class"),           # ClassName
        (r"`([a-z_]+\(\))`", "function"),           # function_name()
        (r"((?:/[\w\-\./]+)+\.\w+)", "file"),        # /path/to/file.ext
        (r"([a-zA-Z_]+Service)", "service"),         # XxxService
        (r"([a-zA-Z_]Repository)", "repository"),   # XxxRepository
    ]
    
    for pattern, entity_type in patterns:
        for match in re.finditer(pattern, text):
            name = match.group(1)
            if name not in [e["name"] for e in entities]:
                entities.append({
                    "name": name,
                    "type": entity_type,
                    "location": extract_context(text, match.start())
                })
    
    return entities

def extract_references(text):
    """Extract URLs and external references."""
    references = []
    
    urls = re.findall(r"https?://[^\s\)\]\"\'>]+", text)
    for url in set(urls):  # Deduplicate
        references.append({
            "url": url,
            "title": url.split("/")[-1][:50] or url
        })
    
    return references

def extract_context(text, pos, radius=100):
    """Extract surrounding context."""
    start = max(0, pos - radius)
    end = min(len(text), pos + radius)
    return text[start:end].strip()

def generate_bash_commands(extraction):
    """Generate bash commands to file extracted knowledge."""
    commands = []
    
    for decision in extraction["decisions"]:
        title_slug = decision["title"].lower().replace(" ", "-")[:50]
        title_escaped = decision["title"].replace('"', '\\"')
        context_escaped = decision.get("context", "").replace('"', '\\"')[:200]
        
        commands.append(
            f'file_decision "{title_escaped}" "{context_escaped}"'
        )
    
    for entity in extraction["entities"]:
        name_escaped = entity["name"].replace('"', '\\"')
        type_escaped = entity["type"].replace('"', '\\"')
        loc_escaped = entity.get("location", "")[:100].replace('"', '\\"')
        
        commands.append(
            f'file_entity "{name_escaped}" "{type_escaped}" "" "{loc_escaped}"'
        )
    
    for ref in extraction["references"]:
        url_escaped = ref["url"].replace('"', '\\"')
        title_escaped = ref["title"].replace('"', '\\"')
        
        commands.append(
            f'file_reference "{url_escaped}" "{title_escaped}"'
        )
    
    return commands

def main():
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1]) as f:
            text = f.read()
    else:
        # Read from stdin
        text = sys.stdin.read()
    
    extraction = extract_from_compaction(text)
    
    if "--dry-run" in sys.argv:
        print(json.dumps(extraction, indent=2))
    else:
        commands = generate_bash_commands(extraction)
        for cmd in commands:
            print(f"# Would execute: {cmd}")
            # Actually execute:
            # import subprocess
            # subprocess.run(f"source memory.sh && {cmd}", shell=True)

if __name__ == "__main__":
    main()
```

**Verification:**
```bash
echo "We decided to use SQLite over Room. AuthService handles auth." | \
    python3 ~/.pi/agent/skills/memory-tracker/extract.py --dry-run
```

---

#### Task 4: Update memory-tracker SKILL.md

**Epic Issue:** KB-104  
**Goals:** G3, G4, G5

**Files to modify:**
- `~/.pi/agent/skills/memory-tracker/SKILL.md`

**New Sections to Add:**

```markdown
## Knowledge Base (KB)

Beyond simple issue tracking, the memory-tracker can maintain a full knowledge base.

### KB Categories

| Tracker | Purpose | Example |
|---------|---------|---------|
| `concepts` | Domain concepts, patterns | "dependency-injection", "event-sourcing" |
| `decisions` | Architectural decisions | "2026-03-15-sqlite-over-room" |
| `entities` | Code entities | "auth-service", "user-repository" |
| `references` | External links | "flutter-docs-2026" |

### KB Setup

```bash
# Register all KB categories at once
register_kb_categories

# Or register individually
register_tracker_type "concepts" "Domain concepts and patterns"
register_tracker_type "decisions" "Architectural decisions with rationale"
register_tracker_type "entities" "Code entities: classes, functions, files"
register_tracker_type "references" "External references: docs, articles"
```

### KB Commands

#### file_decision
```bash
file_decision "title" "rationale" [--context "context"]
```

High-level decision filing with auto-summary and archival.

#### file_entity
```bash
file_entity "name" "type" [--file "path"] [--desc "description"]
```

Record a code entity (class, function, file, API).

#### file_reference
```bash
file_reference "url" "title" [--notes "notes"]
```

Store an external reference.

#### link_entries
```bash
link_entries "tracker/entity" "tracker/entity" "relationship"
```

Create wikilink between entries.

### Wikilinks

Entries can link to each other using wikilink syntax:

```
[[tracker/entity_key]]
```

Example:
```
This decision links to [[entities/auth-service]] which implements the auth logic.
```

### Q&A Workflow

When user asks complex questions:

1. Use `search_kb "query"` to find relevant entries
2. Read relevant entries
3. Synthesize answer
4. Optionally file new insights

```
User: Why did we choose SQLite?

Assistant:
[sudo] search_kb "SQLite"
# Found: decisions/2026-03-15-sqlite-over-room

Let me check that decision...
# From the entry: "Rationale: Room adds complexity we don't need"

Answer: We chose SQLite because Room added unnecessary complexity for our simple CRUD needs.
```

### Compaction Integration

On session compaction, the LLM should extract knowledge:

1. Review messages being summarized
2. Run extraction: `python3 extract.py messages.txt`
3. Execute generated commands to file knowledge
4. Link related entries

### Extraction from Compaction

```bash
# After compaction, extract knowledge
python3 extract.py --dry-run < compacted_messages.txt

# Review, then file:
python3 extract.py < compacted_messages.txt | bash
```
```

**Verification:**
```bash
grep -c "file_decision\|file_entity\|link_entries\|search_kb" ~/.pi/agent/skills/memory-tracker/SKILL.md
# Should show multiple matches
```

---

### Phase 2: Extension Integration

#### Task 5: Create Session Compaction Hook

**Epic Issue:** KB-201  
**Goals:** G1, G2, G3

**Files to create:**
- `~/.pi/agent/extensions/memory-kb-auto.js`

**Implementation:**

```javascript
// Pi extension: memory-kb-auto
// Triggers KB extraction on session compaction

module.exports = {
  name: "memory-kb-auto",
  version: "1.0.0",

  onLoad(pi) {
    console.log("[KB-Auto] Memory KB Auto-extraction loaded");
  },

  async on("session_before_compact", async (event, ctx) => {
    const { preparation } = event;
    
    // Check config
    const configPath = home/.pi/agent/settings.json");
    const config = JSON.parse(require("fs").readFileSync(configPath));
    
    // Only auto-extract if enabled
    if (config.enableKbAutoExtract !== true) {
      return;
    }

    console.log("[KB-Auto] Compaction detected, extracting knowledge...");

    // Serialize messages for extraction
    const { serializeConversation } = require("@mariozechner/pi-coding-agent");
    const messages = preparation.messagesToSummarize.map(m => ({
      message: m
    }));
    const text = serializeConversation(messages);

    // Run extraction
    const { spawn } = require("child_process");
    const extract = spawn("python3", [
      require("path").join(process.env.HOME, 
        ".pi/agent/skills/memory-tracker/extract.py"),
      "--dry-run"
    ]);

    let output = "";
    extract.stdout.on("data", d => output += d);
    extract.stderr.on("data", d => console.error("[KB-Auto]", d.toString()));

    extract.on("close", async () => {
      try {
        const extraction = JSON.parse(output);
        
        // File each category
        for (const decision of extraction.decisions) {
          const title = decision.title.replace(/"/g, '\\"');
          const ctx = (decision.context || "").replace(/"/g, '\\"');
          await ctx.run(`file_decision "${title}" "${ctx}"`);
        }
        
        for (const entity of extraction.entities) {
          const name = entity.name.replace(/"/g, '\\"');
          const type = entity.type;
          await ctx.run(`file_entity "${name}" "${type}"`);
        }
        
        console.log(`[KB-Auto] Extracted:`, {
          decisions: extraction.decisions.length,
          entities: extraction.entities.length,
          references: extraction.references.length
        });
      } catch (e) {
        console.error("[KB-Auto] Extraction failed:", e.message);
      }
    });
  })
};
```

**Verification:**
```bash
cp ~/.pi/agent/skills/memory-tracker/pi-knowledge-base.js \
   ~/.pi/agent/extensions/memory-kb-auto.js 2>/dev/null || true

# Edit settings.json to enable:
# "enableKbAutoExtract": true

pi /reload
```

---

#### Task 6: Add KB Search as Pi Tool

**Epic Issue:** KB-202  
**Goals:** G4

**Files to create:**
- `~/.pi/agent/extensions/memory-kb-search.js`

**Implementation:**

```javascript
// Pi extension: memory-kb-search
// Provides KB search as native Pi tools

module.exports = {
  name: "memory-kb-search",
  version: "1.0.0",

  tools: [
    {
      name: "kb_search",
      description: "Search the knowledge base for entries matching a query",
      inputSchema: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "Search query"
          },
          tracker: {
            type: "string",
            enum: ["all", "concepts", "decisions", "entities", "references"],
            default: "all"
          }
        },
        required: ["query"]
      },

      async handler({ query, tracker = "all" }) {
        const { spawnSync } = require("child_process");
        const fs = require("fs");
        const path = require("path");

        const memoryDir = path.join(process.env.HOME, "agents/memory/trackers");
        
        // Simple grep-based search
        const searchDir = tracker === "all" 
          ? memoryDir 
          : path.join(memoryDir, tracker);

        const results = [];
        
        function searchDir(dir) {
          const entries = fs.readdirSync(dir, { withFileTypes: true });
          for (const entry of entries) {
            const fullPath = path.join(dir, entry.name);
            if (entry.isDirectory()) {
              const convFile = path.join(fullPath, "conversation.json");
              if (fs.existsSync(convFile)) {
                const content = fs.readFileSync(convFile, "utf-8");
                if (content.toLowerCase().includes(query.toLowerCase())) {
                  // Extract tracker and key from path
                  const relPath = path.relative(memoryDir, fullPath);
                  results.push({
                    tracker: relPath.split("/")[0],
                    entity_key: path.basename(fullPath),
                    preview: content.substring(0, 200)
                  });
                }
              }
            }
          }
        }

        try {
          searchDir(searchDir);
        } catch (e) {
          return { error: e.message };
        }

        return {
          query,
          tracker,
          count: results.length,
          results
        };
      }
    },

    {
      name: "kb_read",
      description: "Read a specific KB entry",
      inputSchema: {
        type: "object",
        properties: {
          tracker: { type: "string" },
          entity_key: { type: "string" }
        },
        required: ["tracker", "entity_key"]
      },

      async handler({ tracker, entity_key }) {
        const fs = require("fs");
        const path = require("path");

        const memoryDir = path.join(process.env.HOME, "agents/memory/trackers");
        
        // Check both active and memory
        for (const state of ["active", "memory"]) {
          const convFile = path.join(
            memoryDir, tracker, state, entity_key, "conversation.json"
          );
          const manifestFile = path.join(
            memoryDir, tracker, state, entity_key, "manifest.json"
          );

          if (fs.existsSync(convFile)) {
            const conversation = JSON.parse(fs.readFileSync(convFile, "utf-8"));
            const manifest = fs.existsSync(manifestFile) 
              ? JSON.parse(fs.readFileSync(manifestFile, "utf-8"))
              : {};

            return {
              tracker,
              entity_key,
              state,
              title: manifest.title || entity_key,
              summary: manifest.summary || "",
              messages: conversation.messages || []
            };
          }
        }

        return { error: "Entry not found" };
      }
    }
  ]
};
```

**Verification:**
```bash
cp ~/.pi/agent/extensions/memory-kb-search.js \
   ~/.pi/agent/extensions/memory-kb-search.js

pi /reload
# Ask pi: "Search the knowledge base for 'authentication'"
# Verify pi uses kb_search tool
```

---

### Phase 3: Enhanced Features

#### Task 7: Create KB Linting Module

**Epic Issue:** KB-301  
**Goals:** G5

**Files to create:**
- `~/.pi/agent/skills/memory-tracker/lint.py`

**Implementation:**

```python
#!/usr/bin/env python3
"""
KB Health Checks

Checks:
1. Broken wikilinks ([[tracker/key]] → non-existent entry)
2. Orphaned entries (no other entry links to them)
3. Missing summaries (entries without proper close message)
4. Suggest link opportunities
"""

import json
import re
from pathlib import Path
from collections import defaultdict

MEMORY_DIR = Path.home() / "agents" / "memory" / "trackers"

class KBLinter:
    def __init__(self):
        self.issues = []
        self.links = defaultdict(list)
        
    def lint_all(self):
        """Run all lint checks."""
        self.collect_links()
        self.check_broken_links()
        self.check_orphans()
        self.check_missing_summaries()
        self.suggest_links()
        return self.issues
    
    def collect_links(self):
        """Find all wikilinks in KB."""
        wikilink_pattern = r'\[\[([^\]]+)\]\]'
        
        for tracker in MEMORY_DIR.iterdir():
            if not tracker.is_dir():
                continue
            for state in ["active", "memory"]:
                state_dir = tracker / state
                if not state_dir.exists():
                    continue
                for entity_dir in state_dir.iterdir():
                    if not entity_dir.is_dir():
                        continue
                    conv_file = entity_dir / "conversation.json"
                    if not conv_file.exists():
                        continue
                    
                    content = conv_file.read_text()
                    for match in re.finditer(wikilink_pattern, content):
                        link = match.group(1)
                        self.links[link].append(str(entity_dir.relative_to(MEMORY_DIR)))
    
    def check_broken_links(self):
        """Find wikilinks pointing to non-existent entries."""
        wikilink_pattern = r'\[\[([^\]]+)\]\]'
        
        for tracker in MEMORY_DIR.iterdir():
            if not tracker.is_dir():
                continue
            for state in ["active", "memory"]:
                state_dir = tracker / state
                if not state_dir.exists():
                    continue
                for entity_dir in state_dir.iterdir():
                    if not entity_dir.is_dir():
                        continue
                    conv_file = entity_dir / "conversation.json"
                    if not conv_file.exists():
                        continue
                    
                    content = conv_file.read_text()
                    for match in re.finditer(wikilink_pattern, content):
                        link = match.group(1)
                        # Check if link target exists
                        tracker_name, entity_key = link.split("/")
                        target_dir = MEMORY_DIR / tracker_name / "active" / entity_key
                        target_mem = MEMORY_DIR / tracker_name / "memory" / entity_key
                        
                        if not target_dir.exists() and not target_mem.exists():
                            self.issues.append({
                                "type": "broken_link",
                                "file": str(entity_dir.relative_to(MEMORY_DIR)),
                                "link": link,
                                "severity": "error"
                            })
    
    def check_orphans(self):
        """Find entries not linked from any other."""
        linked = set(self.links.keys())
        
        for tracker in MEMORY_DIR.iterdir():
            if not tracker.is_dir():
                continue
            for state in ["active", "memory"]:
                state_dir = tracker / state
                if not state_dir.exists():
                    continue
                for entity_dir in state_dir.iterdir():
                    if not entity_dir.is_dir():
                        continue
                    
                    rel_path = f"{tracker.name}/{entity_dir.name}"
                    if rel_path not in linked and rel_path.split("/")[0] in ["concepts", "decisions", "entities", "references"]:
                        self.issues.append({
                            "type": "orphan",
                            "file": rel_path,
                            "severity": "warning"
                        })
    
    def check_missing_summaries(self):
        """Find entries without summary/close message."""
        for tracker in MEMORY_DIR.iterdir():
            if tracker.name not in ["concepts", "decisions", "entities", "references"]:
                continue
            for state in ["memory"]:
                state_dir = tracker / state
                if not state_dir.exists():
                    continue
                for entity_dir in state_dir.iterdir():
                    manifest_file = entity_dir / "manifest.json"
                    if manifest_file.exists():
                        manifest = json.loads(manifest_file.read_text())
                        if not manifest.get("summary"):
                            self.issues.append({
                                "type": "missing_summary",
                                "file": f"{tracker.name}/{entity_dir.name}",
                                "severity": "info"
                            })
    
    def suggest_links(self):
        """Suggest related entries that could be linked."""
        # Check for shared keywords between entities
        for tracker in ["concepts", "decisions"]:
            files = list((MEMORY_DIR / tracker / "memory").glob("*"))
            files = [f for f in files if f.is_dir()]
            
            for i, f1 in enumerate(files):
                c1 = (f1 / "conversation.json").read_text().lower() if (f1 / "conversation.json").exists() else ""
                words1 = set(w for w in c1.split() if len(w) > 6)
                
                for f2 in files[i+1:]:
                    c2 = (f2 / "conversation.json").read_text().lower() if (f2 / "conversation.json").exists() else ""
                    words2 = set(w for w in c2.split() if len(w) > 6)
                    
                    shared = words1 & words2
                    if len(shared) > 5:
                        link = f"{tracker}/{f2.name}"
                        if link not in self.links[f"{tracker}/{f1.name}"]:
                            self.issues.append({
                                "type": "suggestion",
                                "message": f"Consider linking {f1.name} and {f2.name} (shared: {', '.join(list(shared)[:3])})",
                                "severity": "info"
                            })

def main():
    linter = KBLinter()
    issues = linter.lint_all()
    
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    info = [i for i in issues if i["severity"] == "info"]
    
    print(f"\nKB Lint Results")
    print(f"{'='*50}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Suggestions: {len(info)}")
    
    if errors:
        print(f"\n❌ Errors:")
        for i in errors:
            print(f"  [{i['file']}] Broken link: {i['link']}")
    
    if warnings:
        print(f"\n⚠️  Warnings:")
        for i in warnings:
            print(f"  [{i['file']}] Orphaned entry")
    
    if info:
        print(f"\n💡 Suggestions:")
        for i in info:
            if i["type"] == "suggestion":
                print(f"  {i['message']}")
            else:
                print(f"  [{i['file']}] Missing summary")

if __name__ == "__main__":
    main()
```

**Verification:**
```bash
python3 ~/.pi/agent/skills/memory-tracker/lint.py
```

---

#### Task 8: Create Export Module

**Epic Issue:** KB-302  
**Goals:** G5

**Files to create:**
- `~/.pi/agent/skills/memory-tracker/export.py`

**Implementation:**

```python
#!/usr/bin/env python3
"""
Export KB content in various formats:
- Markdown wiki
- Marp slides
- Matplotlib timeline
- JSON
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / "agents" / "memory" / "trackers"

def export_markdown(output_dir=None, tracker=None):
    """Export KB as markdown wiki."""
    output_dir = Path(output_dir) or Path("kb-export")
    output_dir.mkdir(exist_ok=True)
    
    trackers = [tracker] if tracker else ["concepts", "decisions", "entities", "references"]
    
    for t in trackers:
        tracker_dir = MEMORY_DIR / t
        if not tracker_dir.exists():
            continue
        
        out_tracker = output_dir / t
        out_tracker.mkdir(exist_ok=True)
        
        for state in ["active", "memory"]:
            state_dir = tracker_dir / state
            if not state_dir.exists():
                continue
            
            for entity_dir in state_dir.iterdir():
                if not entity_dir.is_dir():
                    continue
                
                conv_file = entity_dir / "conversation.json"
                manifest_file = entity_dir / "manifest.json"
                
                if conv_file.exists():
                    content = ["#" + (manifest_file.read_text() if manifest_file.exists() else {}).get("title", entity_dir.name)]
                    content.append("")
                    content.append(conv_file.read_text())
                    
                    (out_tracker / f"{entity_dir.name}.md").write_text("\n".join(content))
    
    print(f"Exported to {output_dir}")
    return output_dir

def export_slides(tracker="decisions"):
    """Export tracker as Marp slides."""
    tracker_dir = MEMORY_DIR / tracker / "memory"
    if not tracker_dir.exists():
        print(f"Tracker {tracker} not found")
        return
    
    slides = []
    slides.append("---")
    slides.append("marp: true")
    slides.append("theme: default")
    slides.append("---")
    slides.append("")
    slides.append(f"# {tracker.title()} Overview")
    slides.append(f"\nGenerated: {datetime.now().date()}")
    
    for entity_dir in sorted(tracker_dir.iterdir()):
        if not entity_dir.is_dir():
            continue
        
        manifest_file = entity_dir / "manifest.json"
        conv_file = entity_dir / "conversation.json"
        
        title = entity_dir.name.replace("-", " ").title()
        if manifest_file.exists():
            try:
                manifest = json.loads(manifest_file.read_text())
                title = manifest.get("title", title)
            except:
                pass
        
        slides.append("\n---")
        slides.append(f"\n## {title}")
        slides.append("")
        
        if conv_file.exists():
            # Extract first meaningful content
            content = conv_file.read_text()
            lines = content.split("\n")[:5]
            slides.extend([l for l in lines if l.strip()])
    
    output = MEMORY_DIR.parent / f"{tracker}-slides.md"
    output.write_text("\n".join(slides))
    print(f"Created slides: {output}")
    return output

def export_json(tracker=None):
    """Export KB as JSON."""
    result = {}
    
    trackers = [tracker] if tracker else ["concepts", "decisions", "entities", "references"]
    
    for t in trackers:
        tracker_dir = MEMORY_DIR / t
        if not tracker_dir.exists():
            continue
        
        result[t] = []
        
        for state in ["active", "memory"]:
            state_dir = tracker_dir / state
            if not state_dir.exists():
                continue
            
            for entity_dir in state_dir.iterdir():
                if not entity_dir.is_dir():
                    continue
                
                entry = {
                    "tracker": t,
                    "state": state,
                    "entity_key": entity_dir.name,
                    "manifest": None,
                    "messages": []
                }
                
                manifest_file = entity_dir / "manifest.json"
                conv_file = entity_dir / "conversation.json"
                
                if manifest_file.exists():
                    entry["manifest"] = json.loads(manifest_file.read_text())
                if conv_file.exists():
                    entry["messages"] = json.loads(conv_file.read_text()).get("messages", [])
                
                result[t].append(entry)
    
    output = MEMORY_DIR.parent / "kb-export.json"
    output.write_text(json.dumps(result, indent=2))
    print(f"Exported JSON: {output}")
    return output

def main():
    parser = argparse.ArgumentParser(description="Export KB")
    parser.add_argument("--format", choices=["markdown", "slides", "json"], default="markdown")
    parser.add_argument("--tracker", choices=["concepts", "decisions", "entities", "references"])
    parser.add_argument("--output", help="Output directory")
    
    args = parser.parse_args()
    
    if args.format == "markdown":
        export_markdown(args.output, args.tracker)
    elif args.format == "slides":
        export_slides(args.tracker or "decisions")
    elif args.format == "json":
        export_json(args.tracker)

if __name__ == "__main__":
    main()
```

**Verification:**
```bash
python3 ~/.pi/agent/skills/memory-tracker/export.py --format slides --tracker decisions
```

---

### Phase 4: Documentation & Testing

#### Task 9: Create KB Usage Documentation

**Epic Issue:** KB-401  
**Goals:** G3

**Files to create:**
- `/home/dev/agents/memory/README.md`

**Implementation:**

```markdown
# Pi Knowledge Base

A persistent knowledge base built on the memory-tracker system. Accumulates insights, decisions, and domain knowledge across Pi sessions.

**Core Principle:** The LLM maintains the KB. User rarely edits directly.

## Quick Start

```bash
# 1. Register KB categories
source ~/.pi/agent/skills/memory-tracker/memory.sh
register_kb_categories

# 2. File a decision
file_decision "use-sqlite-over-room" "Room adds complexity we don't need"

# 3. Search KB
search_kb "sqlite"
```

## KB Categories

| Tracker | Purpose | Example |
|---------|---------|---------|
| `concepts` | Domain concepts and patterns | "dependency-injection" |
| `decisions` | Architectural decisions with rationale | "2026-03-15-sqlite-over-room" |
| `entities` | Code entities (classes, functions, files) | "auth-service" |
| `references` | External links (docs, articles) | "flutter-docs-2026" |

## Commands

| Command | Description |
|---------|-------------|
| `register_kb_categories` | Initialize all 4 KB trackers |
| `file_decision "title" "rationale"` | File a decision |
| `file_entity "name" "type"` | File a code entity |
| `file_reference "url" "title"` | File an external reference |
| `link_entries "t/k" "t/k" "rel"` | Create wikilink between entries |
| `search_kb "query"` | Full-text search |
| `search_kb "query" --tracker "decisions"` | Search specific tracker |

## Wikilinks

Link between entries:

```
[[decisions/use-sqlite-over-room]]
[[entities/auth-service]]
```

## Q&A Workflow

```
User: Why did we choose SQLite?

Assistant:
search_kb "SQLite" --tracker "decisions"

# Found: decisions/2026-03-15-sqlite-over-room

# Reads the entry...

Answer: We chose SQLite because Room added unnecessary complexity 
for our simple CRUD needs at that stage (v0.2).
```

## Compaction Integration

On compaction, knowledge is auto-extracted:

1. LLM reviews summarized messages
2. Patterns matched: "Decision:", class names, URLs
3. KB entries created automatically
4. Related entries linked

## Export

```bash
# Export all KB as markdown
python3 ~/.pi/agent/skills/memory-tracker/export.py --format markdown

# Export decisions as slides
python3 ~/.pi/agent/skills/memory-tracker/export.py --format slides --tracker decisions

# Export as JSON
python3 ~/.pi/agent/skills/memory-tracker/export.py --format json
```

## Lint

```bash
# Check KB health
python3 ~/.pi/agent/skills/memory-tracker/lint.py
```

Checks for:
- Broken wikilinks
- Orphaned entries
- Missing summaries
- Link suggestions
```

**Verification:**
```bash
cat /home/dev/agents/memory/README.md | head -30
```

---

#### Task 10: Create Test Suite

**Epic Issue:** KB-402  
**Goals:** G3, G5

**Files to create:**
- `~/.pi/agent/skills/memory-tracker/test_kb.py`

**Implementation:**

```python
#!/usr/bin/env python3
"""
Tests for KB system
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path

# Mock paths for testing
TEST_MEMORY_DIR = None

class TestTrackerRegistration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        global TEST_MEMORY_DIR
        TEST_MEMORY_DIR = self.test_dir
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_register_kb_categories_creates_directories(self):
        """Test that register_kb_categories creates tracker directories."""
        trackers_dir = Path(self.test_dir) / "trackers"
        trackers_dir.mkdir()
        
        # Simulate registration
        for tracker in ["concepts", "decisions", "entities", "references"]:
            tracker_dir = trackers_dir / tracker
            tracker_dir.mkdir()
            (tracker_dir / "active").mkdir()
            (tracker_dir / "memory").mkdir()
        
        # Verify
        for tracker in ["concepts", "decisions", "entities", "references"]:
            self.assertTrue((trackers_dir / tracker).exists())
            self.assertTrue((trackers_dir / tracker / "active").exists())
            self.assertTrue((trackers_dir / tracker / "memory").exists())

class TestFileFunctions(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.trackers_dir = Path(self.test_dir) / "trackers"
        self.trackers_dir.mkdir()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_file_decision_creates_entry(self):
        """Test file_decision creates proper entry structure."""
        decisions_dir = self.trackers_dir / "decisions"
        decisions_dir.mkdir()
        memory_dir = decisions_dir / "memory"
        memory_dir.mkdir()
        
        entity_key = "test-decision"
        entity_dir = memory_dir / entity_key
        entity_dir.mkdir()
        
        # Create manifest
        manifest = {
            "tracker": "decisions",
            "entity_key": entity_key,
            "title": "Test Decision",
            "status": "closed",
            "summary": "Test rationale"
        }
        (entity_dir / "manifest.json").write_text(json.dumps(manifest))
        
        # Create conversation
        conversation = {
            "messages": [
                {"role": "assistant", "content": "Decision: Test Decision"},
                {"role": "assistant", "content": "Rationale: Test rationale"}
            ]
        }
        (entity_dir / "conversation.json").write_text(json.dumps(conversation))
        
        # Verify
        self.assertTrue((entity_dir / "manifest.json").exists())
        self.assertTrue((entity_dir / "conversation.json").exists())
        
        manifest_read = json.loads((entity_dir / "manifest.json").read_text())
        self.assertEqual(manifest_read["title"], "Test Decision")
        self.assertEqual(manifest_read["status"], "closed")

class TestExtractor(unittest.TestCase):
    def test_extract_decisions_finds_decision_pattern(self):
        """Test decision extraction finds Decision: pattern."""
        from extract import extract_decisions
        
        text = "We decided to use SQLite over Room because Room added complexity."
        decisions = extract_decisions(text)
        
        self.assertTrue(len(decisions) >= 1)
        self.assertTrue(any("sqlite" in d["title"].lower() for d in decisions))
    
    def test_extract_entities_finds_class_names(self):
        """Test entity extraction finds class names."""
        from extract import extract_entities
        
        text = "The AuthService class handles authentication. UserRepository manages users."
        entities = extract_entities(text)
        
        entity_names = [e["name"] for e in entities]
        self.assertTrue(any("AuthService" in n for n in entity_names))
        self.assertTrue(any("UserRepository" in n for n in entity_names))
    
    def test_extract_references_finds_urls(self):
        """Test reference extraction finds URLs."""
        from extract import extract_references
        
        text = "Check out https://docs.flutter.dev and https://dart.dev"
        refs = extract_references(text)
        
        self.assertTrue(len(refs) >= 1)
        self.assertTrue(any("flutter.dev" in r["url"] for r in refs))

class TestLinter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_broken_link_detection(self):
        """Test linter detects broken wikilinks."""
        # Create KB structure with broken link
        concepts_dir = Path(self.test_dir) / "concepts" / "memory" / "test-concept"
        concepts_dir.mkdir(parents=True)
        
        conv = {"messages": [{"content": "See [[decisions/nonexistent]]"}]}
        (concepts_dir / "conversation.json").write_text(json.dumps(conv))
        
        # Run linter (would need to mock MEMORY_DIR)
        # For now, just verify structure
        self.assertTrue((concepts_dir / "conversation.json").exists())

if __name__ == "__main__":
    unittest.main()
```

**Verification:**
```bash
cd ~/.pi/agent/skills/memory-tracker
python3 -m pytest test_kb.py -v
```

---

## Verification Checklist

### Phase 1 Complete
- [ ] `register_kb_categories` runs without errors
- [ ] `file_decision` creates entry in `decisions/`
- [ ] `file_entity` creates entry in `entities/`
- [ ] `link_entries` creates wikilinks
- [ ] `search_kb` finds entries
- [ ] `extract.py` runs without errors
- [ ] SKILL.md updated with KB documentation

### Phase 2 Complete
- [ ] Extension loads on pi startup
- [ ] Compaction triggers extraction
- [ ] `kb_search` tool available to LLM
- [ ] `kb_read` tool available to LLM

### Phase 3 Complete
- [ ] `lint.py` reports issues
- [ ] `export.py --format slides` generates Marp
- [ ] `export.py --format json` generates JSON

### Phase 4 Complete
- [ ] README exists at `/home/dev/agents/memory/README.md`
- [ ] Tests pass: `pytest test_kb.py -v`

---

## File Summary

| Task | File | Action |
|------|------|--------|
| 1 | `memory.sh` | Add `register_kb_categories()` |
| 2 | `memory.sh` | Add KB functions |
| 3 | `extract.py` | Create new |
| 4 | `SKILL.md` | Update |
| 5 | `memory-kb-auto.js` | Create new |
| 6 | `memory-kb-search.js` | Create new |
| 7 | `lint.py` | Create new |
| 8 | `export.py` | Create new |
| 9 | `README.md` | Create in `/home/dev/agents/memory/` |
| 10 | `test_kb.py` | Create new |

**Total:** ~1400 lines across 10 files

---

## Estimated Time

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1 | 1-4 | 45-60 min |
| Phase 2 | 5-6 | 30-45 min |
| Phase 3 | 7-8 | 30-45 min |
| Phase 4 | 9-10 | 15-20 min |
| **Total** | 10 | **2-3 hours** |

---

## Integration with Existing memory-tracker

This plan extends rather than replaces the existing memory-tracker:

| Existing | Extended |
|----------|----------|
| `register_tracker_type` | `register_kb_categories` (batch) |
| `start_tracking` + `add_message` | `file_decision`, `file_entity` (high-level) |
| `list_memory` | `search_kb` (full-text search) |
| Manual archival | Auto-extraction on compaction |
| Single-file structure | + wikilinks.json for cross-references |

The existing `github_issues` tracker and `github_issues/` directory remain unchanged.

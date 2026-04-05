# Epic: Pi Knowledge Base System (Memory-Tracker Integration)

**Epic ID:** KB-001  
**Status:** Backlog  
**Plan:** `/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md`  
**Design:** `/home/dev/docs/plans/2026-04-04-pi-knowledge-base-design.md`

---

## Epic Overview

Extend the existing memory-tracker system at `/home/dev/agents/memory/` to create a full-featured knowledge base that accumulates insights, decisions, and domain knowledge across Pi sessions. The LLM should compile, maintain, and query the knowledge base—not the user.

**Existing Infrastructure:**
```
/home/dev/agents/memory/
├── trackers/
│   ├── github_issues/     ← Already exists
│   └── ...                ← Other tracker types
└── github_issues/          ← GitHub integration
```

**Proposed Extension:**
```
/home/dev/agents/memory/trackers/
├── github_issues/          ← Existing
├── concepts/               ← NEW: Domain concepts
├── decisions/              ← NEW: Decision log
├── entities/               ← NEW: Code entities
└── references/             ← NEW: External references
```

**User Story:**  
*As a developer using Pi for long-term research and complex projects, I want my insights, decisions, and domain knowledge to persist across sessions, so I can query past work and build on accumulated understanding rather than starting fresh each time.*

**Goals:**

| ID | Goal | Source |
|----|------|--------|
| G1 | Persistent decision memory across sessions | Design §Problem |
| G2 | Accumulated entity tracking (classes, APIs, files) | Design §Problem |
| G3 | LLM-authored KB maintenance (user doesn't edit) | Design §Principles |
| G4 | Complex Q&A against accumulated knowledge | Design §Features |
| G5 | Self-improving KB through linting/compilation | Design §Features |

---

## Integration with Existing memory-tracker

### Existing Functions (to reuse)

| Function | Purpose | New KB Usage |
|----------|---------|--------------|
| `register_tracker_type` | Create new category | `register_tracker_type "concepts"`, `register_tracker_type "decisions"` |
| `start_tracking` | Create new entry | `start_tracking "decisions" "2026-03-15-sqlite"` |
| `add_message` | Add content | `add_message "decisions" "2026-03-15-sqlite" "assistant" "We chose SQLite because..."` |
| `close_conversation` | Archive with summary | Auto-summarize on close |
| `list_active` | List open entries | `list_active "decisions"` |
| `list_memory` | List archived | `list_memory "decisions"` |

### New Functions (to implement)

| Function | Purpose |
|----------|---------|
| `register_kb_categories` | Initialize concepts, decisions, entities, references trackers |
| `file_decision` | High-level decision filing |
| `link_entries` | Create wikilinks between entries |
| `kb_search` | Full-text + semantic search |
| `kb_query` | Complex Q&A against KB |
| `kb_lint` | Health checks |
| `kb_compile` | Compile raw → refined |
| `kb_export` | Export to various formats |

### Existing Storage Format (reused)

```
/home/dev/agents/memory/trackers/{tracker_type}/
├── active/{entity_key}/
│   ├── manifest.json
│   └── conversation.json
└── memory/{entity_key}/
    ├── manifest.json
    └── conversation.json
```

**New KB Extensions:**
- `wikilinks.json` - Links between entries
- `index.json` - Fast lookup by tag/category

---

## Issues

### Phase 1: Core Infrastructure

---

#### Issue KB-101: Register KB Tracker Categories

**Labels:** `phase-1`, `infrastructure`  
**Estimate:** 5 min  
**Plan Task:** Task 1  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-1-register-kb-tracker-categories`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-1-register-kb-tracker-categories)

**Goals Addressed:** G3, G5

**Description:**  
Register the four new tracker types: concepts, decisions, entities, references.

**Acceptance Criteria:**
- [ ] `concepts` tracker registered
- [ ] `decisions` tracker registered
- [ ] `entities` tracker registered
- [ ] `references` tracker registered
- [ ] Each has description and proper configuration

**Verification:**
```bash
# List tracker types should show: concepts, decisions, entities, references
list_tracker_types
```

**Dependencies:** None (uses existing memory-tracker)

---

#### Issue KB-102: Extend memory-tracker with KB Functions

**Labels:** `phase-1`, `core`, `bash`  
**Estimate:** 30 min  
**Plan Task:** Task 2  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-2-extend-memory-tracker-with-kb-functions`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-2-extend-memory-tracker-with-kb-functions)

**Goals Addressed:** G3, G4, G5

**Description:**  
Add new functions to the memory-tracker skill for KB-specific operations.

**Functions to Add:**

| Function | Purpose |
|----------|---------|
| `register_kb_categories()` | Initialize all 4 KB tracker types |
| `file_decision()` | High-level decision filing with auto-summary |
| `file_entity()` | Record code entity with type inference |
| `file_reference()` | Store external URL with metadata |
| `link_entries()` | Create wikilink between entries |
| `search_kb()` | Full-text search across KB |
| `query_kb()` | Semantic Q&A against KB |

**File to Modify:** `~/.pi/agent/skills/memory-tracker/SKILL.md`

**Acceptance Criteria:**
- [ ] `register_kb_categories` runs without errors
- [ ] `file_decision "SQLite over Room" "Rationale..."` creates proper entry
- [ ] `file_entity "AuthService" "class"` creates entity entry
- [ ] `link_entries "decisions/123" "concepts/auth"` creates link
- [ ] `search_kb "authentication"` returns relevant entries

**Verification:**
```bash
register_kb_categories
file_decision "test-decision" "We chose option A"
search_kb "test"
```

**Dependencies:** KB-101

---

#### Issue KB-103: Create Knowledge Extraction Module

**Labels:** `phase-1`, `extraction`, `python`  
**Estimate:** 25 min  
**Plan Task:** Task 3  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-3-create-knowledge-extraction-module`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-3-create-knowledge-extraction-module)

**Goals Addressed:** G1, G2, G3

**Description:**  
Build extraction module that analyzes session compaction events and files knowledge into KB.

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `extract_from_compaction()` | Main entry point |
| `extract_decisions()` | Pattern-match decision statements |
| `extract_entities()` | Extract class/function/file names |
| `extract_references()` | Extract URLs |
| `serialize_messages()` | Convert session to text |

**Pattern Detection:**

```python
# Decision patterns
r"(?:Decision|Cho[so]e|Went with)[:\s]+(.+?)(?:\.|$)"
r"(?:Implement|Use|Adopt)[:\s]+(.+?)(?:\.|$)"

# Entity patterns
r"`([A-Z][a-zA-Z]+)`"           # ClassName
r"`([a-z_]+\(\))`"              # function_name()
r"((?:/[\w\-\./]+)+\.\w+)"      # /path/to/file.ext
```

**File Location:** `~/.pi/agent/skills/memory-tracker/extract.py`

**Acceptance Criteria:**
- [ ] `extract.py` runs without errors
- [ ] `extract_decisions()` finds "Decision:" patterns
- [ ] `extract_entities()` finds class names and file paths
- [ ] Output compatible with `file_decision()`, `file_entity()`

**Verification:**
```bash
echo "We decided to use SQLite." | python3 ~/.pi/agent/skills/memory-tracker/extract.py
```

**Dependencies:** KB-102

---

#### Issue KB-104: Update memory-tracker SKILL.md

**Labels:** `phase-1`, `skill`, `documentation`  
**Estimate:** 20 min  
**Plan Task:** Task 4  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-4-update-memory-tracker-skillmd`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-4-update-memory-tracker-skillmd)

**Goals Addressed:** G3, G4, G5

**Description:**  
Update the memory-tracker SKILL.md to document all new KB functions.

**New Sections to Add:**

1. KB Overview (how KB differs from basic tracking)
2. KB Categories (concepts, decisions, entities, references)
3. KB Commands (file_decision, file_entity, link_entries, search_kb, query_kb)
4. Wikilink Format (`[[tracker/entity_key]]`)
5. Q&A Workflow
6. Compaction Integration

**File Location:** `~/.pi/agent/skills/memory-tracker/SKILL.md`

**Acceptance Criteria:**
- [ ] All new KB functions documented
- [ ] Wikilink syntax explained
- [ ] Q&A workflow example included
- [ ] `/skill:memory-tracker` loads with KB functions

**Verification:**
```bash
pi /reload
# Check skill loaded
```

**Dependencies:** KB-102, KB-103

---

### Phase 2: Extension Integration

---

#### Issue KB-201: Create Session Compaction Hook

**Labels:** `phase-2`, `extension`, `javascript`  
**Estimate:** 25 min  
**Plan Task:** Task 5  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-5-create-session-compaction-hook`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-5-create-session-compaction-hook)

**Goals Addressed:** G1, G2, G3

**Description:**  
Create Pi extension that intercepts compaction events and triggers KB extraction.

**Hook to Implement:** `session_before_compact`

**Behavior:**
1. Check if `config.auto_extract` is enabled
2. Call `extract_from_compaction()` with messages
3. File extracted decisions, entities, references
4. Update `config.last_extracted`

**File Location:** `~/.pi/agent/extensions/memory-kb-auto.js`

**Acceptance Criteria:**
- [ ] Extension loads on pi startup
- [ ] Compaction triggers extraction automatically
- [ ] Extracted entries appear in KB
- [ ] No errors in pi console
- [ ] Can be disabled via config

**Verification:**
```bash
pi /reload
# Trigger compaction
# Check KB for new entries
```

**Dependencies:** KB-103, KB-104

---

#### Issue KB-202: Add KB Search as Pi Tool

**Labels:** `phase-2`, `extension`, `javascript`, `tool`  
**Estimate:** 20 min  
**Plan Task:** Task 6  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-6-add-kb-search-as-pi-tool`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-6-add-kb-search-as-pi-tool)

**Goals Addressed:** G4

**Description:**  
Add KB search functionality as a native Pi tool for the LLM.

**Tools to Implement:**

| Tool | Input | Output |
|------|-------|--------|
| `kb_search` | `{query: string, section?: string}` | `{query, count, results: [{tracker, entity_key, preview}]}` |
| `kb_read` | `{tracker: string, entity_key: string}` | `{title, content, links, summary}` |
| `kb_query` | `{question: string}` | `{answer, sources: [{tracker, entity_key}]}` |

**File Location:** `~/.pi/agent/extensions/memory-kb-search.js`

**Acceptance Criteria:**
- [ ] `kb_search` tool available to LLM
- [ ] `kb_read` tool available to LLM
- [ ] `kb_query` tool available to LLM
- [ ] Search returns relevant results
- [ ] Query synthesizes answer from KB

**Verification:**
```bash
pi /reload
# Ask pi: "Search the knowledge base for 'authentication'"
# Verify pi uses kb_search tool
```

**Dependencies:** KB-102

---

### Phase 3: Enhanced Features

---

#### Issue KB-301: Create KB Linting Module

**Labels:** `phase-3`, `linting`, `python`  
**Estimate:** 25 min  
**Plan Task:** Task 7  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-7-create-kb-linting-module`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-7-create-kb-linting-module)

**Goals Addressed:** G5

**Description:**  
Build health checks for KB integrity using existing memory-tracker structure.

**Checks to Implement:**

| Check | Type | Severity | Description |
|-------|------|----------|-------------|
| `check_broken_links()` | Link | Error | `[[wikilink]]` → non-existent entry |
| `check_orphans()` | Structure | Warning | Entry not linked from any other |
| `check_missing_summaries()` | Content | Info | Entry without summary |
| `suggest_links()` | Suggestion | Info | Related entries not linked |

**File Location:** `~/.pi/agent/skills/memory-tracker/lint.py`

**Acceptance Criteria:**
- [ ] `lint.py` runs without errors
- [ ] Detects broken wikilinks
- [ ] Detects orphaned entries
- [ ] Reports missing summaries
- [ ] Suggests link opportunities
- [ ] Clean exit code when healthy

**Verification:**
```bash
# Create test broken link
python3 ~/.pi/agent/skills/memory-tracker/lint.py
```

**Dependencies:** KB-102

---

#### Issue KB-302: Create Export Module

**Labels:** `phase-3`, `export`, `python`  
**Estimate:** 20 min  
**Plan Task:** Task 8  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-8-create-export-module`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-8-create-export-module)

**Goals Addressed:** G5

**Description:**  
Build export functionality for multiple output formats.

**Export Formats:**

| Format | Function | Description |
|--------|----------|-------------|
| Markdown Wiki | `export_markdown()` | Full KB dump with wikilinks |
| Marp Slides | `export_slides()` | Presentation format |
| Timeline | `export_timeline()` | matplotlib decision timeline |
| JSON | `export_json()` | Structured data |

**File Location:** `~/.pi/agent/skills/memory-tracker/export.py`

**Acceptance Criteria:**
- [ ] `export_markdown()` creates wikilink-compatible markdown
- [ ] `export_slides()` creates valid Marp markdown
- [ ] `export_timeline()` creates PNG (if matplotlib installed)
- [ ] `export_json()` creates structured JSON

**Verification:**
```bash
python3 ~/.pi/agent/skills/memory-tracker/export.py --format slides --tracker decisions
```

**Dependencies:** KB-102

---

### Phase 4: Documentation & Testing

---

#### Issue KB-401: Create KB Usage Documentation

**Labels:** `phase-4`, `documentation`  
**Estimate:** 15 min  
**Plan Task:** Task 9  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-9-create-kb-usage-documentation`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-9-create-kb-usage-documentation)

**Goals Addressed:** G3

**Description:**  
Create user-facing README for the KB system in the memory directory.

**File Location:** `/home/dev/agents/memory/README.md`

**Sections:**

1. Quick Start (3 commands to get going)
2. KB Categories (concepts, decisions, entities, references)
3. Commands Reference (table of all functions)
4. Wikilink Syntax (`[[tracker/entity_key]]`)
5. Q&A Workflow
6. Compaction Integration
7. Workflows (New Project, During Work, On Compaction)

**Acceptance Criteria:**
- [ ] README exists at `/home/dev/agents/memory/README.md`
- [ ] Quick start works in < 5 min
- [ ] All commands documented
- [ ] Workflow examples included

**Verification:**
```bash
cat /home/dev/agents/memory/README.md | head -50
```

**Dependencies:** KB-102

---

#### Issue KB-402: Create Test Suite

**Labels:** `phase-4`, `testing`, `python`  
**Estimate:** 20 min  
**Plan Task:** Task 10  
**Plan Ref:** [`/home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-10-create-test-suite`](file:///home/dev/docs/plans/2026-04-04-pi-knowledge-base-implementation.md#task-10-create-test-suite)

**Goals Addressed:** G3, G5

**Description:**  
Create comprehensive tests for KB system.

**Test Classes:**

| Class | Tests |
|-------|-------|
| `TestTrackerRegistration` | `test_register_concepts`, `test_register_decisions` |
| `TestFileFunctions` | `test_file_decision`, `test_file_entity`, `test_link_entries` |
| `TestExtractor` | `test_extract_decisions`, `test_extract_entities` |
| `TestLinter` | `test_broken_link_detection` |

**File Location:** `~/.pi/agent/skills/memory-tracker/test_kb.py`

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] `pytest test_kb.py -v` runs
- [ ] Test isolation (temp directories)
- [ ] Coverage of core functions

**Verification:**
```bash
cd ~/.pi/agent/skills/memory-tracker
python3 -m pytest test_kb.py -v
```

**Dependencies:** KB-102, KB-103, KB-301

---

## Issue Summary

| Issue | Title | Phase | Estimate | Dependencies |
|-------|-------|-------|----------|--------------|
| KB-101 | Register KB Tracker Categories | 1 | 5 min | - |
| KB-102 | Extend memory-tracker with KB Functions | 1 | 30 min | KB-101 |
| KB-103 | Create Knowledge Extraction Module | 1 | 25 min | KB-102 |
| KB-104 | Update memory-tracker SKILL.md | 1 | 20 min | KB-102, KB-103 |
| KB-201 | Create Session Compaction Hook | 2 | 25 min | KB-103, KB-104 |
| KB-202 | Add KB Search as Pi Tool | 2 | 20 min | KB-102 |
| KB-301 | Create KB Linting Module | 3 | 25 min | KB-102 |
| KB-302 | Create Export Module | 3 | 20 min | KB-102 |
| KB-401 | Create KB Usage Documentation | 4 | 15 min | KB-102 |
| KB-402 | Create Test Suite | 4 | 20 min | KB-102, KB-103, KB-301 |

**Total:** 10 issues, ~3 hours estimated

---

## Milestones

| Milestone | Issues | Goal |
|-----------|--------|------|
| M1: Core | KB-101, KB-102, KB-103, KB-104 | KB functional within memory-tracker |
| M2: Integration | KB-201, KB-202 | LLM-native KB usage |
| M3: Polish | KB-301, KB-302, KB-401, KB-402 | Production-ready |

---

## Definition of Done

Epic KB-001 is complete when:

- [ ] All 10 issues closed
- [ ] `register_kb_categories` works on fresh setup
- [ ] Compaction automatically files decisions
- [ ] `kb_search`, `kb_read`, `kb_query` tools available to LLM
- [ ] `lint.py` runs clean on new KB
- [ ] `export.py --format slides` generates valid Marp
- [ ] All tests pass
- [ ] README accurate and complete

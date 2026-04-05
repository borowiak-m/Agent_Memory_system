# Design: Pi Knowledge Base System (Memory-Tracker Integration)

## Problem Statement

Pi currently treats sessions as **episodic**—each session is independent, with memory only preserved through compaction summaries. This works for short-term coding but fails for:

1. **Research tracking**: User studies papers across sessions, can't query past findings
2. **Decision memory**: Decisions made in session #3 are forgotten by session #10
3. **Entity tracking**: Class names, API patterns, architectural choices aren't accumulated
4. **Knowledge compounding**: Each session starts fresh, doesn't build on past work

The user-provided approach shows a better model: **LLM-driven knowledge accumulation** where the agent compiles, maintains, and queries a structured knowledge base.

---

## Solution: Extend memory-tracker

Rather than creating a parallel system, we extend the existing **memory-tracker skill** at `~/.pi/agent/skills/memory-tracker/`.

**Existing infrastructure:**
```
/home/dev/agents/memory/
├── trackers/
│   ├── github_issues/     ← Already exists, works
│   └── ...                ← Other tracker types
└── github_issues/          ← GitHub integration
```

**Proposed extension:**
```
/home/dev/agents/memory/trackers/
├── github_issues/          ← Unchanged
├── concepts/               ← NEW: Domain concepts
├── decisions/              ← NEW: Decision log
├── entities/               ← NEW: Code entities
└── references/             ← NEW: External references
```

**Key insight:** The memory-tracker already has:
- Tracker registration system
- Entity lifecycle (start → track → close → memory)
- JSON storage structure
- Bash functions for scripting

We add KB-specific features on top.

---

## Core Concept

Transform Pi from an **episodic session manager** into a **persistent knowledge partner** using existing infrastructure:

```
Sessions (episodes)
    ↓ compaction
Knowledge Extraction (LLM + extract.py)
    ↓
memory-tracker storage (extended)
    ↓ (wikilinks.json + search)
Q&A / Linting / Compilation (LLM + tools)
    ↓
Enhanced KB (self-improving)
```

**The key insight from the user approach:** The LLM maintains the KB. We integrate this with the existing session management system.

---

## Design Principles

1. **LLM-authored**: The agent creates and updates KB entries, user rarely touches files directly
2. **Incremental**: Knowledge accumulates naturally through compaction extraction
3. **Wiki-native**: Standard Markdown with `[[wikilinks]]` for cross-referencing
4. **Queryable**: Complex Q&A against accumulated knowledge via `kb_search`, `kb_query`
5. **Self-improving**: Periodic linting and compilation enhance KB quality
6. **Minimal overhead**: KB maintenance shouldn't dominate token usage
7. **Leverage existing**: Extend memory-tracker, don't replace it

---

## User Interactions

### Current (Episodic)
```
Session 1: User asks about auth → LLM implements auth
Session 2: User asks about caching → LLM implements caching, forgets auth rationale
Session 3: User asks "why did we choose JWT?" → LLM has no idea
```

### With KB (Accumulated via memory-tracker)
```
Session 1: User asks about auth → LLM implements auth
           Compaction triggers: file_decision "use-jwt" "reason..."
           → Creates /home/dev/agents/memory/trackers/decisions/memory/use-jwt/
           
Session 2: User asks about caching → LLM implements caching
           Compaction: file_decision "use-redis" ...
           
Session 3: User asks "why JWT?"
           LLM: search_kb "JWT" → finds decisions/use-jwt
           Answer: "Decision made on 2026-03-15: Use JWT because..."
```

---

## Data Model

### Knowledge Categories (New Trackers)

| Category | Tracker | Content | Example |
|----------|---------|---------|---------|
| **Concepts** | `concepts` | Domain knowledge, patterns, architecture | "dependency-injection", "event-sourcing" |
| **Decisions** | `decisions` | Architectural choices with rationale | "2026-03-15-sqlite-over-room" |
| **Entities** | `entities` | Code artifacts (classes, functions, files) | "AuthService", "UserRepository" |
| **References** | `references` | External links (docs, articles, papers) | "firebase-auth-docs" |

### Entry Schema (via existing memory-tracker)

```
/home/dev/agents/memory/trackers/{tracker}/
├── active/{entity_key}/
│   ├── manifest.json      # Metadata
│   └── conversation.json  # Messages
└── memory/{entity_key}/   # Archived (closed)
    ├── manifest.json
    ├── conversation.json
    └── logs/
```

**manifest.json:**
```json
{
  "tracker": "decisions",
  "entity_key": "2026-03-15-sqlite-over-room",
  "title": "Use SQLite over Room",
  "created": "2026-03-15T10:00:00Z",
  "closed": "2026-03-15T10:30:00Z",
  "summary": "Chose SQLite because Room added unnecessary complexity",
  "tags": ["database", "mobile", "v0.2"]
}
```

**wikilinks.json (NEW):**
```json
{
  "links": [
    {
      "from": "decisions/2026-03-15-sqlite-over-room",
      "to": "entities/auth-service",
      "relationship": "uses"
    }
  ]
}
```

---

## Key Features

### 1. Knowledge Extraction (on Compaction)

When context is compacted, LLM reviews summarized messages and:
- Identifies new decisions → `file_decision "title" "rationale"`
- Tracks new entities → `file_entity "ClassName" "class"`
- Notes references → `file_reference "url" "title"`
- Creates links → `link_entries "decisions/123" "entities/456" "implements"`

### 2. Q&A Against KB

User asks: "What's our approach to error handling?"

LLM:
1. Uses `kb_search` tool to search for "error handling", "exception"
2. Uses `kb_read` to read relevant entries
3. Synthesizes answer from KB + current context
4. Optionally files new insights

### 3. Wikilinks

Cross-reference entries:

```
In decisions/2026-03-15-sqlite:
"This decision relates to [[entities/auth-service]] which stores user data."
```

### 4. Health Checks (Linting)

Periodic checks via `lint.py`:
- Broken wikilinks (`[[tracker/key]]` → non-existent)
- Orphaned entries (no links to them)
- Inconsistent terminology
- Missing summaries
- Link suggestions

### 5. Export Formats

Via `export.py`:
- **Markdown wiki** - Full KB dump with wikilinks
- **Marp slides** - Presentation format for decisions
- **JSON** - Structured data for programmatic access
- **matplotlib charts** - Decision timelines (optional)

---

## Technical Architecture

### File Structure

```
~/.pi/agent/skills/memory-tracker/
├── SKILL.md              # Updated with KB documentation
├── memory.sh             # Core functions (extended)
│   ├── register_tracker_type()
│   ├── start_tracking()
│   ├── add_message()
│   ├── close_conversation()
│   ├── list_active()
│   ├── list_memory()
│   └── NEW:
│       ├── register_kb_categories()
│       ├── file_decision()
│       ├── file_entity()
│       ├── file_reference()
│       ├── link_entries()
│       ├── search_kb()
│       └── query_kb()
├── extract.py            # NEW: Session → KB extraction
├── lint.py               # NEW: Health checks
├── export.py             # NEW: Format conversion
├── test_kb.py            # NEW: Tests
└── wikilinks.json        # NEW: Link tracking

/home/dev/agents/memory/trackers/
├── github_issues/        # Unchanged
├── concepts/             # NEW tracker
├── decisions/            # NEW tracker
├── entities/             # NEW tracker
└── references/           # NEW tracker

~/.pi/agent/extensions/
├── memory-kb-auto.js      # NEW: Compaction hook
└── memory-kb-search.js    # NEW: KB tools for LLM
```

### Extension Points

1. **`session_before_compact`** hook (via memory-kb-auto.js)
2. **Custom tools**: `kb_search`, `kb_read`, `kb_query` (via memory-kb-search.js)
3. **Skill commands**: All memory-tracker commands + new KB functions

---

## Comparison with Described System

| Feature | Described System | Pi KB (Memory-Tracker) |
|---------|------------------|------------------------|
| Raw data ingest | Obsidian Web Clipper → raw/ | Future: `raw/` tracker |
| Wiki compilation | LLM compiles raw → wiki | LLM extracts session → KB |
| IDE frontend | Obsidian | Terminal (future viewer possible) |
| Q&A | LLM queries wiki | LLM queries KB via `kb_search` |
| Output formats | Markdown, Marp, matplotlib | Same via `export.py` |
| Linting | LLM health checks | `lint.py` checks |
| Search engine | Custom CLI | `search_kb` function |
| Self-improvement | Queries enhance wiki | KB + linting |

### Key Differences from User Approach

1. **Focus**: User's system is document-centric (articles → wiki). Our system is session-centric (sessions → decisions).

2. **Ingestion**: User ingests external documents. We extract from LLM conversations.

3. **Storage**: User uses Obsidian (markdown files). We use memory-tracker (JSON + conversation files).

4. **Philosophy same**: LLM maintains the structure. User rarely edits directly.

---

## Comparison: Separate KB vs. Extended memory-tracker

| Aspect | Separate KB System | Extended memory-tracker |
|--------|-------------------|------------------------|
| Storage | `~/.pi/agent/knowledge/` | `/home/dev/agents/memory/trackers/` |
| Code | New skill + scripts | Extend existing skill |
| Learning curve | New commands | Familiar commands + new |
| Integration | Needs custom hooks | Uses existing hooks |
| GitHub issues | Separate | Same system |

**Advantage of integration:** Single system for issue tracking AND knowledge management.

---

## Implementation Phases

### Phase 1: Core Infrastructure
- Register KB tracker types (concepts, decisions, entities, references)
- Extend memory.sh with KB functions
- Create extraction module
- Update SKILL.md documentation

### Phase 2: Deep Integration
- Pi extension for compaction hooks
- KB search as LLM tool

### Phase 3: Enhanced Features
- Advanced linting
- Multiple output formats

### Phase 4: Polish
- Documentation
- Tests

---

## Open Questions

1. **When to extract?** Only on compaction, or on significant user events too?
   - **Decision:** Compaction only initially, configurable

2. **How much context to include?** Link-only vs. full content?
   - **Decision:** Full content in conversation.json, summary in manifest

3. **Should user see KB entries?** Hidden by default, queryable?
   - **Decision:** User can view via file system, LLM presents via Q&A

4. **Token budget?** KB adds to context—need smart loading
   - **Decision:** LLM decides what to load based on query

5. **Wikilinks location?** Store in each entry or centralized?
   - **Decision:** Both—`conversation.json` has inline `[[links]]`, `wikilinks.json` has structured graph

---

## Success Metrics

1. User can ask "Why did we choose X in session #3?" and get answer
2. KB entries link to each other (no orphans after lint)
3. Compaction triggers extraction without user prompting
4. `lint.py` runs clean after weekly maintenance
5. User never manually edits KB files (LLM maintains)

---

## Appendix: Reference Implementation Notes

From the described system:

> "I thought I had to reach for fancy RAG, but the LLM has been pretty good about auto-maintaining index files and brief summaries of all the documents and it reads all the important related data fairly easily at this ~small scale."

**Key takeaway:** Don't over-engineer. Simple indexing + summaries + full-text search is sufficient. The LLM handles the rest.

Our KB follows same principle:
- Simple JSON structure (via memory-tracker)
- Full-text search (via grep/shell)
- LLM does heavy lifting (extraction, Q&A, linking)
- Linting ensures quality

---

## Future Enhancements (Out of Scope)

- [ ] Semantic search (embeddings)
- [ ] Multi-user/shared KB
- [ ] Sync across machines
- [ ] Fine-tuning dataset generation
- [ ] Obsidian plugin compatibility (export matches Obsidian format)
- [ ] `raw/` tracker for document ingestion

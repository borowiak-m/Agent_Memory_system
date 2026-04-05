# Agent Memory System

A knowledge base system for [Pi coding agent](https://pi.dev) that extends the memory-tracker to accumulate insights, decisions, and domain knowledge across sessions.

## Overview

Built on the existing [memory-tracker](skills/memory-tracker/) skill, this system transforms Pi from an episodic session manager into a persistent knowledge partner. The LLM maintains the knowledge base — the user rarely edits directly.

## Quick Start

```bash
# Clone into your pi skills directory
git clone https://github.com/borowiak-m/Agent_Memory_system.git ~/.pi/agent/skills/agent-memory-system

# Or copy individual components
cp -r skills/memory-tracker/ ~/.pi/agent/skills/
```

## Components

### skills/memory-tracker/

The core memory-tracker with KB extensions. See [docs/plans/](docs/plans/) for design and implementation details.

**KB Categories (new trackers):**

| Tracker | Purpose |
|---------|---------|
| `concepts` | Domain concepts, patterns, architecture |
| `decisions` | Architectural decisions with rationale |
| `entities` | Code entities (classes, functions, files) |
| `references` | External links (docs, articles) |

**New KB Functions:**

```bash
source ~/.pi/agent/skills/memory-tracker/tracker.sh

# Register KB categories
register_kb_categories

# File a decision
file_decision "use-sqlite-over-room" "Room adds complexity we don't need"

# Search KB
search_kb "authentication"
```

## Documentation

- [Design](docs/plans/2026-04-04-pi-knowledge-base-design.md)
- [Implementation Plan](docs/plans/2026-04-04-pi-knowledge-base-implementation.md)
- [Epic & Issues](docs/plans/2026-04-04-pi-knowledge-base-epic.md)

## Roadmap

See [Epic KB-001](docs/plans/2026-04-04-pi-knowledge-base-epic.md) for issue breakdown.

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | Backlog | Core infrastructure (KB trackers, functions) |
| Phase 2 | Backlog | Extension integration (compaction hook, search tool) |
| Phase 3 | Backlog | Enhanced features (linting, export) |
| Phase 4 | Backlog | Documentation and tests |

## Contributing

This is personal infrastructure being open-sourced. Issues and PRs welcome for:

- Bug fixes
- Feature additions
- Documentation improvements

## License

MIT

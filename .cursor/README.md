# Memory Bank System

## Overview

The Memory Bank is a persistent context structure that enables seamless AI agent handoffs without hallucinations. It provides both long-term project memory and short-term session tracking.

## Purpose

- **Eliminate Context Loss**: New agents can quickly understand project state
- **Prevent Hallucinations**: Documented decisions prevent agents from making conflicting choices
- **Enable Continuity**: Work can be paused and resumed without losing progress
- **Track Progress**: Clear visibility into what's done, in progress, and planned

## Directory Structure

```
.cursor/
├── README.md                    # This file - System documentation
├── memory/                      # Long-term context (rarely changes)
│   ├── PROJECT_BRIEF.md         # ReadOnly - Project goals + Future Capabilities
│   ├── TECH_STACK.md            # ReadOnly - Technologies and versions
│   ├── ARCHITECTURE.md          # ReadOnly - System design and patterns
│   ├── PRODUCT_ROADMAP.md       # Read/Write - Epics, workstreams, tasks
│   ├── LESSONS_LEARNED.md       # Read/Write - Patterns and gotchas
│   └── DECISION_LOG.md          # Read/Write - Architecture Decision Records
└── active_sprint/               # Short-term state (high-frequency updates)
    ├── CURRENT_OBJECTIVE.md     # What we're working on right now
    └── TASK_LOG.md              # Progress log with timestamps
```

## Agent Protocol

### On Session Start

1. **Read Roadmap**: Check `memory/PRODUCT_ROADMAP.md` for current priorities
2. **Print Plan**: Show user the proposed plan before executing
3. **Get Approval**: Wait for user to approve or pivot
4. **Resume Work**: Check `active_sprint/CURRENT_OBJECTIVE.md` for in-progress work

### During Work

1. **Update Task Log**: Record progress in `active_sprint/TASK_LOG.md`
2. **Record Decisions**: Architecture decisions → `memory/DECISION_LOG.md`
3. **Record Learnings**: Patterns and gotchas → `memory/LESSONS_LEARNED.md`
4. **Track Todos**: Use hierarchical format: `[Epic X > WS Y.Z] Task`

### On Session End

1. **Update Objective**: Note any incomplete work
2. **Update Roadmap**: Mark completed tasks
3. **Commit Changes**: Follow Version Control Protocol

## File Descriptions

### Long-Term Memory (`memory/`)

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `PROJECT_BRIEF.md` | Mission, scope, and future capabilities | Rarely (project pivots only) |
| `TECH_STACK.md` | Technologies, versions, dependencies | When stack changes |
| `ARCHITECTURE.md` | System design, patterns, principles | When architecture evolves |
| `PRODUCT_ROADMAP.md` | Epics, workstreams, task status | Each session |
| `LESSONS_LEARNED.md` | Technical patterns, gotchas, warnings | When discoveries made |
| `DECISION_LOG.md` | ADRs (Architecture Decision Records) | When decisions made |

### Short-Term State (`active_sprint/`)

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `CURRENT_OBJECTIVE.md` | Active session goal and context | Each session start/end |
| `TASK_LOG.md` | Timestamped progress entries | Multiple times per session |

## Decision Heuristic

When to log where:

- **DECISION_LOG.md**: Architecture choices, technology selections, design patterns
  - "I chose X over Y because..."
  - "We will use pattern Z for..."
  
- **LESSONS_LEARNED.md**: Bugs found, constraints discovered, patterns observed
  - "Docker health checks should be lightweight because..."
  - "Always check X before Y because..."

## Test Types

The Memory Bank system supports a two-phase testing strategy:

| Marker | Phase | Description |
|--------|-------|-------------|
| `@unit` | Build-time | Mocked, no I/O |
| `@integration` | Runtime | Requires DB/services |
| `@browser` | Runtime | Uses browser tools |
| `@real-asset` | Runtime | Uses actual photos/videos |
| `@slow` / `@heavy` | Decoupled | Media processing |

## Integration with .cursorrules

The Memory Bank system is enforced via `.cursorrules` Sections 9 and 10:
- Section 9: Memory Bank Protocol (startup, during, end behaviors)
- Section 10: User Story Testing Protocol (two-phase testing)


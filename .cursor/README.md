# Memory Bank System

**Purpose:** Persistent context structure for seamless AI agent handoffs without hallucinations.

---

## Directory Structure

```
.cursor/
├── README.md                    # This file - system documentation
├── memory/                      # Long-term context (ReadOnly or Read/Write)
│   ├── PROJECT_BRIEF.md         # Mission, scope, future capabilities
│   ├── TECH_STACK.md            # Technologies and versions
│   ├── ARCHITECTURE.md          # System design and data flow
│   ├── PRODUCT_ROADMAP.md       # Epics, workstreams, tasks
│   ├── LESSONS_LEARNED.md       # Patterns and gotchas
│   └── DECISION_LOG.md          # Architecture Decision Records
└── active_sprint/               # Short-term state (High-frequency updates)
    ├── CURRENT_OBJECTIVE.md     # Current session goal
    └── TASK_LOG.md              # Progress tracking
```

---

## File Purposes

### Long-Term Context (`memory/`)

| File | Update Frequency | Purpose |
|------|-----------------|---------|
| `PROJECT_BRIEF.md` | Rarely | Mission, scope, future capabilities |
| `TECH_STACK.md` | On dependency changes | Technologies, versions, packages |
| `ARCHITECTURE.md` | On structural changes | System design, data flow, modules |
| `PRODUCT_ROADMAP.md` | Weekly/Sprint | Epics, workstreams, task status |
| `LESSONS_LEARNED.md` | After issues | Patterns, gotchas, debugging tips |
| `DECISION_LOG.md` | On architecture decisions | ADRs (Architecture Decision Records) |

### Short-Term Context (`active_sprint/`)

| File | Update Frequency | Purpose |
|------|-----------------|---------|
| `CURRENT_OBJECTIVE.md` | Per session | What agent is currently working on |
| `TASK_LOG.md` | Per task | Detailed progress, blockers, notes |

---

## Agent Startup Protocol

When a new agent session begins:

1. **Read Roadmap Context:**
   - Read `memory/PRODUCT_ROADMAP.md`
   - Read `active_sprint/CURRENT_OBJECTIVE.md` (if exists)

2. **Print Plan:**
   ```
   📋 Current Context:
   - Epic: [Epic name and status]
   - Workstream: [WS name and status]
   - Tasks: [List of pending tasks]
   
   🎯 Proposed Actions:
   1. [Action 1]
   2. [Action 2]
   ...
   
   Shall I proceed with this plan?
   ```

3. **Await Approval:**
   - Wait for user confirmation before executing
   - Adjust plan if user provides different direction

4. **Execute & Update:**
   - Work through tasks
   - Update `TASK_LOG.md` with progress
   - Update roadmap on task completion

---

## Recording Guidelines

### When to Add a DECISION (DECISION_LOG.md)

Add a decision record when:
- Choosing a technology or framework
- Selecting an architecture pattern
- Making a schema design choice
- Picking an infrastructure approach

### When to Add a LESSON (LESSONS_LEARNED.md)

Add a lesson when:
- Discovering a bug and its root cause
- Learning about operational constraints
- Finding performance insights
- Solving tricky debugging scenarios

### Heuristic

> **DECISION:** "We chose X because..."  
> **LESSON:** "We learned that X causes Y when..."

---

## Todo Format

When using the todo system, use hierarchical format:

```
[Epic X > WS Y.Z] Task description
```

Examples:
- `[Epic 0 > WS 0.2] Write TECH_STACK.md from docker-compose and requirements`
- `[Epic 2 > WS 2.1] Create system_status table`

---

## Maintenance

### Regular Updates

| Trigger | Action |
|---------|--------|
| Task completed | Update PRODUCT_ROADMAP.md |
| Bug fixed | Add to LESSONS_LEARNED.md |
| Architecture choice | Add ADR to DECISION_LOG.md |
| Session end | Update CURRENT_OBJECTIVE.md |

### Periodic Review

- **Weekly:** Review PRODUCT_ROADMAP.md, update task statuses
- **Monthly:** Review LESSONS_LEARNED.md, consolidate patterns
- **Quarterly:** Review DECISION_LOG.md, validate decisions still valid

---

**END OF README**

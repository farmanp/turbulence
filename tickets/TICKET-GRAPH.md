# Windtunnel Ticket Dependency Graph

This document defines ticket dependencies and parallel execution batches for autonomous implementation.

## Dependency Legend

```
A → B    : B depends on A (A must complete before B starts)
A | B    : A and B can run in parallel (no dependency)
[batch]  : Tickets in same batch can be worked in parallel
```

## Full Dependency Graph

```
                                    INFRA-001
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
               FEAT-001            FEAT-002            FEAT-003
               (CLI)           (SUT Config)        (Scenario Loader)
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
               FEAT-004            FEAT-005            FEAT-006
            (HTTP Action)       (Wait Action)       (Assert Action)
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        │
                                        ▼
                                   FEAT-007
                              (Context Templating)
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
               FEAT-008            FEAT-009            FEAT-010
            (Artifact Store)    (HTML Report)         (Replay)
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
               FEAT-011            FEAT-012        FEAT-013 | FEAT-014
           (Parallel Exec)      (Turbulence)     (Schema)  | (Expressions)
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        │
                                ┌───────┼───────┐
                                │       │       │
                                ▼       ▼       ▼
                           FEAT-015  FEAT-016  FEAT-017
                          (Reports)  (CI Gate) (Variation)
                                │       │       │
                                └───────┴───────┘
                                        │
                          ┌─────────────┼─────────────┐
                          │             │             │
                          ▼             ▼             ▼
                     FEAT-018      FEAT-019      SPIKE-001
                     (SQLite)    (Branching)    (LLM Research)
```

## Parallel Execution Batches

Execute each batch to completion before starting the next. Within a batch, all tickets can be worked in parallel.

### Batch 0: Foundation
| Ticket | Title | Dependencies | Estimated Complexity |
|--------|-------|--------------|---------------------|
| INFRA-001 | Project setup and Python package scaffolding | None | Medium |

**Batch Notes:** Must complete before any other work. Sets up the development environment.

---

### Batch 1: CLI & Configuration (Parallel)
| Ticket | Title | Dependencies | Estimated Complexity |
|--------|-------|--------------|---------------------|
| FEAT-001 | CLI scaffold with run, report, replay commands | INFRA-001 | Medium |
| FEAT-002 | SUT config loader | INFRA-001 | Low |
| FEAT-003 | Scenario loader and YAML parser | INFRA-001 | Medium |

**Batch Notes:** All three tickets only depend on INFRA-001. Can be developed and tested independently.

---

### Batch 2: Action Runners (Parallel)
| Ticket | Title | Dependencies | Estimated Complexity |
|--------|-------|--------------|---------------------|
| FEAT-004 | HTTP action runner with extraction | FEAT-002, FEAT-003 | Medium |
| FEAT-005 | Wait action runner with polling | FEAT-002, FEAT-003 | Medium |
| FEAT-006 | Assert action with basic expectations | FEAT-002, FEAT-003 | Low |

**Batch Notes:** Action runners share the same interface. Can be developed in parallel with mock configs.

---

### Batch 3: Context Engine
| Ticket | Title | Dependencies | Estimated Complexity |
|--------|-------|--------------|---------------------|
| FEAT-007 | Context templating engine | FEAT-004, FEAT-005, FEAT-006 | Medium |

**Batch Notes:** Sequential - requires action runners to integrate with. This is the glue that connects entry data → actions → extractions.

---

### Batch 4: Persistence & Output (Parallel)
| Ticket | Title | Dependencies | Estimated Complexity |
|--------|-------|--------------|---------------------|
| FEAT-008 | JSONL artifact storage and run persistence | FEAT-007 | Medium |
| FEAT-009 | Basic HTML report generation | FEAT-007 | Medium |
| FEAT-010 | Replay command implementation | FEAT-007, FEAT-001 | Medium |

**Batch Notes:** All depend on context engine but don't depend on each other. FEAT-010 also needs CLI from FEAT-001.

---

### Batch 5: Scale & Resilience (Parallel)
| Ticket | Title | Dependencies | Estimated Complexity |
|--------|-------|--------------|---------------------|
| FEAT-011 | Parallel execution engine | FEAT-008 | High |
| FEAT-012 | Turbulence engine v0 | FEAT-004 | Medium |
| FEAT-013 | Schema validation expectation | FEAT-006 | Low |
| FEAT-014 | Custom expression evaluator | FEAT-006 | High |

**Batch Notes:**
- FEAT-011 needs artifact storage for concurrent writes
- FEAT-012 wraps HTTP actions for fault injection
- FEAT-013/014 extend assertion capabilities

---

### Batch 6: Polish & CI (Parallel)
| Ticket | Title | Dependencies | Estimated Complexity |
|--------|-------|--------------|---------------------|
| FEAT-015 | Enhanced report aggregations | FEAT-009, FEAT-011 | Medium |
| FEAT-016 | CI gating with fail-on thresholds | FEAT-011 | Low |
| FEAT-017 | Deterministic variation engine | FEAT-007 | Medium |

**Batch Notes:**
- FEAT-015 needs basic reports + parallel execution data
- FEAT-016 needs run metrics from parallel execution
- FEAT-017 only needs context engine (variation feeds into context)

---

### Batch 7: Future Enhancements (Parallel, Optional)
| Ticket | Title | Dependencies | Estimated Complexity |
|--------|-------|--------------|---------------------|
| FEAT-018 | SQLite backend for run storage | FEAT-008 | Medium |
| FEAT-019 | Branching flows and actor policies | FEAT-007, FEAT-006 | High |
| SPIKE-001 | LLM-driven actor policy research | FEAT-017, FEAT-019 | Research |

**Batch Notes:** These are optional enhancements. Can be deferred or worked based on priority.

---

## Dependency Matrix

| Ticket | Depends On | Blocks |
|--------|-----------|--------|
| INFRA-001 | - | FEAT-001, FEAT-002, FEAT-003 |
| FEAT-001 | INFRA-001 | FEAT-010 |
| FEAT-002 | INFRA-001 | FEAT-004, FEAT-005, FEAT-006 |
| FEAT-003 | INFRA-001 | FEAT-004, FEAT-005, FEAT-006 |
| FEAT-004 | FEAT-002, FEAT-003 | FEAT-007, FEAT-012 |
| FEAT-005 | FEAT-002, FEAT-003 | FEAT-007 |
| FEAT-006 | FEAT-002, FEAT-003 | FEAT-007, FEAT-013, FEAT-014, FEAT-019 |
| FEAT-007 | FEAT-004, FEAT-005, FEAT-006 | FEAT-008, FEAT-009, FEAT-010, FEAT-017, FEAT-019 |
| FEAT-008 | FEAT-007 | FEAT-011, FEAT-018 |
| FEAT-009 | FEAT-007 | FEAT-015 |
| FEAT-010 | FEAT-007, FEAT-001 | - |
| FEAT-011 | FEAT-008 | FEAT-015, FEAT-016 |
| FEAT-012 | FEAT-004 | - |
| FEAT-013 | FEAT-006 | - |
| FEAT-014 | FEAT-006 | - |
| FEAT-015 | FEAT-009, FEAT-011 | - |
| FEAT-016 | FEAT-011 | - |
| FEAT-017 | FEAT-007 | SPIKE-001 |
| FEAT-018 | FEAT-008 | - |
| FEAT-019 | FEAT-007, FEAT-006 | SPIKE-001 |
| SPIKE-001 | FEAT-017, FEAT-019 | - |

## Critical Path

The longest dependency chain determines minimum implementation time:

```
INFRA-001 → FEAT-002 → FEAT-004 → FEAT-007 → FEAT-008 → FEAT-011 → FEAT-015
    │           │           │           │           │           │         │
  Batch 0    Batch 1    Batch 2    Batch 3    Batch 4    Batch 5   Batch 6
```

**Critical path length: 7 sequential batches**

## AI Agent Execution Instructions

### For Each Batch:
1. Check all dependencies are complete (previous batch done)
2. Start all tickets in the batch in parallel
3. For each ticket:
   - Read the ticket file
   - Implement according to acceptance criteria
   - Write tests
   - Verify acceptance criteria pass
   - Mark ticket complete
4. Only proceed to next batch when ALL tickets in current batch are complete

### Completion Checklist per Ticket:
- [ ] All acceptance criteria satisfied
- [ ] Unit tests written and passing
- [ ] Integration points with dependencies verified
- [ ] No regressions in dependent tickets
- [ ] Code follows project patterns (from INFRA-001)

### Handling Blockers:
- If blocked on a dependency not in the ticket graph, document and ask for clarification
- If a ticket's scope needs adjustment, note the reason and propose changes
- If tests fail due to dependency issues, check the dependent ticket first

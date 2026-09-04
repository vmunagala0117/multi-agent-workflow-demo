# Enterprise Agentic AI Platform Demo

> Production-minded agentic AI prototype showing reusable orchestration, MCP/tools, structured state, checkpointing, HITL, evaluation, observability, and enterprise deployment patterns.

## Objective

Build one reusable agentic AI framework and prove it across two representative clean-room use cases:

1. **MedEvidence Research**
   - LangGraph multi-agent orchestration
   - parallel research
   - structured state
   - checkpointing / recovery
   - citation validation
   - human approval
   - evaluation / tracing

2. **InsightOps Enterprise Analytics**
   - reusable skills
   - agent + MCP routing
   - governed tool access
   - domain/context routing
   - golden-question evaluation

This repository uses synthetic/public data and does not reproduce confidential client implementations.


## Repository Strategy

Both use cases intentionally live in the **same repository**.

The purpose is to prove that shared platform primitives can support materially different workflows:

```text
Shared Agentic Platform
   ├── MedEvidence Research
   └── InsightOps Enterprise Analytics
```

The use cases remain separated under `use_cases/`, while reusable capabilities live under `app/`.

This lets us demonstrate:

- shared orchestration patterns
- reusable state / checkpointing
- common policy controls
- common observability / evaluation
- reusable MCP / tool abstractions
- independent use-case logic

If either use case later requires its own runtime, scaling profile, security boundary, or release cadence, it can be deployed independently without splitting the source repository immediately.


## Design Principles

- Build concrete first; extract reusable patterns second.
- Keep deterministic things deterministic.
- Use agents where semantic reasoning is needed.
- Compute should be disposable; state should be durable.
- Checkpointing tells us where to resume; idempotency makes recovery safe.
- Prompts guide behavior; deterministic controls enforce policy.
- Reuse capabilities, not whole use cases.
- Evaluation and observability are part of the runtime lifecycle.


## Technology Direction

We will implement incrementally and avoid provisioning infrastructure before it is needed.

Initial stack:

- **LangGraph** — orchestration and stateful workflows
- **LangSmith** — tracing, debugging, evaluation, and regression analysis
- **Azure AI Foundry / Azure OpenAI** — model endpoints
- **Local or lightweight persistence first** — then external durable checkpointing
- **Synthetic/public data only**

Later phases may add:

- **Azure AI Search** for permission-aware / vector retrieval
- **Azure Container Apps** for runtime deployment
- **Managed Identity / Entra ID** for workload and delegated access patterns
- **APIM** for gateway, throttling, policy, and production controls
- **Azure Monitor / Application Insights** if useful alongside LangSmith

Azure AI Search and Foundry do not need to be in the same Azure region for this prototype. Cross-region calls are workable for a demo, although production design should consider latency, data residency, networking, and service availability.


## High-Level Architecture

```text
User / API Client
       |
       v
API / Gateway
       |
       v
LangGraph Orchestrator
       |
 +-----+--------------------------+
 |                                |
 v                                v
Agent / Skill Nodes          Policy Layer
 |                                |
 +---------------+----------------+
                 |
                 v
            Tool / MCP Layer
                 |
        +--------+---------+
        |                  |
        v                  v
Retrieval/Search     Enterprise Data/APIs
        |
        v
Structured Workflow State
        |
        v
Durable Checkpoint Store
        |
        v
Evaluation / Tracing / Monitoring
```

Cross-cutting: Identity, Authorization, State, Security, GxP, Cost, Deployment, Versioning.

## Project Layout

```text
enterprise-agentic-platform-demo/
├── app/
│   ├── api/              # API entry points
│   ├── orchestration/    # LangGraph graphs / routing
│   ├── agents/           # reusable agents / skills
│   ├── tools/            # tool abstractions / adapters
│   ├── mcp/              # MCP client/server/tool schemas
│   ├── state/            # state schemas / reducers / checkpointing
│   ├── policies/         # deterministic policy gates
│   ├── evals/            # reusable evaluators
│   └── observability/    # tracing / metrics / logging
├── use_cases/
│   ├── medevidence_research/
│   └── insightops_analytics/
├── tests/
│   ├── unit/
│   └── integration/
├── evals/
│   ├── datasets/
│   └── results/
├── docs/
│   ├── architecture/
│   └── decisions/
├── scripts/
├── requirements.txt
├── .env.example
└── README.md
```

## MedEvidence-Style Target Architecture

```text
Medical User
    |
    v
Request Validation
    |
    v
LangGraph Orchestrator
    |
    +----------------------+----------------------+
    |                                             |
    v                                             v
Literature Research Agent                Internal Evidence Agent
    |                                             |
    +----------------------+----------------------+
                           |
                           v
                    Synthesis Agent
                           |
                           v
                  Citation Validation
                           |
                           v
                   Human Approval
                           |
                           v
                     Final Response
```

## InsightOps-Style Target Architecture

```text
Business User
    |
    v
Intent / Domain Classifier
    |
    v
Agent / Orchestrator
    |
    v
Skill Selection
    |
    +--------------------+--------------------+
    |                                         |
    v                                         v
Finance Skill                           Operations Skill
    |                                         |
    v                                         v
MCP Finance Tool                        MCP Operations Tool
    |                                         |
    +--------------------+--------------------+
                         |
                         v
                Synthetic Enterprise Data
                         |
                         v
                  Grounded Response
```

# Implementation Phases

## Phase 0 — Project Bootstrap
**Status:** 🟨 In Progress

Deliverables:
- [ ] Python environment
- [x] requirements.txt
- [x] .env.example
- [x] basic config/logging
- [x] smoke test script
- [x] initial README

Learning focus:
- repo boundaries
- framework vs use-case code
- avoid premature abstraction

---

## Phase 1 — MedEvidence State Model + LangGraph Skeleton
**Status:** ⬜ Not Started

Deliverables:
- [ ] MedicalResearchState
- [ ] START/END graph
- [ ] validation node
- [ ] literature node
- [ ] internal evidence node
- [ ] synthesis node
- [ ] conditional routing
- [ ] CLI execution

Questions:
- What belongs in state?
- What should be deterministic?
- Which nodes need an LLM?
- What can run in parallel?
- Who owns each state field?

---

## Phase 2 — Parallel Agents + Structured State
**Status:** ⬜ Not Started

Deliverables:
- [ ] literature agent
- [ ] internal evidence agent
- [ ] parallel branches
- [ ] scoped state updates
- [ ] reducer/merge behavior
- [ ] join/synthesis node

System design drill:
> What happens if one parallel branch succeeds and the other fails?

---

## Phase 3 — Tools + Retrieval
**Status:** ⬜ Not Started

Deliverables:
- [ ] public/synthetic research tool
- [ ] internal retrieval tool
- [ ] tool schemas
- [ ] structured outputs
- [ ] timeout/retry handling

System design drill:
> Why is retrieval a tool/capability rather than another autonomous agent?

---

## Phase 4 — Checkpointing + Recovery
**Status:** ⬜ Not Started

Deliverables:
- [ ] checkpoint store
- [ ] workflow/thread ID
- [ ] resume after simulated failure
- [ ] externalized state
- [ ] replica-independent recovery

System design drill:
> What happens if the runtime dies after a tool succeeds but before the checkpoint commits?

---

## Phase 5 — Idempotency + Failure Safety
**Status:** ⬜ Not Started

Deliverables:
- [ ] stable operation IDs
- [ ] idempotency ledger/mock
- [ ] duplicate-execution protection
- [ ] retry policy
- [ ] failure simulation

```text
Checkpointing = where to resume
Idempotency  = how to resume safely
```

---

## Phase 6 — Citation Validation + HITL
**Status:** ⬜ Not Started

Deliverables:
- [ ] citation validator
- [ ] claim/source mapping
- [ ] approval state
- [ ] interrupt/suspend
- [ ] approve/reject/modify path
- [ ] audit metadata

Learning focus:
- deterministic control boundaries
- HITL mechanics
- abstention
- patient-safety / regulated-use thinking

---

## Phase 7 — Extract Reusable Framework Components
**Status:** ⬜ Not Started

Candidate components:
- [ ] state/checkpoint helper
- [ ] policy gate
- [ ] tool registry
- [ ] trace helper
- [ ] model wrapper
- [ ] human-approval component
- [ ] evaluator interface
- [ ] shared error handling

Design rule:
> Build concrete first; extract repeated patterns second.

---

## Phase 8 — InsightOps-Style Skills + MCP
**Status:** ⬜ Not Started

Deliverables:
- [ ] domain classifier
- [ ] finance skill
- [ ] operations skill
- [ ] MCP server
- [ ] MCP tool definitions
- [ ] synthetic enterprise data
- [ ] governed routing
- [ ] policy checks

System design drill:
> Why MCP instead of calling the database/API directly?

---

## Phase 9 — Evaluation Harness
**Status:** ⬜ Not Started

Deliverables:
- [ ] golden dataset
- [ ] routing eval
- [ ] retrieval eval
- [ ] tool-selection eval
- [ ] trajectory eval
- [ ] citation accuracy
- [ ] response relevance/groundedness
- [ ] regression runner

```text
Component → Trajectory → Outcome
```

---

## Phase 10 — Observability
**Status:** ⬜ Not Started

Deliverables:
- [ ] correlation IDs
- [ ] graph/node traces
- [ ] latency
- [ ] token usage
- [ ] tool traces
- [ ] retry/error telemetry
- [ ] agent/prompt/graph version metadata

```text
System → Trajectory → Quality
```

---

## Phase 11 — Production Architecture Mapping
**Status:** ⬜ Not Started

Topics:
- [ ] APIM / gateway
- [ ] Entra ID / OBO / Managed Identity
- [ ] Container Apps / AKS
- [ ] external checkpoint store
- [ ] queue / async workers
- [ ] model gateway
- [ ] MCP deployment
- [ ] SIEM/logging
- [ ] secrets/private networking
- [ ] scaling/backpressure

---

## Phase 12 — Deployment + Versioning
**Status:** ⬜ Not Started

Deliverables:
- [ ] version metadata
- [ ] prompt version
- [ ] graph version
- [ ] tool version
- [ ] state-schema version
- [ ] canary / blue-green design
- [ ] rollback criteria

```text
Agent Version =
Code + Prompt + Model + Tools + Graph +
State Schema + Configuration + Eval Baseline
```

---

## Phase 13 — Documentation + Interview Walkthrough
**Status:** ⬜ Not Started

Deliverables:
- [ ] polished README
- [ ] architecture diagrams
- [ ] ADRs
- [ ] demo instructions
- [ ] production-vs-demo distinctions
- [ ] known limitations
- [ ] roadmap
- [ ] 10-minute walkthrough
- [ ] 30-minute deep dive

# Proposed Build Sequence

```text
MedEvidence workflow
   ↓
State
   ↓
Agents
   ↓
Tools
   ↓
Checkpointing
   ↓
HITL / Citations
   ↓
Extract reusable primitives
   ↓
InsightOps skills + MCP
   ↓
Evaluation
   ↓
Observability
   ↓
Production mapping
   ↓
Interview rehearsal
```

# Learning / Interview Method

At every build checkpoint:

1. Explain what was implemented.
2. Explain why it was designed that way.
3. Identify contention/failure points.
4. Discuss alternatives/tradeoffs.
5. Answer a system-design follow-up without looking at the code.

Use Codex primarily for boilerplate and repetitive work. Core architecture decisions should remain understandable and defendable without generated explanations.

# Success Criteria

By the end, the repository should demonstrate the ability to:

- implement LangGraph workflows
- explain single vs multi-agent tradeoffs
- design structured durable state
- build tool/MCP abstractions
- implement failure recovery
- explain idempotency
- implement HITL
- evaluate agent behavior
- trace/debug workflows
- create reusable enterprise capabilities
- map a prototype to production
- explain identity, security, scaling, latency, deployment, and GxP tradeoffs
- defend major design decisions in an interview

# Current Status

```text
Phase 0  Project Bootstrap                     ⬜
Phase 1  MedEvidence State + LangGraph Skeleton       ⬜
Phase 2  Parallel Agents                       ⬜
Phase 3  Tools + Retrieval                     ⬜
Phase 4  Checkpointing                         ⬜
Phase 5  Idempotency                           ⬜
Phase 6  Citations + HITL                      ⬜
Phase 7  Reusable Framework Extraction         ⬜
Phase 8  InsightOps Skills + MCP                      ⬜
Phase 9  Evaluation Harness                    ⬜
Phase 10 Observability                         ⬜
Phase 11 Production Architecture Mapping       ⬜
Phase 12 Deployment + Versioning               ⬜
Phase 13 Documentation + Interview Walkthrough ⬜
```

# Next Step

Begin Phase 0, then move immediately into Phase 1.

First design question:

> What state does the MedEvidence-style workflow need to carry from the user request through research, synthesis, citation validation, and approval?

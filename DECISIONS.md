# HowlRelay Architectural Decision Records (ADRs)

This document tracks significant architectural decisions for HowlRelay using lightweight ADR entries.

---

## ADR-0001: Anti-Surveillance Core Principle and Prohibited Signals
- **Date:** 2026-09-06
- **Status:** Accepted
- **Context:**
  Distributed engineering tools frequently drift into monitoring employee presence, keystrokes, active windows, or online activity. This conflates visibility of the worker with observability of the work.
- **Decision:**
  HowlRelay adopts the foundational principle: **"Measure the work system, not the worker."**
  HowlRelay explicitly prohibits and filters signals related to:
  - Keystroke frequency / typing activity
  - Mouse movement
  - Webcams / screen captures / active application tracking
  - Presence status (Slack, Teams, etc.)
  - Idle time / away duration
  - Badge swipes / physical office attendance
  - Raw hours-online metrics
  All domain models and adapters must strictly validate or sanitize input to reject these signals.
- **Consequences:**
  - Guarantees psychological safety and ethical alignment.
  - Keeps HowlRelay focused purely on artifacts, verifiable outputs, decisions, dependencies, and state of work.

---

## ADR-0002: Python, Pydantic V2, and Local-First CLI Architecture
- **Date:** 2026-09-06
- **Status:** Accepted
- **Context:**
  HowlRelay needs to be fast, dependable, locally executable by both human developers and autonomous AI agents, and easily integrated with Howl ecosystem tools (HowlPlane, HowlChangeOps, HowlWriter).
- **Decision:**
  Use Python (>=3.10) with Pydantic v2 for strong typing and data validation, PyYAML for serialization, and a modular `src/howlrelay` layout.
  External integrations (Git, CI, filesystems, HowlFrame) must reside behind adapter interfaces.
  The core engine must run locally without requiring network access, cloud databases, or LLM runtime calls. AI enhances reasoning when available, but deterministic rules govern evidence collection and verification.
- **Consequences:**
  - Instant local execution in any repo with zero external server dependencies.
  - High determinism and predictable machine-readable outputs (JSON, YAML, Markdown).

---

## ADR-0003: Evidence-Based Meeting-Required Reasoning States
- **Date:** 2026-09-06
- **Status:** Accepted
- **Context:**
  Engineering teams often schedule synchronous meetings by default due to a lack of observable work state. Conversely, an LLM hallucinating that "no meeting is needed" without evidence is dangerous.
- **Decision:**
  Introduce an evidence-based recommendation engine for synchronous alignment with 4 explicit states:
  1. `NOT_REQUIRED`: All work is progressing, decisions are resolved, tests pass, next actions are clear.
  2. `RECOMMENDED`: Non-trivial blocker or conflicting path detected where synchronous discussion could expedite resolution.
  3. `REQUIRES_HUMAN_DECISION`: A high-impact architectural choice or policy boundary requires explicit human authority.
  4. `INSUFFICIENT_EVIDENCE`: Insufficient state or evidence is available to determine if synchronous alignment is required.
  Every recommendation must output inspectable triggers and rationale.
- **Consequences:**
  - Prevents unnecessary status meetings while clearly highlighting genuine decision bottlenecks.
  - Maintains verifiable provenance for why a meeting was or was not recommended.

---

## ADR-0004: HowlFrame Capability & Loose Coupling Boundary
- **Date:** 2026-09-06
- **Status:** Accepted
- **Context:**
  HowlFrame provides capability-bounded policy evaluation in the Howl ecosystem. HowlRelay should leverage HowlFrame where available, but must not fail when running in environments where HowlFrame is not installed.
- **Decision:**
  Implement a dedicated `HowlFrameAdapter` with capability detection. If `howlframe` binary and policies are present, evaluate evidence envelopes through it; if absent, gracefully degrade to internal deterministic Python policy verification.
- **Consequences:**
  - Maintains ecosystem alignment with HowlFrame's "intent is not authority" model.
  - Preserves standalone local utility across any developer workstation or standard CI runner.

---

## ADR-0005: Heterogeneous Continuity Parsing and Code-Fence-Aware Extraction
- **Date:** 2026-09-06
- **Status:** Accepted
- **Context:**
  Dogfooding HowlRelay against sibling repository `howlcipher/howlcreate` exposed that real repositories frequently use numbered section headings (`## 1. System Summary`), heading synonyms (`Commands to Resume Work`, `What Works Right Now`), code comments starting with `#` inside bash blocks, and subdirectories (`docs/journal/`, `dogfood/`). Strict single-word regexes failed to extract structured context, yielding "Unknown objective" and empty completed work.
- **Decision:**
  1. Continuity parsing must be code-fence-aware: lines starting with `#` inside fenced blocks (` ``` `) must never be treated as Markdown heading boundaries.
  2. Section extraction must support numbered/bulleted prefixes (`1.`, `A.`) and priority synonym maps for standard engineering sections (Objective/Summary, Completed Work, Active Work, Starting Commands, Key Files).
  3. Canonical file audits must inspect standard subdirectories (`docs/`, `.github/`) for journals and decisions before flagging them missing.
  4. Working trees that are clean must fall back to surfacing key files documented in continuity or HEAD commit touched files so incoming agents retain immediate file context.
- **Consequences:**
  - Robust interoperability across diverse Howl ecosystem repositories without imposing rigid markdown templates.
  - Preserves anti-surveillance boundary by measuring the work artifacts rather than developer formatting conformity.

---

## ADR-0006: Deep Architectural Diff Analysis & Non-Surveilling Blocker Staleness Heuristics
- **Date:** 2026-09-06
- **Status:** Accepted
- **Context:**
  HowlRelay Milestone 2 requires deeper visibility into code churn and workstream friction without tracking worker activity or violating anti-surveillance policies. HowlCreate dogfooding run 4 (`run-ddef596c`, exploring stigmergic coordination and commit decay) identified that repository diffs and commit histories provide rich work-system signals if analyzed structurally.
- **Decision:**
  1. Implement `analyze_diff` in `GitCollector`:
     - Group uncommitted file changes into architectural layers (`core`, `tests`, `docs`, `config`, `other`).
     - Extract modified code symbols (functions, classes, methods) directly from unified diff hunk headers (`@@ ... @@ def/class`).
     - Evaluate **test parity risk**: flag a warning if core source files are modified without accompanying test modifications.
  2. Implement `compute_blocker_staleness` in `GitCollector`:
     - Measure blocker age by checking commit history (`git log -S` and `git rev-list --count`) to compute how many commits have landed on the repository branch while the blocker remained unresolved.
     - If a blocker has persisted across >= 3 commits, mark it `stale = True`.
  3. Integrate with `MeetingReasoningEngine`:
     - Stale blockers or critical blockers escalate the synchronous alignment recommendation to `RECOMMENDED` with explicit inspectable triggers (`stale_blockers(N)`).
- **Consequences:**
  - High-signal async handoffs that surface architectural risk (e.g. test parity gaps) and stuck work without surveilling the developer.
  - Objective escalation triggers grounded entirely in Git commit evidence.


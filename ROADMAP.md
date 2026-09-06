# HowlRelay Roadmap

This document outlines the evolutionary milestones of HowlRelay.

---

## Milestone 0 — Foundation [COMPLETED]
- [x] Authorize and initialize repository (`howlcipher/howlrelay`).
- [x] Set up standard project structure, `.gitignore`, `pyproject.toml`, `LICENSE`, `.flake8`.
- [x] Establish continuity files (`AGENTS.md`, `PROJECT_STATE.md`, `ROADMAP.md`, `JOURNAL.md`, `HANDOFF.md`, `DECISIONS.md`).
- [x] Configure Python virtual environment, package dependencies (`pydantic`, `pyyaml`, `pytest`, `flake8`).
- [x] Set up GitHub Actions CI workflow for test and lint.
- [x] Implement domain model foundation with anti-surveillance enforcement.
- [x] Implement CLI entrypoint skeleton (`howlrelay`).

---

## Milestone 1 — Evidence-Based Async Handoffs v1 [COMPLETED]
- [x] Implement Local Git Evidence Adapter:
  - Branch, HEAD revision, remote tracking, uncommitted diffs, recent commit log, commit trailers.
- [x] Implement Continuity Document Adapter:
  - Extracts explicit recorded objectives, decisions, blockers, and next steps from repository continuity files.
- [x] Implement Test Verification Adapter:
  - Discovers test frameworks, inspects test cache status, and captures live test execution evidence.
- [x] Implement Work-State & Handoff Domain Model:
  - Distinguishes observed facts, inferred state, missing information, and recommendations.
  - Preserves provenance (timestamps, hashes, source refs).
  - Enforces anti-surveillance policy (rejects keystroke, mouse, camera, presence, idle tracking).
- [x] Implement Meeting-Required Reasoning Engine:
  - Evidence-based classification: `NOT_REQUIRED`, `RECOMMENDED`, `REQUIRES_HUMAN_DECISION`, `INSUFFICIENT_EVIDENCE`.
  - Detailed inspectable triggers and rationale.
- [x] Implement `howlrelay handoff`:
  - Structured YAML/JSON export.
  - Clean deterministic Markdown formatting.
  - Continuation instructions for human engineers and AI coding agents.
  - Epistemic provenance reporting.
- [x] Dogfood `howlrelay handoff` on HowlRelay itself:
  - Verified against HowlRelay repository development.

---

## Milestone 2 — Project Status & Team Brief [CURRENT]
- [x] Implement `howlrelay status`:
  - Current state of project / workstream, completed work, active work, blockers, dependencies, risks, confidence.
- [x] Implement `howlrelay brief`:
  - Team brief summarizing meaningful progress, decisions, blockers, risk changes, requests for action.
  - Anti-activity-theater filtering (no noise for the sake of looking busy).
- [x] Structured export formats (`--json`, `--yaml`, `--markdown`).
- [ ] Deep diff-summary analysis in status/brief.
- [ ] Blocker age tracking and dependency staleness detection.

---

## Milestone 3 — HowlFrame Integration & Policy Gates
- [x] Inspect and connect with HowlFrame runtime (`howlframe` binary / `.howl` policies).
- [x] Capability model discovery and graceful fallback when HowlFrame is absent.
- [ ] Formal `.howl` policy module for handoff integrity checking.
- [ ] Cryptographic digest binding for handoff envelopes matching HowlChangeOps / HowlFrame patterns.

---

## Milestone 4 — GitHub & Ecosystem Adapters
- [ ] Pull Request evidence collector (PR head, reviews, status checks).
- [ ] GitHub Issues evidence collector (blockers, linked issues).
- [ ] CI/CD run evidence collector.
- [ ] HowlPlane run/task integration adapter.

---

## Milestone 5 — Distributed Work Health
- [ ] System-level work health heuristics:
  - Handoff completeness index.
  - Stale blocker detection.
  - Undocumented decision alerts.
  - Dependency age and approval latency tracking.
- [ ] Anti-surveillance guarantee: No worker rankings, no presence metrics, no individual surveillance scores. Measure the work system, not the worker.

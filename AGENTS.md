# AGENTS.md — Operating Instructions for Coding Agents

Welcome to **HowlRelay**. This document contains mandatory instructions and operating protocols for any AI coding agent or human contributor working in this repository.

---

## 1. Project Purpose & Core Thesis

HowlRelay is an **async-first coordination and handoff system for distributed engineering teams**.

### Core Principle
> Remote and distributed work should be evaluated by whether work is observable, transferable, verifiable, and capable of continuing asynchronously — not by whether workers are physically visible.

### Foundational Principle
> **Measure the work system, not the worker.**

### Engineering Hypothesis
> Distributed engineering teams operate more effectively when work state, decisions, evidence, blockers, ownership, dependencies, and next actions are explicit and transferable.

---

## 2. Anti-Surveillance Policy & Prohibited Signals

HowlRelay is strictly **NOT**:
* an employee monitoring system
* a keystroke tracker
* a mouse activity tracker
* a webcam monitoring system
* an idle-time tracker
* a presence monitor
* an activity-theater generator

### Strictly Prohibited Signals
Never infer productivity or work quality from:
* Keystrokes or typing frequency
* Mouse movements or clicks
* Webcam or microphone feeds
* Desktop screenshots or window switching
* Chat presence or online/offline status (Slack/Teams/Discord)
* Idle time or away duration
* Physical badge swipes or office attendance
* Raw hours-online metrics

If any upstream integration or data source exposes such signals, HowlRelay **must ignore, reject, or sanitize** them before ingestion into domain models.

---

## 3. Product Boundaries

HowlRelay is not a replacement for Jira, Slack, Teams, or an AI meeting-notes product.
It is an async handoff and coordination engine. It answers three questions through evidence:
1. `howlrelay status` — What is the current state of this project or workstream?
2. `howlrelay handoff` — What does another engineer or agent need to continue this work without talking to the previous person?
3. `howlrelay brief` — What does the broader team need to know without scheduling a status meeting?

### Grounding Rule: Never Fabricate Missing Information
* **Unknown is preferable to guessed.**
* Clearly distinguish between **observed facts**, **inferred state**, **missing information**, and **recommendations**.
* Preserve provenance for all claims (commit SHAs, file paths, test runs, policy digests).

---

## 4. Continuity Files & Source of Truth

We assume different agents will work across sessions with no shared conversational memory. The repository state itself is the baton pass.

The six canonical continuity files are:
1. `AGENTS.md` (this file): Permanent operating instructions and constraints.
2. `PROJECT_STATE.md`: Authoritative current snapshot (milestone, architecture, active features, test counts, debt, immediate priorities). Update whenever facts materially change.
3. `ROADMAP.md`: Milestones 0 through 5.
4. `JOURNAL.md`: Append-only chronological record of every development session.
5. `HANDOFF.md`: The active baton pass for the next agent. Concise, current, and rewritten every session.
6. `DECISIONS.md`: Architectural Decision Records (ADRs).

---

## 5. Mandatory Agent Session Protocol

### At Session Start
1. Read in order:
   - `AGENTS.md`
   - `PROJECT_STATE.md`
   - `HANDOFF.md`
   - Relevant portions of `ROADMAP.md`
   - Recent `JOURNAL.md` entries
   - Relevant `DECISIONS.md` entries
2. Inspect repository state:
   ```bash
   git status
   git log --oneline -10
   ```
3. Run the baseline test suite:
   ```bash
   .venv/bin/pytest
   ```
4. Verify repository facts. Code and verifiable Git state always win over out-of-date documentation.

### During Work
1. Work continuously toward the current milestone. Do not stop after brainstorming or writing empty templates.
2. Work in small, verifiable increments with strong typing and robust unit tests.
3. Keep external dependencies light and modular: use adapter boundaries.
4. Keep the core deterministic: no mandatory LLMs or cloud databases required for local operations.

### Before Ending Any Session
1. Run full test suite (`.venv/bin/pytest`).
2. Run linter (`.venv/bin/flake8 src tests`).
3. Check `git diff` for unintended changes.
4. Update `PROJECT_STATE.md` with factual counts and state.
5. Append session summary to `JOURNAL.md`.
6. Rewrite `HANDOFF.md` for the incoming agent.
7. Record any architectural decisions in `DECISIONS.md`.
8. Commit work with clean, descriptive messages.
9. Push commits to `origin/main` (or active feature branch).

---

## 6. Howl Ecosystem Relationships

HowlRelay lives within the Howl ecosystem alongside:
* `howlcipher/howlframe`: Capability-bounded execution runtime and policy verification engine.
* `howlcipher/howlplane`: AI engineering control plane.
* `howlcipher/changeops`: Bounded release authority and verification boundary.
* `howlcipher/howlwriter`: Writing, humanization, and citation verification.

### Neighboring Repository Rules
* **Do not make destructive changes** to other Howl repositories.
* Maintain a clean adapter boundary: HowlRelay must function locally when HowlFrame or HowlPlane are unavailable.
* Propose changes to other repos via separate branches or PRs if needed.

---

## 7. Verification Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with verbose output
pytest -v

# Run linter
flake8 src tests

# Test CLI
howlrelay --help
howlrelay status
howlrelay handoff
howlrelay brief
```

# HowlRelay

[![CI](https://github.com/howlcipher/howlrelay/actions/workflows/ci.yml/badge.svg)](https://github.com/howlcipher/howlrelay/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

> **HowlRelay is an async-first coordination and handoff system for distributed engineering teams.**
>
> It makes work state, decisions, blockers, evidence, dependencies, and next actions transferable without requiring constant meetings or employee surveillance.
>
> **Measure the work system, not the worker.**

---

## The Problem

Modern distributed engineering teams suffer from two opposing failure modes:

1. **Synchronous Meeting Saturation:** Because the state of work is fragmented across git branches, uncommitted local changes, ephemeral chat threads, and human memories, teams schedule endless status meetings just to answer: *"Where are we, what's blocked, and who owns what next?"*
2. **Surveillance Creep:** In response to remote work visibility challenges, management tools increasingly monitor keystrokes, active windows, mouse activity, webcam feeds, and presence dots. This confuses *visibility of the worker* with *observability of the work* and destroys trust.

Distributed engineering teams do not need surveillance. They need **explicit, verifiable, and transferable work state**.

---

## Core Thesis & Philosophy

- **Remote and distributed work should be evaluated by whether work is observable, transferable, verifiable, and capable of continuing asynchronously — not by whether workers are physically visible.**
- **Intent is not authority, and opinion is not evidence:** Work claims must be backed by verifiable artifacts (commits, diffs, tests, documented decisions, CI results).
- **Never fabricate missing information:** `Unknown` is strictly preferable to guessed or hallucinated state.
- **Evidence-based meeting recommendations:** A meeting is not deemed "unnecessary" based on LLM whims. Instead, HowlRelay analyzes unresolved architectural decisions, critical blockers, and test evidence to recommend whether synchronous discussion is genuinely required.

---

## Anti-Surveillance Policy

HowlRelay adheres to an explicit privacy policy:
- **Prohibited signals:** Keystroke monitoring, mouse tracking, webcam or microphone captures, desktop screenshots, active window tracking, chat presence tracking (Slack/Teams), idle time tracking, physical office attendance/badge tracking, and raw hours-online metrics.
- **Filtering & Sanitation:** Ingestion adapters reject or sanitize surveillance signals before they can influence work-system assessments.

---

## What HowlRelay Is NOT

* NOT an employee monitoring system.
* NOT a keystroke or mouse tracker.
* NOT a replacement for Jira, Slack, or Microsoft Teams.
* NOT an AI meeting-notes generator.
* NOT activity-theater software.

---

## CLI Interface

HowlRelay provides three primary local-first commands:

```bash
# 1. What is the current state of this project or workstream?
howlrelay status

# 2. What does another engineer or agent need to continue this work without talking to the previous person?
howlrelay handoff

# 3. What does the broader team need to know without scheduling a status meeting?
howlrelay brief
```

### Options & Formats
All commands support structured export and target repository selection:
```bash
howlrelay handoff --repo /path/to/project --format markdown
howlrelay handoff --json
howlrelay handoff --yaml
howlrelay handoff --update-handoff  # Writes directly to HANDOFF.md
```

---

## Howl Ecosystem Relationships

HowlRelay is built to integrate with the broader **Howl** ecosystem:

* **[HowlFrame](https://github.com/howlcipher/howlframe):** Capability-bounded execution runtime and policy verification engine. HowlRelay integrates with HowlFrame policies when present, while remaining fully functional offline with zero mandatory dependencies.
* **[HowlPlane](https://github.com/howlcipher/howlplane):** AI engineering control plane.
* **[HowlChangeOps](https://github.com/howlcipher/howlchangeops):** Policy-driven release authority and verification boundary.
* **[HowlWriter](https://github.com/howlcipher/howlwriter):** Citation, provenance, and verification system.

---

## Architecture

```text
               +-------------------------------------------+
               |             HowlRelay CLI                 |
               |     (status | handoff | brief)            |
               +---------------------+---------------------+
                                     |
                       +-------------v-------------+
                       |   Handoff Engine / Core   |
                       | - Anti-Surveillance Gate  |
                       | - Meeting Recommendation  |
                       | - Provenance & Envelope   |
                       +-------------+-------------+
                                     |
        +----------------------------+----------------------------+
        |                            |                            |
+-------v--------+          +--------v---------+         +--------v--------+
|   Git Adapter  |          | Continuity Docs  |         |  Test Runner    |
| (branch, diff, |          | (PROJECT_STATE,  |         | (pytest, junit, |
|  log, status)  |          |  HANDOFF, ADRs)  |         |  exit codes)    |
+----------------+          +------------------+         +-----------------+
```

---

## Dogfooding Experiment

HowlRelay is developed using its own principles from day one:
1. Every engineering session appends to `JOURNAL.md`.
2. Every session passes the baton via an authoritative `HANDOFF.md`.
3. HowlRelay generates handoffs for **its own repository**, comparing the output against manual handoff documents to continuously refine accuracy and completeness.

---

## Current Project Maturity

- **Current Status:** Pre-Alpha / Experimental (Milestones 0 & 1).
- **Implemented:** Core local Git, continuity doc, and test evidence adapters; normalized WorkState and HandoffEnvelope domain models; evidence-grounded meeting recommendation engine; CLI commands (`status`, `handoff`, `brief`).
- **Upcoming:** HowlFrame policy binding, GitHub PR/Issue adapters, distributed work health analytics.

---

## Installation & Development

```bash
# Clone the repository
git clone https://github.com/howlcipher/howlrelay.git
cd howlrelay

# Create virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
flake8 src tests
```

---

## License

[MIT](LICENSE) Copyright (c) 2026 HowlCipher

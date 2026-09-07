# Current Handoff

## Objective
Build and launch HowlRelay: an async-first coordination and handoff system for distributed engineering teams. Deliver Milestone 0 (foundation, packaging, CI) and Milestone 1 (Evidence-Based Async Handoffs v1).

## Current State
Milestones 0, 1, 2, GitHub Pages integration, and Cross-Repo Dogfooding Enhancements are complete:
- GitHub repository created: `howlcipher/howlrelay`.
- Full package structure implemented in `src/howlrelay`.
- 28 unit, integration, and documentation tests passing (`pytest`).
- Zero lint issues (`flake8 src tests`).
- CLI commands implemented: `howlrelay status`, `howlrelay handoff`, `howlrelay brief`.
- Self-dogfooding verified on `howlrelay` itself with epistemic provenance.
- Cross-repo dogfooding verified against `howlcipher/howlcreate`.
- Deep architectural diff analysis with layer breakdown and symbol extraction (Milestone 2 / ADR-0006).
- Test parity risk detection (alerts when core logic is touched without tests).
- Blocker staleness heuristics and meeting recommendation triggers (Milestone 2 / ADR-0006).

## Last Completed Work
- Implemented `analyze_diff` in `GitCollector`: categorizes changes into architectural layers (`core`, `tests`, `docs`, `config`), extracts modified symbol headers (`def`, `class`), and evaluates test parity risk.
- Implemented `compute_blocker_staleness` in `GitCollector`: queries commit history to determine commit age of blockers and mark stale status.
- Enhanced `MeetingReasoningEngine`: triggers synchronous meeting recommendations on stale or critical blockers with inspectable triggers.
- Surfaced test parity risk in `HandoffEngine` and rendered architectural layer diff summaries and stale badges in markdown reports.
- Recorded ADR-0006 in `DECISIONS.md`.
- Added unit tests in `tests/test_adapters.py` and `tests/test_meeting_reasoning.py`.

## Important Decisions
- **Measure the work system, not the worker:** Strict prohibition on keystroke, mouse, camera, presence, or idle surveillance (ADR-0001).
- **Local-first & deterministic:** Core handoffs and status work offline from Git and local artifacts without mandatory LLMs or external databases (ADR-0002).
- **Inspectable Meeting-Required Reasoning:** Four discrete states (`NOT_REQUIRED`, `RECOMMENDED`, `REQUIRES_HUMAN_DECISION`, `INSUFFICIENT_EVIDENCE`) backed by concrete triggers (ADR-0003).
- **Clean HowlFrame boundary:** Integrates with HowlFrame policies when present, gracefully falls back when absent (ADR-0004).
- **Heterogeneous continuity parsing:** Code-fence aware markdown extraction, synonym maps, and non-surveillance codebase grounding (ADR-0005).
- **Deep Architectural Diff & Blocker Staleness:** Non-surveilling work-system signals via unified diff hunks, symbol extraction, test parity risk, and commit-age decay (ADR-0006).

## Files / Components Involved
- `src/howlrelay/adapters/git.py`
- `src/howlrelay/engine.py`
- `src/howlrelay/model.py`
- `src/howlrelay/reasoning/meeting.py`
- `src/howlrelay/renderers/markdown.py`
- `tests/test_adapters.py`
- `tests/test_meeting_reasoning.py`
- `DECISIONS.md`
- `PROJECT_STATE.md`
- `JOURNAL.md`
- `HANDOFF.md`

## Verification Performed
- `pytest -v` -> 28 passed in 0.77s.
- `flake8 src tests` -> clean (exit code 0).
- `howlrelay status --repo /var/home/howlcipher/howlcreate` -> correctly extracted objective, completed work, active work, and status.
- `howlrelay handoff --repo /var/home/howlcipher/howlcreate` -> verified exact starting commands and key files extraction.
- `howlrelay brief --repo /var/home/howlcipher/howlcreate` -> verified clean team brief without activity theater.
- `howlrelay handoff --repo /run/media/system/tallgeese/dev/howlrelay` -> verified self-dogfooding with deep diff and epistemic provenance.

## Known Failures
None.

## Blockers
None.

## Next Recommended Action
1. Begin Milestone 3:
   - Compile and verify a native HowlFrame policy artifact (`.howl` / `.hfbc`) for HowlRelay handoff approval.
2. Advance Milestone 4:
   - GitHub PR, Issue, and CI evidence collector adapter via `gh` CLI.

## Exact Starting Commands
```bash
cd /run/media/system/tallgeese/dev/howlrelay
source .venv/bin/activate
git status
pytest -v
flake8 src tests
howlrelay handoff --run-tests
```

## Context the Next Agent Must Not Lose
- Grounding: Never fabricate missing information. "Unknown" is strictly preferred over guessed data.
- Distinguish between observed facts, inferred state, missing information, and recommendations.
- Keep HowlRelay loosely coupled to HowlFrame so it works out of the box on standard developer machines.

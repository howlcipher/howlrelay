# Current Handoff

## Objective
Build and launch HowlRelay: an async-first coordination and handoff system for distributed engineering teams. Deliver Milestone 0 (foundation, packaging, CI) and Milestone 1 (Evidence-Based Async Handoffs v1).

## Current State
Milestones 0, 1, GitHub Pages integration, and Cross-Repo Dogfooding Enhancements are complete:
- GitHub repository created: `howlcipher/howlrelay`.
- Full package structure implemented in `src/howlrelay`.
- 24 unit, integration, and documentation tests passing (`pytest`).
- Zero lint issues (`flake8 src tests`).
- CLI commands implemented: `howlrelay status`, `howlrelay handoff`, `howlrelay brief`.
- Self-dogfooding verified on `howlrelay` itself with epistemic provenance.
- Cross-repo dogfooding verified against `howlcipher/howlcreate`.
- CI workflow established in `.github/workflows/ci.yml`.
- Public GitHub Pages site deployed under `docs/` using Howl design tokens.

## Last Completed Work
- Implemented heterogeneous continuity parsing supporting numbered headings and heading synonyms (ADR-0005).
- Implemented code-fence isolation so code comments inside bash blocks do not trigger markdown section splits (ADR-0005).
- Implemented canonical file audit checking standard subdirectories (`docs/journal`, `docs/adr`) before declaring files missing.
- Added discovery of creative dogfood artifacts (`dogfood/*.json`, `dogfood/*.md`).
- Added HEAD modified files and key files fallback when working tree is clean.
- Fixed porcelain status parser leading-whitespace stripping in `_run_git`, preserving column alignment, correct staging detection, and rename parsing.
- Added reproduction and regression tests in `tests/test_adapters.py`.
- Verified end-to-end `howlrelay status`, `howlrelay handoff`, and `howlrelay brief` against `howlcipher/howlcreate`.

## Important Decisions
- **Measure the work system, not the worker:** Strict prohibition on keystroke, mouse, camera, presence, or idle surveillance (ADR-0001).
- **Local-first & deterministic:** Core handoffs and status work offline from Git and local artifacts without mandatory LLMs or external databases (ADR-0002).
- **Inspectable Meeting-Required Reasoning:** Four discrete states (`NOT_REQUIRED`, `RECOMMENDED`, `REQUIRES_HUMAN_DECISION`, `INSUFFICIENT_EVIDENCE`) backed by concrete triggers (ADR-0003).
- **Clean HowlFrame boundary:** Integrates with HowlFrame policies when present, gracefully falls back when absent (ADR-0004).
- **Heterogeneous continuity parsing:** Code-fence aware markdown extraction, synonym maps, and non-surveillance codebase grounding (ADR-0005).

## Files / Components Involved
- `src/howlrelay/adapters/continuity.py`
- `src/howlrelay/adapters/git.py`
- `src/howlrelay/engine.py`
- `tests/test_adapters.py`
- `DECISIONS.md`
- `PROJECT_STATE.md`
- `JOURNAL.md`
- `HANDOFF.md`

## Verification Performed
- `pytest -v` -> 24 passed in 0.72s.
- `flake8 src tests` -> clean (exit code 0).
- `howlrelay status --repo /var/home/howlcipher/howlcreate` -> correctly extracted objective, completed work, active work, and status.
- `howlrelay handoff --repo /var/home/howlcipher/howlcreate` -> verified exact starting commands and key files extraction.
- `howlrelay brief --repo /var/home/howlcipher/howlcreate` -> verified clean team brief without activity theater.

## Known Failures
None.

## Blockers
None.

## Next Recommended Action
1. Begin Milestone 2 enhancements:
   - Deep git diff-summary heuristics in `status` and `brief`.
   - Blocker age tracking and dependency staleness detection.
2. Advance Milestone 3:
   - Implement native HowlFrame policy artifact (`.howl` / `.hfbc`) for handoff approval verification.
3. Advance Milestone 4:
   - GitHub PR and Issue adapter via `gh` CLI.

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

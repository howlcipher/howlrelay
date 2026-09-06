# HowlRelay Engineering Journal

Append-only record of engineering sessions, decisions, verifications, and progress.

---

## 2026-09-06 — Session 01: Project Inception & Foundation Setup

### Goal
Initialize the `howlcipher/howlrelay` repository, establish the core architectural foundation, anti-surveillance principles, continuity documentation, test harness, and implement Milestone 1: Evidence-Based Async Handoffs v1.

### Starting State
- No `howlrelay` repository existed locally or on GitHub.
- Inspected existing Howl ecosystem repositories:
  - `howlcipher/howlframe` (Go, bytecode VM, capability-bounded execution, intent is not authority)
  - `howlcipher/howlplane` (Python/Go AI engineering control plane)
  - `howlcipher/changeops` (Go/HowlFrame release controller and approval gate)
  - `howlcipher/howlwriter` (Python writing/citation/verification tool)
- Environment verified: Python 3.14.4, `git`, `gh` CLI authenticated as `howlcipher`, `howlframe` binary at `/home/howlcipher/.local/bin/howlframe`.

### Work Completed
1. Created GitHub repository `howlcipher/howlrelay` via `gh repo create`.
2. Initialized local git repository at `/run/media/system/tallgeese/dev/howlrelay` with `main` branch and linked remote `origin`.
3. Created Python virtual environment (`.venv`) and installed core dependencies: `pydantic` (v2), `pyyaml`, `pytest`, `flake8`.
4. Created project configuration:
   - `pyproject.toml` (standard build, console script `howlrelay`, pytest & flake8 configs)
   - `.flake8` (max-line-length = 100)
   - `.gitignore`
   - `LICENSE` (MIT License)
   - `.github/workflows/ci.yml` (multi-version Python test matrix 3.10-3.13, linting, CLI verification, dogfooding)
5. Established mandatory continuity files:
   - `AGENTS.md`: Operating protocol, anti-surveillance rules, session lifecycle.
   - `PROJECT_STATE.md`: Active snapshot and immediate priorities.
   - `ROADMAP.md`: Milestones 0 to 5.
   - `DECISIONS.md`: ADR-0001 through ADR-0004.
   - `JOURNAL.md`: This file.
   - `HANDOFF.md`: Current baton pass.
6. Implemented core package modules:
   - `howlrelay.policy`: Anti-surveillance enforcement, prohibited signal definitions, sanitizers.
   - `howlrelay.model`: Strongly typed Pydantic v2 domain models (`WorkState`, `Evidence`, `Decision`, `Blocker`, `Risk`, `MeetingRecommendation`, `HandoffEnvelope`).
   - `howlrelay.adapters.base`: Base adapter interface.
   - `howlrelay.adapters.git`: Git working tree, commit log, diff, and branch evidence collector.
   - `howlrelay.adapters.continuity`: Parser for canonical markdown continuity files.
   - `howlrelay.adapters.test_runner`: Test framework detection, cache inspection, and live test runner.
   - `howlrelay.adapters.howlframe`: HowlFrame toolchain and policy detector with graceful fallback.
   - `howlrelay.reasoning.meeting`: Grounded meeting-required recommendation engine (`NOT_REQUIRED`, `RECOMMENDED`, `REQUIRES_HUMAN_DECISION`, `INSUFFICIENT_EVIDENCE`).
   - `howlrelay.engine`: Core coordinator orchestrating collectors and producing epistemic partitions.
   - `howlrelay.renderers`: Markdown, JSON, and YAML renderers.
   - `howlrelay.cli.main`: CLI entrypoints for `status`, `handoff`, and `brief`.
7. Created comprehensive unit and integration test suite (21 tests in `tests/` across policy, models, reasoning, adapters, and CLI).
8. Conducted dogfooding experiment: Ran `howlrelay handoff --run-tests` on `howlrelay` itself.

### Decisions
- Adopted strict anti-surveillance policy: reject/filter all keystroke, mouse, screenshot, presence, and idle tracking (ADR-0001).
- Chose Python 3.10+ with Pydantic v2 and PyYAML for structured, deterministic local-first execution without external network or LLM dependency (ADR-0002).
- Designed 4-state meeting-required reasoning engine: `NOT_REQUIRED`, `RECOMMENDED`, `REQUIRES_HUMAN_DECISION`, `INSUFFICIENT_EVIDENCE` (ADR-0003).
- Established loose coupling with HowlFrame runtime with graceful degradation (ADR-0004).

### Verification
- `pytest -v` executed with 21 passing tests.
- `flake8 src tests` executed with 0 errors/warnings.
- `howlrelay status`, `howlrelay handoff`, and `howlrelay brief` executed with clean outputs in markdown, json, and yaml.
- `howlrelay handoff --run-tests` successfully executed pytest in bounded mode, captured test run evidence (21 passed), and incorporated it into the handoff envelope.

### Dogfooding Observations
- Running `howlrelay handoff` against itself accurately discovered:
  1. All 14 uncommitted files and listed them under `Files & Components Involved`.
  2. All 4 ADRs from `DECISIONS.md` with status and rationale.
  3. All completed and active items from `HANDOFF.md` and `PROJECT_STATE.md`.
  4. Correct meeting recommendation `NOT_REQUIRED` with grounded triggers (`all_decisions_resolved`, `no_active_blockers`).
  5. Correct test verification status `PASSED` when `--run-tests` was enabled.
- Discrepancy observed: Manual handoffs tend to include prose narrative while generated handoffs are cleanly partitioned into facts, inferred state, and missing info. This is a desirable property that reduces ambiguous narrative in favor of grounded state.

### Problems Discovered
- Flake8 requires `.flake8` file to respect `max-line-length = 100` instead of reading `pyproject.toml` directly. Created `.flake8` and adjusted line formatting.
- System python3 lacked pip package; virtual environment `python3 -m venv .venv` resolved it cleanly.

### Remaining Work
- Progress to Milestone 2 enhancements (deep diff heuristics, blocker staleness tracking).
- Implement Milestone 3 HowlFrame policy artifact (.howl / .hfbc).
- Explore Milestone 4 GitHub adapter.

### Commits & CI Run
- Commit: `2c23b7a` - `feat: initial release of HowlRelay with Evidence-Based Async Handoffs v1`
- Remote Branch: `origin/main` (https://github.com/howlcipher/howlrelay)
- GitHub Actions CI Run: `34050072936` (All matrix jobs passed: Python 3.10, 3.11, 3.12, 3.13)

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

---

## Session 2: 2026-09-06T21:00:00-04:00 (Ecosystem Integration & GitHub Pages)

### Goal
Implement public GitHub Pages site for HowlRelay using the canonical Howl ecosystem design language, integrate with Howl hub directory, and verify assets and tests.

### Work Completed
1. Created `docs/` static GitHub Pages portal:
   - `docs/index.html`: Fully featured responsive site covering Problem Statement (meeting saturation & surveillance creep), Capabilities, Continuity Model (Journal/Handoff/State), Architecture & HowlPlane relationship, Anti-Surveillance Policy table, and CLI usage.
   - `docs/style.css`: Reusable Howl retro-futurist design system with theme toggle (dark/light), typography, and navigation drawer.
   - `docs/script.js`: Theme persistence and mobile drawer handling.
   - `docs/favicon.svg` & `docs/favicon.png`: Dedicated "HR" emblem with cyan accent.
   - `docs/social-preview.svg` & `docs/social-preview.png`: 1200x630 card with flow diagrams.
2. Added `tests/test_docs.py`: Automated pytest suite verifying asset existence, section anchors, and ecosystem navigation links.
3. Configured GitHub Pages deployment from `main:/docs`.

### Verification
- `pytest -v` -> 23 passed in 1.94s.
- `flake8 src tests` -> 0 errors/warnings.

---

## Session 3: 2026-09-06T21:40:00-04:00 (Cross-Repository Dogfood & Heterogeneous Parsing)

### Goal
Dogfood HowlRelay against sibling repository `howlcipher/howlcreate`. Identify and resolve handoff and coordination failures, and ensure transferable async state between repositories.

### Starting State
- HowlRelay: 23 tests passing, clean flake8, commit `84ac5c2`.
- HowlCreate: 35 tests passing, actively running Dogfood Target 3 (`run-3c13e4f4` exploring cross-repo dogfooding via local Ollama).

### Problems Discovered & Coordination Limitations
1. **Header Parsing Fragility**: Running `howlrelay handoff --repo ../howlcreate` reported `Unknown objective`, `Completed Work: None explicitly recorded`, and `Active Work: No active items tracked`. `ContinuityCollector` strictly matched unnumbered exact headers (`#+ Objective`), failing on numbered headers (`## 1. System Summary`, `## 2. What Works Right Now`) and synonyms.
2. **Code-Fence Interference**: A code comment `# Run all tests` inside a fenced bash block was treated as a Markdown header boundary, truncating extracted starting commands.
3. **Subdirectory Invisibility**: `docs/journal/` was ignored by canonical file audits, wrongly declaring `JOURNAL.md` missing.
4. **Clean Worktree Context Loss**: In a clean Git working tree, `files_involved` was empty, omitting key files documented in continuity or touched by HEAD commit.

### Work Completed
1. Created reproduction test `test_continuity_collector_heterogeneous_formats` in `tests/test_adapters.py`.
2. Reimplemented `_extract_markdown_section` with code-fence awareness, preventing comment lines inside fenced blocks from triggering header breaks.
3. Added `_extract_section_by_synonyms` covering standard variations for Objective/Summary, Completed Work, Active Work, Starting Commands, Key Files, and Blockers.
4. Extended canonical file audit to check `docs/`, `.github/`, and subdirectories (`docs/journal`, `docs/adr`).
5. Added discovery of creative dogfood artifacts (`dogfood/*.json`, `dogfood/*.md`).
6. Added `head_modified_files` extraction to `GitCollector` and updated `HandoffEngine` to surface key files and HEAD modified files when the working tree is clean.
7. Recorded ADR-0005.

### Verification
- `pytest -v` -> 24 passed in 0.72s.
- `flake8 src tests` -> 0 errors/warnings.
- Real dogfood on `howlcreate`:
  - `howlrelay status --repo /var/home/howlcipher/howlcreate` correctly extracts Objective, Completed Work (17 items), Active Work (7 items), Next Actions, and High confidence.
  - `howlrelay handoff --repo /var/home/howlcipher/howlcreate` extracts all starting commands and 13 key files.
  - `howlrelay brief --repo /var/home/howlcipher/howlcreate` produces crisp, grounded executive summary.

---

## Session 4: 2026-09-06T21:43:00-04:00 (Porcelain Parsing & Whitespace Integrity)

### Goal
Resolve filename truncation and false-staging bug identified during live cross-repository inspection of `howlcipher/howlcreate`.

### Problems Discovered
1. **Porcelain Leading-Whitespace Truncation**: When running `howlrelay handoff --repo /var/home/howlcipher/howlcreate`, the first modified file appeared as `rc/howlcreate/engine/convergence.py` under staged files instead of `src/howlcreate/engine/convergence.py` under modified files.
2. **Root Cause**: `GitCollector._run_git` called `.strip()` on command output. In `git status --porcelain`, an unstaged modification begins with a leading space (`" M filename"`). Stripping the entire output stripped that leading space, converting `" M src/..."` to `"M src/..."`. The parser then inspected index 0 (`"M"`), concluded the file was staged, and extracted the filename from index 3 (`"rc/..."`).

### Work Completed
1. Updated `GitCollector._run_git` to use `.rstrip("\r\n")` rather than `.strip()`, preserving column-aligned leading whitespace.
2. Added defensive column index checks and rename handling (`"old -> new"` extraction) to `GitCollector.collect`.
3. Added unit test `test_git_collector_porcelain_parsing` in `tests/test_adapters.py`.

### Verification
- `pytest -v` -> 25 passed in 0.71s.
- `flake8 src tests` -> 0 errors/warnings.
- Verified on `howlcreate`: files involved accurately reported as `src/howlcreate/...` with 0 staged, 3 unstaged.



# HowlRelay Project State

Authoritative snapshot of project status, architecture, features, and immediate priorities.

---

## Current Milestone
**Milestone 1: Evidence-Based Async Handoffs v1** (Completed) / **Milestone 2: Project Status / Brief Enhancements** (Next)

---

## Current Architecture
- **Language & Runtime:** Python 3.10+ (verified on Python 3.14 locally).
- **Core Libraries:** `pydantic` (v2) for domain typing & schema validation, `pyyaml` for structured YAML interchange.
- **Testing & Verification:** `pytest` (21 tests passing), `flake8` (clean, 0 warnings).
- **Packaging:** Standard `pyproject.toml` with setuptools build-backend and `src/` layout.
- **Entrypoint:** `howlrelay.cli.main:main` (`howlrelay status`, `howlrelay handoff`, `howlrelay brief`).
- **Architectural Patterns:**
  - Strict anti-surveillance boundary & signal filter (`howlrelay.policy`).
  - Pluggable evidence collectors:
    - `GitCollector`: branches, HEAD commit, uncommitted working tree diffs, commit log, remotes.
    - `ContinuityCollector`: ADRs, objectives, blockers, next actions from canonical continuity markdown.
    - `TestCollector`: test framework discovery, pytest cache inspection, live test execution.
    - `HowlFrameCollector`: runtime toolchain discovery, policy discovery, capability model.
  - Epistemic partitioning: observed facts vs inferred state vs missing information vs recommendations.
  - Deterministic meeting recommendation reasoning engine (`MeetingReasoningEngine`).
  - Multi-format rendering: Deterministic Markdown, JSON, YAML.

---

## Implemented Features
- [x] Repository initialization (`howlcipher/howlrelay`) on GitHub and locally.
- [x] Python virtual environment, dependencies, and packaging foundation.
- [x] Continuity infrastructure (`AGENTS.md`, `PROJECT_STATE.md`, `ROADMAP.md`, `JOURNAL.md`, `HANDOFF.md`, `DECISIONS.md`).
- [x] Core domain models with anti-surveillance metadata validation (`howlrelay.model`).
- [x] Anti-surveillance signal sanitizer and policy checker (`howlrelay.policy`).
- [x] Local Git evidence collector (`howlrelay.adapters.git`).
- [x] Continuity document parser & evidence collector (`howlrelay.adapters.continuity`).
- [x] Test discovery & execution collector (`howlrelay.adapters.test_runner`).
- [x] HowlFrame policy adapter with graceful fallback (`howlrelay.adapters.howlframe`).
- [x] Evidence-based meeting recommendation engine (`howlrelay.reasoning.meeting`).
- [x] CLI commands: `howlrelay status`, `howlrelay handoff`, `howlrelay brief` (`howlrelay.cli.main`).
- [x] Structured output rendering: Markdown, formatted JSON, clean YAML (`howlrelay.renderers`).
- [x] GitHub Actions CI workflow for test matrix (3.10, 3.11, 3.12, 3.13) and flake8 linting.
- [x] Heterogeneous continuity parser supporting numbered headings, heading synonyms, code-fence isolation, and subdirectories (ADR-0005).
- [x] Creative dogfood artifacts collector and clean worktree key files fallback.
- [x] Comprehensive test suite (24 unit and integration tests passing).
- [x] Cross-dogfooding verification on sibling repository `howlcipher/howlcreate`.

---

## Incomplete / Next Priorities
- [ ] Milestone 2 enhancements:
  - Deep diff-summary analysis in status/brief.
  - Blocker age tracking and dependency staleness detection.
- [ ] Milestone 3 HowlFrame deep policy:
  - Compile and verify a native `.howl` / `.hfbc` policy for HowlRelay handoff approval.
- [ ] Milestone 4 GitHub integration:
  - PR, Issue, and CI evidence collector adapter via `gh` CLI / GitHub API.

---

## Known Defects
- None.

---

## Known Technical Debt
- Offline Git collector uses subprocess calls to `git`; consideration for `pygit2` or direct object reading if performance on large monorepos demands it later.

---

## Active Integrations
- Local Git repository inspection (`git` CLI).
- Pytest test runner and cache inspection (`.pytest_cache`).
- HowlFrame toolchain integration (`/home/howlcipher/.local/bin/howlframe`).
- Sibling cross-repository dogfooding (`howlcipher/howlcreate`).

---

## Test Counts & Status
- **Test Count:** 24 passing, 0 failing.
- **Lint:** 0 flake8 errors/warnings.
- **Execution Time:** ~0.7s.

---

## Important Commands
```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
flake8 src tests
howlrelay status
howlrelay handoff
howlrelay handoff --run-tests
howlrelay brief
```

---

## Immediate Priorities
1. Commit and push Milestone 0 & 1 foundations to GitHub (`origin/main`).
2. Verify GitHub Actions CI triggers and passes.
3. Compare dogfood-generated handoff with manual `HANDOFF.md`.
4. Progress toward Milestone 2 / 3 capabilities.

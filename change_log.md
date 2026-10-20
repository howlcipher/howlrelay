# Changelog

## Unreleased

- Howl interop contract: `howlrelay interop --json` prints the `howl.interop/v1` descriptor. HowlDream envelopes are read only when `schema_version` is `howl.exploration_result/v1` (what HowlDream writes); any other shape is skipped and reported instead of read field by field. HowlProof's `howlproof-handoff.md` (`howlproof handoff --for relay`) is used when there is no `HANDOFF.md`. The HowlFrame probe runs the documented `howlframe --version` instead of `-help`. `generator_version` follows the package version. Python 3.11 is required, like the rest of the ecosystem.

- Support the documented `--json` and `--yaml` output shortcuts on status, handoff, and brief. Conflicting format options fail with an actionable usage error.

"""The ``howl.interop/v1`` descriptor printed by ``howlrelay interop --json``.

HowlRelay runs no other Howl component's command line: it reads HowlDream
exploration envelopes and continuity files (including HowlProof's
``howlproof-handoff.md``) off disk, and asks ``howlframe --version`` only to report
whether HowlFrame is present. Contract:
https://github.com/howlcipher/howl/blob/main/docs/INTEROP.md
"""

import argparse
from typing import Any, Dict, List

from howlrelay import __version__
from howlrelay.adapters.howldream import SUPPORTED_ENVELOPE_SCHEMAS

SCHEMA = "howl.interop/v1"

EXIT_CODES = {
    "0": "ok",
    "1": "error (the repository path does not exist, or inspection failed)",
    "2": "usage error",
}


def _flags(parser: argparse.ArgumentParser) -> List[str]:
    return sorted(o for a in parser._actions for o in a.option_strings if o not in ("-h", "--help"))


def describe(parser: argparse.ArgumentParser) -> Dict[str, Any]:
    commands: List[Dict[str, Any]] = [{"path": [], "flags": _flags(parser), "json": False}]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                flags = _flags(sub)
                entry: Dict[str, Any] = {"path": [name], "flags": flags, "json": "--json" in flags}
                if name in ("status", "handoff", "brief"):
                    entry["accepts"] = list(SUPPORTED_ENVELOPE_SCHEMAS)
                if name == "interop":
                    entry["emits"] = [SCHEMA]
                commands.append(entry)
    return {
        "schema": SCHEMA,
        "component": "howlrelay",
        "version": __version__,
        "commands": commands,
        "exit_codes": EXIT_CODES,
        "env": ["HOWLDREAM_BIN"],
        "consumes": [{"component": "howlframe", "command": [], "flags": ["--version"]}],
    }

"""Main CLI entrypoint for HowlRelay.

Provides commands:
  howlrelay status   - What is the current state of this project or workstream?
  howlrelay handoff  - What does another engineer or agent need to continue this work?
  howlrelay brief    - What does the broader team need to know without a status meeting?
"""

import argparse
from pathlib import Path
import sys
from typing import Optional

from howlrelay import __version__
from howlrelay.engine import HandoffEngine
from howlrelay.renderers.json_yaml import render_json, render_yaml
from howlrelay.renderers.markdown import render_brief, render_handoff, render_status


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="howlrelay",
        description=(
            "HowlRelay: Async-first coordination and handoff system for distributed "
            "engineering teams."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # Command: status
    parser_status = subparsers.add_parser(
        "status",
        help="Inspect and display current project workstream status.",
    )
    parser_status.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path to repository to inspect (default: current directory).",
    )
    parser_status.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser_status.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: stdout).",
    )

    # Command: handoff
    parser_handoff = subparsers.add_parser(
        "handoff",
        help="Generate grounded asynchronous handoff for an engineer or AI agent.",
    )
    parser_handoff.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path to repository to inspect (default: current directory).",
    )
    parser_handoff.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser_handoff.add_argument(
        "--update-handoff",
        action="store_true",
        help="Write generated handoff directly to HANDOFF.md in the repository root.",
    )
    parser_handoff.add_argument(
        "--run-tests",
        action="store_true",
        help="Run pytest verification during handoff collection.",
    )
    parser_handoff.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: stdout).",
    )

    # Command: brief
    parser_brief = subparsers.add_parser(
        "brief",
        help="Generate a concise, anti-activity-theater status brief for the broader team.",
    )
    parser_brief.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path to repository to inspect (default: current directory).",
    )
    parser_brief.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser_brief.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: stdout).",
    )

    return parser.parse_args(args)


def write_output(content: str, output_path: Optional[Path]) -> None:
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"Wrote output to {output_path}")
    else:
        print(content)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)
    if not args.command:
        # Default behavior: show help if no subcommand provided
        parse_args(["--help"])
        return 0

    engine = HandoffEngine()
    repo_path = args.repo.resolve()

    if not repo_path.exists():
        sys.stderr.write(f"Error: Target repository path does not exist: {repo_path}\n")
        return 1

    try:
        run_tests = getattr(args, "run_tests", False)
        envelope = engine.inspect_repo(repo_path, run_tests=run_tests)

        if args.command == "status":
            if args.format == "json":
                out = render_json(envelope.work_state)
            elif args.format == "yaml":
                out = render_yaml(envelope.work_state)
            else:
                out = render_status(envelope.work_state)
            write_output(out, args.output)

        elif args.command == "handoff":
            if args.format == "json":
                out = render_json(envelope)
            elif args.format == "yaml":
                out = render_yaml(envelope)
            else:
                out = render_handoff(envelope)

            if getattr(args, "update_handoff", False):
                handoff_path = repo_path / "HANDOFF.md"
                write_output(out, handoff_path)
            else:
                write_output(out, args.output)

        elif args.command == "brief":
            if args.format == "json":
                out = render_json(envelope.work_state)
            elif args.format == "yaml":
                out = render_yaml(envelope.work_state)
            else:
                out = render_brief(envelope.work_state)
            write_output(out, args.output)

        return 0

    except Exception as ex:
        sys.stderr.write(f"Error executing howlrelay {args.command}: {ex}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

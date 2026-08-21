"""Command line entry point for histfmt."""

import argparse
import sys
from typing import List, Optional

from .formatter import dedupe, to_human, to_json
from .parser import parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="histfmt",
        description="Normalise a messy shell history file into a readable or JSON stream.",
    )
    parser.add_argument(
        "histfile",
        nargs="?",
        help="path to a history file, defaults to stdin",
    )
    parser.add_argument(
        "--format",
        choices=["zsh-extended", "plain", "fish"],
        help="force a source format instead of auto-detecting it",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a JSON array instead of the human-readable listing",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="keep consecutive duplicate commands instead of collapsing them",
    )
    return parser


def read_lines(path: Optional[str]) -> List[str]:
    if path is None:
        return sys.stdin.readlines()
    with open(path, "r", errors="replace") as handle:
        return handle.readlines()


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    lines = read_lines(args.histfile)
    entries = parse(lines, fmt=args.format)
    if not args.no_dedupe:
        entries = dedupe(entries)
    output = to_json(entries) if args.json else to_human(entries)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())

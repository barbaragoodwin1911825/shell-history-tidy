"""Command line entry point for histfmt."""

import argparse
import os
import re
import sys
from typing import List, Optional

from .formatter import DEFAULT_TIME_FORMAT, dedupe, filter_entries, merge_entries, to_human, to_json
from .parser import parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="histfmt",
        description="Normalise a messy shell history file into a readable or JSON stream.",
    )
    parser.add_argument(
        "histfile",
        nargs="*",
        help="path to a history file, defaults to stdin; pass more than one "
        "to merge them into a single timeline sorted by timestamp",
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
    parser.add_argument(
        "--time-format",
        metavar="STRFTIME",
        help="strftime pattern for timestamps in the human-readable listing "
        "(defaults to the HISTTIMEFORMAT environment variable if it is set, "
        "otherwise '%%Y-%%m-%%d %%H:%%M:%%S'); has no effect on --json output",
    )
    parser.add_argument(
        "--filter",
        metavar="PATTERN",
        help="only show commands containing PATTERN (substring match, or a "
        "regex if --regex is given)",
    )
    parser.add_argument(
        "--regex",
        action="store_true",
        help="treat --filter's PATTERN as a regular expression instead of a "
        "plain substring",
    )
    return parser


def read_lines(path: Optional[str]) -> List[str]:
    if path is None:
        return sys.stdin.readlines()
    with open(path, "r", errors="replace") as handle:
        return handle.readlines()


def main(argv: Optional[List[str]] = None) -> int:
    arg_parser = build_parser()
    args = arg_parser.parse_args(argv)
    if args.regex and not args.filter:
        arg_parser.error("--regex has no effect without --filter")
    if not args.histfile:
        entries = parse(read_lines(None), fmt=args.format)
    elif len(args.histfile) == 1:
        entries = parse(read_lines(args.histfile[0]), fmt=args.format)
    else:
        entries = merge_entries(parse(read_lines(path), fmt=args.format) for path in args.histfile)
    if not args.no_dedupe:
        entries = dedupe(entries)
    if args.filter:
        try:
            entries = filter_entries(entries, args.filter, regex=args.regex)
        except re.error as exc:
            arg_parser.error(f"invalid --filter regex: {exc}")
    if args.json:
        output = to_json(entries)
    else:
        time_format = args.time_format or os.environ.get("HISTTIMEFORMAT") or DEFAULT_TIME_FORMAT
        output = to_human(entries, time_format=time_format)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())

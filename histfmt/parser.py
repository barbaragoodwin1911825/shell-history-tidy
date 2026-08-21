"""Parsers for the shell history formats I actually run into.

Bash writes plain lines (optionally preceded by a `#<epoch>` comment when
HISTTIMEFORMAT is set). Zsh's extended history prefixes each command with
`: <start>:<duration>;`. Fish writes a small YAML-like block per command.
None of these are documented as a stable format, so the regexes here are
based on reading actual history files, not a spec.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, List, Optional


@dataclass
class HistoryEntry:
    command: str
    timestamp: Optional[int] = None
    duration: Optional[int] = None


_ZSH_EXTENDED_RE = re.compile(r"^: (?P<ts>\d+):(?P<dur>\d+);(?P<cmd>.*)$")
_BASH_TIMESTAMP_RE = re.compile(r"^#(?P<ts>\d+)$")
_FISH_CMD_RE = re.compile(r"^- cmd:\s?(?P<cmd>.*)$")
_FISH_WHEN_RE = re.compile(r"^\s+when:\s?(?P<ts>\d+)$")


def detect_format(lines: List[str]) -> str:
    """Guess which history format a set of lines came from.

    Checks the first format-specific marker found, since plain bash
    history has no marker at all and would otherwise match everything.
    """
    for line in lines:
        if _ZSH_EXTENDED_RE.match(line):
            return "zsh-extended"
        if _FISH_CMD_RE.match(line):
            return "fish"
    return "plain"


def parse_zsh_extended(lines: Iterator[str]) -> Iterator[HistoryEntry]:
    pending: Optional[HistoryEntry] = None
    for raw in lines:
        line = raw.rstrip("\n")
        match = _ZSH_EXTENDED_RE.match(line)
        if match:
            if pending is not None:
                yield pending
            pending = HistoryEntry(
                command=match.group("cmd"),
                timestamp=int(match.group("ts")),
                duration=int(match.group("dur")),
            )
        elif pending is not None:
            # a continuation of a multi-line command that zsh split on
            # the trailing backslash it wrote when saving the entry
            pending.command += "\n" + line
    if pending is not None:
        yield pending


def parse_plain(lines: Iterator[str]) -> Iterator[HistoryEntry]:
    pending_ts: Optional[int] = None
    for raw in lines:
        line = raw.rstrip("\n")
        if not line:
            continue
        ts_match = _BASH_TIMESTAMP_RE.match(line)
        if ts_match:
            pending_ts = int(ts_match.group("ts"))
            continue
        yield HistoryEntry(command=line, timestamp=pending_ts)
        pending_ts = None


def parse_fish(lines: Iterator[str]) -> Iterator[HistoryEntry]:
    pending: Optional[HistoryEntry] = None
    for raw in lines:
        line = raw.rstrip("\n")
        cmd_match = _FISH_CMD_RE.match(line)
        if cmd_match:
            if pending is not None:
                yield pending
            pending = HistoryEntry(command=cmd_match.group("cmd"))
            continue
        when_match = _FISH_WHEN_RE.match(line)
        if when_match and pending is not None:
            pending.timestamp = int(when_match.group("ts"))
    if pending is not None:
        yield pending


def parse(lines: List[str], fmt: Optional[str] = None) -> List[HistoryEntry]:
    """Parse history lines, auto-detecting the format unless one is given."""
    fmt = fmt or detect_format(lines)
    if fmt == "zsh-extended":
        return list(parse_zsh_extended(iter(lines)))
    if fmt == "fish":
        return list(parse_fish(iter(lines)))
    return list(parse_plain(iter(lines)))

"""Render parsed history entries as human-readable text or JSON."""

import json
import re
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from .parser import HistoryEntry

DEFAULT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def filter_entries(
    entries: Iterable[HistoryEntry], pattern: str, regex: bool = False
) -> List[HistoryEntry]:
    """Keep only entries whose command matches `pattern`.

    Plain substring matching by default, since that covers the common case
    of "did I run something with docker in it" without needing to know
    regex syntax. `regex=True` compiles `pattern` and matches with search,
    so the caller doesn't have to anchor it themselves.
    """
    if regex:
        matcher = re.compile(pattern)
        return [entry for entry in entries if matcher.search(entry.command)]
    return [entry for entry in entries if pattern in entry.command]


def merge_entries(entry_lists: Iterable[Iterable[HistoryEntry]]) -> List[HistoryEntry]:
    """Merge entries parsed from several history files into one timeline.

    Sorted by timestamp so interleaved bash/zsh/fish histories from
    different machines line up chronologically instead of just being
    file after file. Entries with no timestamp can't be placed on that
    timeline, so they're pushed to the end, in the order they were
    encountered; `sorted` is stable so ties (including "no timestamp")
    don't reorder entries that were already in the right order.
    """
    merged = [entry for entries in entry_lists for entry in entries]
    return sorted(merged, key=lambda entry: (entry.timestamp is None, entry.timestamp or 0))


def dedupe(entries: Iterable[HistoryEntry]) -> List[HistoryEntry]:
    """Drop consecutive duplicate commands.

    This is the noise that piles up from re-running `ls`, `cd ..`, or a
    failed command a few times in a row. It deliberately only collapses
    consecutive runs, not every repeat in the file, since `git status`
    showing up fifty times across a session is normal and useful.
    """
    result: List[HistoryEntry] = []
    for entry in entries:
        if result and result[-1].command == entry.command:
            continue
        result.append(entry)
    return result


def normalize_command(command: str) -> str:
    """Collapse internal whitespace and strip leading/trailing padding."""
    return " ".join(command.strip().split())


def _format_timestamp(timestamp: Optional[int], time_format: str) -> Optional[str]:
    if timestamp is None:
        return None
    stamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return stamp.strftime(time_format)


def to_human(entries: List[HistoryEntry], time_format: str = DEFAULT_TIME_FORMAT) -> str:
    """Render entries as one line each, timestamp first when one is known.

    `time_format` is a strftime pattern, the same kind of thing bash reads
    from HISTTIMEFORMAT, so a caller can match whatever style they already
    have their shell's `history` command printing.
    """
    lines = []
    for entry in entries:
        command = normalize_command(entry.command)
        stamp = _format_timestamp(entry.timestamp, time_format)
        lines.append(f"{stamp}  {command}" if stamp else command)
    return "\n".join(lines)


def to_json(entries: List[HistoryEntry]) -> str:
    payload = [
        {
            "command": normalize_command(entry.command),
            "timestamp": entry.timestamp,
            "duration": entry.duration,
        }
        for entry in entries
    ]
    return json.dumps(payload, indent=2)

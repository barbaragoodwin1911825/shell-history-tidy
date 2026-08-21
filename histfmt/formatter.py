"""Render parsed history entries as human-readable text or JSON."""

import json
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from .parser import HistoryEntry


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


def _format_timestamp(timestamp: Optional[int]) -> Optional[str]:
    if timestamp is None:
        return None
    stamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return f"{stamp:%Y-%m-%d %H:%M:%S}"


def to_human(entries: List[HistoryEntry]) -> str:
    lines = []
    for entry in entries:
        command = normalize_command(entry.command)
        stamp = _format_timestamp(entry.timestamp)
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

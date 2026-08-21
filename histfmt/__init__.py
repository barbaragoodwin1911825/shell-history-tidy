"""histfmt: normalise shell history files from bash, zsh, and fish."""

from .formatter import dedupe, to_human, to_json
from .parser import HistoryEntry, parse

__version__ = "0.1.0"

__all__ = ["HistoryEntry", "parse", "dedupe", "to_human", "to_json"]

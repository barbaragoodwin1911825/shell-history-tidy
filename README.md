# histfmt

Shell history files are a mess once you actually look at them. Bash writes
plain lines, or `#1690000000`-style comments before each one if
`HISTTIMEFORMAT` is set. Zsh's extended history prefixes every command with
`: 1690000000:0;` (start time and duration). Fish writes a small YAML-like
block per command. If you've ever tried to grep across a history file copied
from a different shell, or feed it into another tool, you've hit this.

`histfmt` reads one of those formats, normalises the whitespace and
duplicate-command noise, and prints either a plain listing or JSON.

## Usage

Point it at a history file:

```
$ histfmt ~/.zsh_history
2023-07-22 09:14:03  git status
2023-07-22 09:14:11  ls -la
2023-07-22 09:15:47  git commit -m "fix off-by-one"
```

Or pipe one in on stdin:

```
$ cat ~/.bash_history | histfmt
git status
ls -la
git commit -m "fix off-by-one"
```

Get JSON instead, e.g. for feeding into `jq` or another script:

```
$ histfmt --json ~/.zsh_history
[
  {
    "command": "git status",
    "timestamp": 1690017243,
    "duration": 0
  },
  {
    "command": "ls -la",
    "timestamp": 1690017251,
    "duration": 0
  }
]
```

Force the source format instead of auto-detecting it, or keep consecutive
duplicate commands instead of collapsing them:

```
$ histfmt --format fish --no-dedupe ~/.local/share/fish/fish_history
```

Change how timestamps are printed in the human-readable listing with
`--time-format`, which takes the same kind of strftime pattern bash reads
from `HISTTIMEFORMAT`. If you already have `HISTTIMEFORMAT` set in your
environment, `histfmt` picks it up automatically so the output matches what
`history` prints for you:

```
$ histfmt --time-format '%H:%M' ~/.bash_history
09:14  git status
09:14  ls -la
```

`--time-format` only affects the human-readable listing; `--json` timestamps
are always the raw epoch seconds so downstream tools don't have to parse a
locale-dependent string.

## Why

I wanted a single normalised view across the three shells I actually use
(bash on servers, zsh locally, fish when I'm poking around), without writing
one-off awk scripts every time. The JSON mode exists so this can sit in front
of something else — a search tool, a stats script — without that thing
needing to know about zsh's history format.

## Installing

No dependencies beyond the standard library.

```
pip install -e .
```

## Status

Early. Bash, zsh extended, and fish history parsing all work, and
`--time-format` covers `HISTTIMEFORMAT`-style custom formats. Things that
don't exist yet are listed in the repo's issues / roadmap: a filtering flag
and merging multiple history files.

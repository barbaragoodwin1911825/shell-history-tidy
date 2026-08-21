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

Early. Bash, zsh extended, and fish history parsing all work. Things that
don't exist yet are listed in the repo's issues / roadmap: multi-file merges,
`HISTTIMEFORMAT`-style custom formats beyond the epoch-comment case, and a
filtering flag.

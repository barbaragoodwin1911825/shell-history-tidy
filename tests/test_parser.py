import unittest

from histfmt.parser import (
    HistoryEntry,
    detect_format,
    parse,
    parse_fish,
    parse_plain,
    parse_zsh_extended,
)


class DetectFormatTests(unittest.TestCase):
    def test_plain_lines_have_no_marker(self):
        lines = ["git status\n", "ls -la\n"]
        self.assertEqual(detect_format(lines), "plain")

    def test_bash_timestamp_comments_still_read_as_plain(self):
        # the #<epoch> comment isn't a format marker on its own, only the
        # zsh and fish prefixes are distinctive enough to key off
        lines = ["#1690000000\n", "git status\n"]
        self.assertEqual(detect_format(lines), "plain")

    def test_zsh_extended_marker(self):
        lines = ["some junk\n", ": 1690000000:0;git status\n"]
        self.assertEqual(detect_format(lines), "zsh-extended")

    def test_fish_marker(self):
        lines = ["- cmd: git status\n", "  when: 1690000000\n"]
        self.assertEqual(detect_format(lines), "fish")

    def test_empty_input_defaults_to_plain(self):
        self.assertEqual(detect_format([]), "plain")


class ParsePlainTests(unittest.TestCase):
    def test_basic_commands(self):
        lines = ["git status\n", "ls -la\n"]
        entries = list(parse_plain(iter(lines)))
        self.assertEqual([e.command for e in entries], ["git status", "ls -la"])
        self.assertTrue(all(e.timestamp is None for e in entries))

    def test_timestamp_comment_attaches_to_next_command_only(self):
        lines = ["#1690000000\n", "git status\n", "ls -la\n"]
        entries = list(parse_plain(iter(lines)))
        self.assertEqual(entries[0], HistoryEntry(command="git status", timestamp=1690000000))
        self.assertEqual(entries[1], HistoryEntry(command="ls -la", timestamp=None))

    def test_blank_lines_are_skipped(self):
        lines = ["git status\n", "\n", "ls -la\n"]
        entries = list(parse_plain(iter(lines)))
        self.assertEqual(len(entries), 2)

    def test_dangling_timestamp_comment_with_no_command_is_dropped(self):
        lines = ["git status\n", "#1690000000\n"]
        entries = list(parse_plain(iter(lines)))
        self.assertEqual(len(entries), 1)
        self.assertIsNone(entries[0].timestamp)


class ParseZshExtendedTests(unittest.TestCase):
    def test_basic_entry(self):
        lines = [": 1690000000:5;git status\n"]
        entries = list(parse_zsh_extended(iter(lines)))
        self.assertEqual(
            entries, [HistoryEntry(command="git status", timestamp=1690000000, duration=5)]
        )

    def test_multiple_entries(self):
        lines = [
            ": 1690000000:0;git status\n",
            ": 1690000011:2;ls -la\n",
        ]
        entries = list(parse_zsh_extended(iter(lines)))
        self.assertEqual([e.command for e in entries], ["git status", "ls -la"])

    def test_continuation_line_is_appended(self):
        # zsh writes a trailing backslash on multi-line commands and the
        # following line has no `: <ts>:<dur>;` prefix at all
        lines = [
            ": 1690000000:0;echo one \\\n",
            "echo two\n",
        ]
        entries = list(parse_zsh_extended(iter(lines)))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].command, "echo one \\\necho two")


class ParseFishTests(unittest.TestCase):
    def test_basic_entry(self):
        lines = ["- cmd: git status\n", "  when: 1690000000\n"]
        entries = list(parse_fish(iter(lines)))
        self.assertEqual(entries, [HistoryEntry(command="git status", timestamp=1690000000)])

    def test_entry_without_when(self):
        lines = ["- cmd: git status\n"]
        entries = list(parse_fish(iter(lines)))
        self.assertEqual(entries, [HistoryEntry(command="git status", timestamp=None)])

    def test_multiple_entries(self):
        lines = [
            "- cmd: git status\n",
            "  when: 1690000000\n",
            "- cmd: ls -la\n",
            "  when: 1690000011\n",
        ]
        entries = list(parse_fish(iter(lines)))
        self.assertEqual([e.command for e in entries], ["git status", "ls -la"])
        self.assertEqual([e.timestamp for e in entries], [1690000000, 1690000011])


class ParseDispatchTests(unittest.TestCase):
    def test_auto_detects_zsh_extended(self):
        lines = [": 1690000000:0;git status\n"]
        entries = parse(lines)
        self.assertEqual(entries, [HistoryEntry(command="git status", timestamp=1690000000, duration=0)])

    def test_auto_detects_fish(self):
        lines = ["- cmd: git status\n", "  when: 1690000000\n"]
        entries = parse(lines)
        self.assertEqual(entries, [HistoryEntry(command="git status", timestamp=1690000000)])

    def test_auto_detects_plain(self):
        lines = ["git status\n"]
        entries = parse(lines)
        self.assertEqual(entries, [HistoryEntry(command="git status")])

    def test_forced_format_overrides_detection(self):
        # this looks like a plain command but forcing zsh-extended means
        # it won't match the prefix regex and yields nothing
        lines = ["git status\n"]
        entries = parse(lines, fmt="zsh-extended")
        self.assertEqual(entries, [])


if __name__ == "__main__":
    unittest.main()

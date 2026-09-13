import json
import unittest

from histfmt.formatter import dedupe, filter_entries, merge_entries, normalize_command, to_human, to_json
from histfmt.parser import HistoryEntry


class FilterEntriesTests(unittest.TestCase):
    def setUp(self):
        self.entries = [
            HistoryEntry(command="git status"),
            HistoryEntry(command="git commit -m fix"),
            HistoryEntry(command="ls -la"),
        ]

    def test_substring_match(self):
        result = filter_entries(self.entries, "git")
        self.assertEqual([e.command for e in result], ["git status", "git commit -m fix"])

    def test_substring_match_is_case_sensitive(self):
        result = filter_entries(self.entries, "GIT")
        self.assertEqual(result, [])

    def test_no_match_is_empty(self):
        result = filter_entries(self.entries, "docker")
        self.assertEqual(result, [])

    def test_regex_match(self):
        result = filter_entries(self.entries, r"^git (status|commit)", regex=True)
        self.assertEqual([e.command for e in result], ["git status", "git commit -m fix"])

    def test_regex_special_chars_are_literal_without_regex_flag(self):
        entries = [HistoryEntry(command="echo a.b"), HistoryEntry(command="echo axb")]
        result = filter_entries(entries, "a.b")
        self.assertEqual([e.command for e in result], ["echo a.b"])

    def test_empty_input(self):
        self.assertEqual(filter_entries([], "git"), [])


class MergeEntriesTests(unittest.TestCase):
    def test_interleaves_by_timestamp(self):
        bash = [HistoryEntry(command="git status", timestamp=1690000000)]
        zsh = [HistoryEntry(command="ls -la", timestamp=1689999999)]
        result = merge_entries([bash, zsh])
        self.assertEqual([e.command for e in result], ["ls -la", "git status"])

    def test_entries_without_timestamp_go_last_in_original_order(self):
        with_ts = [HistoryEntry(command="git status", timestamp=1690000000)]
        without_ts = [HistoryEntry(command="ls -la"), HistoryEntry(command="cd ..")]
        result = merge_entries([without_ts, with_ts])
        self.assertEqual([e.command for e in result], ["git status", "ls -la", "cd .."])

    def test_stable_for_equal_timestamps(self):
        first = [HistoryEntry(command="a", timestamp=100)]
        second = [HistoryEntry(command="b", timestamp=100)]
        result = merge_entries([first, second])
        self.assertEqual([e.command for e in result], ["a", "b"])

    def test_single_list_is_unchanged_when_already_sorted(self):
        entries = [
            HistoryEntry(command="a", timestamp=1),
            HistoryEntry(command="b", timestamp=2),
        ]
        self.assertEqual(merge_entries([entries]), entries)

    def test_empty_input(self):
        self.assertEqual(merge_entries([]), [])
        self.assertEqual(merge_entries([[], []]), [])


class DedupeTests(unittest.TestCase):
    def test_drops_consecutive_duplicates(self):
        entries = [
            HistoryEntry(command="ls"),
            HistoryEntry(command="ls"),
            HistoryEntry(command="git status"),
        ]
        result = dedupe(entries)
        self.assertEqual([e.command for e in result], ["ls", "git status"])

    def test_keeps_non_consecutive_repeats(self):
        entries = [
            HistoryEntry(command="git status"),
            HistoryEntry(command="ls"),
            HistoryEntry(command="git status"),
        ]
        result = dedupe(entries)
        self.assertEqual(len(result), 3)

    def test_empty_input(self):
        self.assertEqual(dedupe([]), [])


class NormalizeCommandTests(unittest.TestCase):
    def test_collapses_internal_whitespace(self):
        self.assertEqual(normalize_command("git   status"), "git status")

    def test_strips_padding(self):
        self.assertEqual(normalize_command("  ls -la  "), "ls -la")

    def test_collapses_tabs_and_newlines(self):
        self.assertEqual(normalize_command("echo one\\\n\techo two"), "echo one\\ echo two")


class ToHumanTests(unittest.TestCase):
    def test_entry_with_timestamp(self):
        entries = [HistoryEntry(command="git status", timestamp=1690000000)]
        self.assertEqual(to_human(entries), "2023-07-22 03:26:40  git status")

    def test_entry_without_timestamp_has_no_leading_stamp(self):
        entries = [HistoryEntry(command="git status")]
        self.assertEqual(to_human(entries), "git status")

    def test_custom_time_format(self):
        entries = [HistoryEntry(command="git status", timestamp=1690000000)]
        self.assertEqual(to_human(entries, time_format="%H:%M"), "03:26  git status")

    def test_multiple_entries_joined_with_newlines(self):
        entries = [
            HistoryEntry(command="git status"),
            HistoryEntry(command="ls -la"),
        ]
        self.assertEqual(to_human(entries), "git status\nls -la")


class ToJsonTests(unittest.TestCase):
    def test_round_trips_entry_fields(self):
        entries = [HistoryEntry(command="git status", timestamp=1690000000, duration=5)]
        payload = json.loads(to_json(entries))
        self.assertEqual(
            payload,
            [{"command": "git status", "timestamp": 1690000000, "duration": 5}],
        )

    def test_missing_timestamp_and_duration_serialise_as_null(self):
        entries = [HistoryEntry(command="git status")]
        payload = json.loads(to_json(entries))
        self.assertIsNone(payload[0]["timestamp"])
        self.assertIsNone(payload[0]["duration"])

    def test_empty_input_is_empty_array(self):
        self.assertEqual(to_json([]), "[]")


if __name__ == "__main__":
    unittest.main()

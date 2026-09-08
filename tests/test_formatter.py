import json
import unittest

from histfmt.formatter import dedupe, normalize_command, to_human, to_json
from histfmt.parser import HistoryEntry


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

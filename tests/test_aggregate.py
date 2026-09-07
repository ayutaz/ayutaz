from __future__ import annotations

import unittest

from profile_stats.aggregate import build_report
from profile_stats.config import Settings
from profile_stats.model import Language, ProfileSnapshot, Repository


class AggregateTests(unittest.TestCase):
    def test_filters_repositories_and_aggregates_languages(self) -> None:
        snapshot = ProfileSnapshot(
            username="ayutaz",
            followers=25,
            repositories=(
                Repository(
                    name="active",
                    is_archived=False,
                    is_private=False,
                    is_fork=False,
                    stars=7,
                    forks=3,
                    languages=(
                        Language("Python", 300, "#3572A5"),
                        Language("C#", 100, "#178600"),
                    ),
                ),
                Repository("archived", True, False, False, 100, 50, (Language("Rust", 900, "#dea584"),)),
                Repository("private", False, True, False, 100, 50, (Language("Go", 900, "#00ADD8"),)),
                Repository("fork", False, False, True, 100, 50, (Language("Java", 900, "#b07219"),)),
                Repository("excluded", False, False, False, 100, 50, (Language("Ruby", 900, "#701516"),)),
            ),
        )
        settings = Settings(
            username="ayutaz",
            exclude_repositories=frozenset({"excluded"}),
            languages_count=2,
        )

        report = build_report(snapshot, settings)

        self.assertEqual(report.stats.active_repositories, 1)
        self.assertEqual(report.stats.stars, 7)
        self.assertEqual(report.stats.forks, 3)
        self.assertEqual(report.stats.followers, 25)
        self.assertEqual(report.stats.language_count, 2)
        self.assertEqual(report.stats.code_bytes, 400)
        self.assertEqual([item.name for item in report.languages], ["Python", "C#"])
        self.assertAlmostEqual(report.languages[0].percentage, 75.0)
        self.assertEqual(
            report.excluded_counts,
            {"archived": 1, "private": 1, "fork": 1, "named": 1},
        )

    def test_language_ties_are_deterministic(self) -> None:
        snapshot = ProfileSnapshot(
            username="ayutaz",
            followers=0,
            repositories=(
                Repository(
                    "active",
                    False,
                    False,
                    False,
                    0,
                    0,
                    (Language("Zig", 100, None), Language("C", 100, "invalid")),
                ),
            ),
        )

        report = build_report(snapshot, Settings(username="ayutaz"))

        self.assertEqual([item.name for item in report.languages], ["C", "Zig"])
        self.assertEqual([item.color for item in report.languages], ["#858585", "#858585"])


if __name__ == "__main__":
    unittest.main()

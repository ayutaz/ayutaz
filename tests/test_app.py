from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from profile_stats.app import generate_assets
from profile_stats.config import Settings
from profile_stats.github import GitHubApiError
from tests.helpers import FakeClient, language, repository, response


class GenerateAssetsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(username="ayutaz", output_directory="assets")
        self.now = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)

    def test_api_failure_preserves_existing_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            stats_path = output / "github-stats.svg"
            stats_path.write_text("last-known-good", encoding="utf-8")
            client = FakeClient([GitHubApiError("network down")])

            with self.assertRaises(GitHubApiError):
                generate_assets(self.settings, client, output, self.now)

            self.assertEqual(stats_path.read_text(encoding="utf-8"), "last-known-good")
            self.assertFalse((output / "top-languages.svg").exists())

    def test_second_identical_generation_does_not_rewrite_files(self) -> None:
        api_response = response(
            [
                repository(
                    "active",
                    stars=2,
                    forks=1,
                    languages=[language("Python", 100, "#3572A5")],
                )
            ],
            followers=3,
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            first = generate_assets(
                self.settings,
                FakeClient([api_response]),
                output,
                self.now,
            )
            original = {
                path.name: path.read_bytes()
                for path in output.iterdir()
                if path.is_file()
            }
            second = generate_assets(
                self.settings,
                FakeClient([api_response]),
                output,
                datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc),
            )

            self.assertTrue(first.changed)
            self.assertFalse(second.changed)
            self.assertEqual(
                original,
                {
                    path.name: path.read_bytes()
                    for path in output.iterdir()
                    if path.is_file()
                },
            )

    def test_missing_asset_is_rebuilt_even_when_digest_matches(self) -> None:
        api_response = response(
            [
                repository(
                    "active",
                    languages=[language("Python", 100, "#3572A5")],
                )
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_assets(
                self.settings,
                FakeClient([api_response]),
                output,
                self.now,
            )
            (output / "top-languages.svg").unlink()

            result = generate_assets(
                self.settings,
                FakeClient([api_response]),
                output,
                datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc),
            )

            self.assertTrue(result.changed)
            self.assertTrue((output / "top-languages.svg").is_file())

    def test_metadata_does_not_publish_repository_names(self) -> None:
        api_response = response(
            [
                repository(
                    "private-project-name",
                    languages=[language("Python", 100, "#3572A5")],
                )
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)

            generate_assets(
                self.settings,
                FakeClient([api_response]),
                output,
                self.now,
            )

            metadata = (output / "stats-metadata.json").read_text(encoding="utf-8")
            self.assertNotIn("private-project-name", metadata)


if __name__ == "__main__":
    unittest.main()

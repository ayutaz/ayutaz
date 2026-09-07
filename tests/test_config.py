from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from profile_stats.config import ConfigError, Settings, load_settings


class SettingsTests(unittest.TestCase):
    def test_loads_valid_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "config.json")
            path.write_text(
                json.dumps(
                    {
                        "username": "ayutaz",
                        "output_directory": "generated",
                        "token_environment": "PROFILE_STATS_TOKEN",
                        "include_private": False,
                        "include_archived": False,
                        "include_forks": False,
                        "exclude_repositories": ["demo"],
                        "languages_count": 7,
                        "stats_title": "Stats",
                        "languages_title": "Languages",
                    }
                ),
                encoding="utf-8",
            )

            settings = load_settings(path)

        self.assertEqual(settings.username, "ayutaz")
        self.assertEqual(settings.output_directory, "generated")
        self.assertEqual(settings.exclude_repositories, frozenset({"demo"}))
        self.assertEqual(settings.languages_count, 7)

    def test_rejects_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "config.json")
            path.write_text('{"username":"ayutaz","surprise":true}', encoding="utf-8")

            with self.assertRaises(ConfigError):
                load_settings(path)

    def test_settings_reject_invalid_language_count(self) -> None:
        with self.assertRaises(ConfigError):
            Settings(username="ayutaz", languages_count=0)


if __name__ == "__main__":
    unittest.main()

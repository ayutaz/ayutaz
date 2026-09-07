from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryWiringTests(unittest.TestCase):
    def test_workflow_uses_uv_python_313_and_ephemeral_token(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "update-profile-stats.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("schedule:", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d", workflow)
        self.assertIn('python-version: "3.13"', workflow)
        self.assertIn("uv sync --locked", workflow)
        self.assertIn("uv run --locked python -m unittest", workflow)
        self.assertIn("PROFILE_STATS_TOKEN: ${{ github.token }}", workflow)
        self.assertNotIn("secrets.PROFILE_STATS_TOKEN", workflow)

    def test_readme_uses_only_repository_hosted_cards(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("./assets/github-stats.svg", readme)
        self.assertIn("./assets/top-languages.svg", readme)
        self.assertNotIn("github-readme-stats", readme)
        self.assertNotIn("vercel.app", readme)

    def test_project_requires_python_313_or_newer(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('requires-python = ">=3.13"', pyproject)
        self.assertEqual((ROOT / ".python-version").read_text(encoding="utf-8").strip(), "3.13")


if __name__ == "__main__":
    unittest.main()

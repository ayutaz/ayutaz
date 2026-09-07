from __future__ import annotations

import unittest

from profile_stats.config import Settings
from profile_stats.github import GitHubApiError, fetch_snapshot
from tests.helpers import FakeClient, repository, response


class FetchSnapshotTests(unittest.TestCase):
    def test_fetches_every_repository_page(self) -> None:
        client = FakeClient(
            [
                response(
                    [repository("alpha")],
                    followers=12,
                    has_next=True,
                    cursor="cursor-1",
                    total_count=2,
                ),
                response(
                    [repository("beta")],
                    followers=12,
                    has_next=False,
                    total_count=2,
                    remaining=4998,
                ),
            ]
        )

        result = fetch_snapshot(client, Settings(username="ayutaz"))

        self.assertEqual([repo.name for repo in result.snapshot.repositories], ["alpha", "beta"])
        self.assertEqual(result.snapshot.followers, 12)
        self.assertEqual(result.repository_pages, 2)
        self.assertEqual(client.variables[0]["cursor"], None)
        self.assertEqual(client.variables[1]["cursor"], "cursor-1")
        self.assertEqual(client.variables[0]["privacy"], "PUBLIC")
        self.assertEqual(client.variables[0]["isFork"], False)

    def test_rejects_missing_cursor_for_another_page(self) -> None:
        client = FakeClient(
            [response([], has_next=True, cursor=None, total_count=1)]
        )

        with self.assertRaisesRegex(GitHubApiError, "cursor"):
            fetch_snapshot(client, Settings(username="ayutaz"))

    def test_rejects_graphql_errors(self) -> None:
        client = FakeClient([{"errors": [{"message": "Bad credentials"}]}])

        with self.assertRaisesRegex(GitHubApiError, "Bad credentials"):
            fetch_snapshot(client, Settings(username="ayutaz"))


if __name__ == "__main__":
    unittest.main()

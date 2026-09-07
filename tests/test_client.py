from __future__ import annotations

import io
import unittest
import urllib.error
from unittest.mock import patch

from profile_stats.github import GitHubApiError, UrllibGraphQLClient


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def _http_error(code: int, message: str, headers: dict[str, str] | None = None) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://api.github.com/graphql",
        code=code,
        msg=message,
        hdrs=headers or {},
        fp=io.BytesIO(f'{{"message":"{message}"}}'.encode()),
    )


class UrllibGraphQLClientTests(unittest.TestCase):
    def test_does_not_retry_non_rate_limited_forbidden_response(self) -> None:
        sleeps: list[float] = []
        client = UrllibGraphQLClient("secret", sleeper=sleeps.append)

        with patch("urllib.request.urlopen", side_effect=_http_error(403, "Resource not accessible")) as request:
            with self.assertRaisesRegex(GitHubApiError, "Resource not accessible"):
                client.execute("query { viewer { login } }", {})

        self.assertEqual(request.call_count, 1)
        self.assertEqual(sleeps, [])

    def test_retries_transient_server_error_without_leaking_token(self) -> None:
        sleeps: list[float] = []
        client = UrllibGraphQLClient("top-secret-token", sleeper=sleeps.append)
        success = _Response(b'{"data":{"viewer":{"login":"ayutaz"}}}')

        with patch(
            "urllib.request.urlopen",
            side_effect=[_http_error(503, "Service unavailable"), success],
        ) as request:
            result = client.execute("query { viewer { login } }", {})

        self.assertEqual(result["data"]["viewer"]["login"], "ayutaz")
        self.assertEqual(request.call_count, 2)
        self.assertEqual(sleeps, [1.0])


if __name__ == "__main__":
    unittest.main()

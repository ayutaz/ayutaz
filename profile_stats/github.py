from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol

from .config import Settings
from .model import FetchResult, Language, ProfileSnapshot, RateLimit, Repository


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

REPOSITORIES_QUERY = """
query ProfileRepositories(
  $login: String!
  $cursor: String
  $privacy: RepositoryPrivacy
  $isFork: Boolean
) {
  user(login: $login) {
    followers {
      totalCount
    }
    repositories(
      ownerAffiliations: OWNER
      privacy: $privacy
      isFork: $isFork
      first: 100
      after: $cursor
      orderBy: {field: NAME, direction: ASC}
    ) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        isArchived
        isPrivate
        isFork
        stargazerCount
        forkCount
        languages(first: 100, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
  rateLimit {
    cost
    remaining
    resetAt
  }
}
"""


class GraphQLClient(Protocol):
    def execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]: ...


class GitHubApiError(RuntimeError):
    """Raised for transport, authentication, or GraphQL response failures."""


class UrllibGraphQLClient:
    """Small GitHub GraphQL client implemented with the Python standard library."""

    def __init__(
        self,
        token: str,
        *,
        endpoint: str = GITHUB_GRAPHQL_URL,
        timeout_seconds: float = 30.0,
        max_attempts: int = 3,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if not token or not token.strip():
            raise GitHubApiError("GitHub API token is empty")
        self._token = token.strip()
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._sleeper = sleeper

    def execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        for attempt in range(1, self._max_attempts + 1):
            request = urllib.request.Request(
                self._endpoint,
                data=body,
                method="POST",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                    "User-Agent": "ayutaz-profile-stats/1.0",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                    payload = response.read().decode("utf-8")
                parsed = json.loads(payload)
                if not isinstance(parsed, dict):
                    raise GitHubApiError("GitHub GraphQL response root is not an object")
                return parsed
            except urllib.error.HTTPError as error:
                retryable = _is_retryable_http_error(error)
                if retryable and attempt < self._max_attempts:
                    delay = _retry_delay(error.headers.get("Retry-After"), attempt)
                    error.close()
                    self._sleeper(delay)
                    continue
                detail = _safe_http_error_detail(error)
                raise GitHubApiError(f"GitHub API returned HTTP {error.code}: {detail}") from error
            except urllib.error.URLError as error:
                if attempt < self._max_attempts:
                    self._sleeper(float(2 ** (attempt - 1)))
                    continue
                raise GitHubApiError(f"GitHub API network error: {error.reason}") from error
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise GitHubApiError("GitHub API returned invalid JSON") from error
        raise AssertionError("unreachable")


def fetch_snapshot(client: GraphQLClient, settings: Settings) -> FetchResult:
    repositories: list[Repository] = []
    followers: int | None = None
    cursor: str | None = None
    seen_cursors: set[str] = set()
    pages = 0
    last_rate_limit = RateLimit(None, None, None)

    while True:
        variables = {
            "login": settings.username,
            "cursor": cursor,
            "privacy": None if settings.include_private else "PUBLIC",
            "isFork": None if settings.include_forks else False,
        }
        payload = client.execute(REPOSITORIES_QUERY, variables)
        errors = payload.get("errors")
        if errors:
            raise GitHubApiError(_graphql_error_message(errors))
        data = payload.get("data")
        if not isinstance(data, dict):
            raise GitHubApiError("GitHub GraphQL response is missing data")
        user = data.get("user")
        if not isinstance(user, dict):
            raise GitHubApiError(f"GitHub user '{settings.username}' was not found")
        follower_data = user.get("followers")
        connection = user.get("repositories")
        if not isinstance(follower_data, dict) or not isinstance(connection, dict):
            raise GitHubApiError("GitHub GraphQL response is missing profile fields")
        current_followers = _nonnegative_int(follower_data.get("totalCount"), "followers")
        if followers is None:
            followers = current_followers
        elif followers != current_followers:
            raise GitHubApiError("followers changed during paginated fetch; retry the run")

        nodes = connection.get("nodes")
        page_info = connection.get("pageInfo")
        if not isinstance(nodes, list) or not isinstance(page_info, dict):
            raise GitHubApiError("GitHub GraphQL response has invalid repository pagination")
        repositories.extend(_parse_repository(node) for node in nodes)
        pages += 1
        last_rate_limit = _parse_rate_limit(data.get("rateLimit"))

        has_next = page_info.get("hasNextPage")
        if type(has_next) is not bool:
            raise GitHubApiError("GitHub GraphQL response has invalid hasNextPage")
        if not has_next:
            break
        next_cursor = page_info.get("endCursor")
        if not isinstance(next_cursor, str) or not next_cursor:
            raise GitHubApiError("GitHub GraphQL pagination cursor is missing")
        if next_cursor in seen_cursors:
            raise GitHubApiError("GitHub GraphQL pagination cursor was repeated")
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    return FetchResult(
        snapshot=ProfileSnapshot(
            username=settings.username,
            followers=followers or 0,
            repositories=tuple(repositories),
        ),
        repository_pages=pages,
        rate_limit=last_rate_limit,
    )


def _parse_repository(value: Any) -> Repository:
    if not isinstance(value, dict):
        raise GitHubApiError("GitHub GraphQL repository node is invalid")
    name = value.get("name")
    if not isinstance(name, str) or not name:
        raise GitHubApiError("GitHub GraphQL repository name is invalid")
    for field in ("isArchived", "isPrivate", "isFork"):
        if type(value.get(field)) is not bool:
            raise GitHubApiError(f"GitHub GraphQL repository field {field} is invalid")
    language_connection = value.get("languages")
    if not isinstance(language_connection, dict) or not isinstance(
        language_connection.get("edges"), list
    ):
        raise GitHubApiError("GitHub GraphQL language data is invalid")
    languages: list[Language] = []
    for edge in language_connection["edges"]:
        if not isinstance(edge, dict) or not isinstance(edge.get("node"), dict):
            raise GitHubApiError("GitHub GraphQL language edge is invalid")
        language_name = edge["node"].get("name")
        color = edge["node"].get("color")
        if not isinstance(language_name, str) or not language_name:
            raise GitHubApiError("GitHub GraphQL language name is invalid")
        if color is not None and not isinstance(color, str):
            raise GitHubApiError("GitHub GraphQL language color is invalid")
        languages.append(
            Language(
                name=language_name,
                size=_nonnegative_int(edge.get("size"), "language size"),
                color=color,
            )
        )
    return Repository(
        name=name,
        is_archived=value["isArchived"],
        is_private=value["isPrivate"],
        is_fork=value["isFork"],
        stars=_nonnegative_int(value.get("stargazerCount"), "stargazerCount"),
        forks=_nonnegative_int(value.get("forkCount"), "forkCount"),
        languages=tuple(languages),
    )


def _parse_rate_limit(value: Any) -> RateLimit:
    if not isinstance(value, dict):
        return RateLimit(None, None, None)
    cost = value.get("cost")
    remaining = value.get("remaining")
    reset_at = value.get("resetAt")
    return RateLimit(
        cost=cost if type(cost) is int else None,
        remaining=remaining if type(remaining) is int else None,
        reset_at=reset_at if isinstance(reset_at, str) else None,
    )


def _nonnegative_int(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        raise GitHubApiError(f"GitHub GraphQL field {field} is invalid")
    return value


def _graphql_error_message(errors: Any) -> str:
    if not isinstance(errors, list):
        return "GitHub GraphQL returned an unknown error"
    messages = [
        error.get("message")
        for error in errors
        if isinstance(error, dict) and isinstance(error.get("message"), str)
    ]
    return "; ".join(messages) if messages else "GitHub GraphQL returned an unknown error"


def _retry_delay(retry_after: str | None, attempt: int) -> float:
    if retry_after is not None:
        try:
            seconds = float(retry_after)
            if 0 <= seconds <= 60:
                return seconds
        except ValueError:
            pass
    return float(2 ** (attempt - 1))


def _is_retryable_http_error(error: urllib.error.HTTPError) -> bool:
    if error.code in {429, 502, 503, 504}:
        return True
    if error.code != 403:
        return False
    return bool(error.headers.get("Retry-After")) or error.headers.get("X-RateLimit-Remaining") == "0"


def _safe_http_error_detail(error: urllib.error.HTTPError) -> str:
    try:
        body = error.read().decode("utf-8")
        parsed = json.loads(body)
        message = parsed.get("message") if isinstance(parsed, dict) else None
        if isinstance(message, str) and message:
            return message[:200]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    return error.reason or "request failed"

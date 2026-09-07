from __future__ import annotations


def language(name: str, size: int, color: str | None = None) -> dict:
    return {"size": size, "node": {"name": name, "color": color}}


def repository(
    name: str,
    *,
    archived: bool = False,
    private: bool = False,
    fork: bool = False,
    stars: int = 0,
    forks: int = 0,
    languages: list[dict] | None = None,
) -> dict:
    return {
        "name": name,
        "isArchived": archived,
        "isPrivate": private,
        "isFork": fork,
        "stargazerCount": stars,
        "forkCount": forks,
        "languages": {"edges": languages or []},
    }


def response(
    nodes: list[dict],
    *,
    followers: int = 0,
    has_next: bool = False,
    cursor: str | None = None,
    total_count: int | None = None,
    remaining: int = 4999,
) -> dict:
    return {
        "data": {
            "user": {
                "followers": {"totalCount": followers},
                "repositories": {
                    "totalCount": len(nodes) if total_count is None else total_count,
                    "pageInfo": {
                        "hasNextPage": has_next,
                        "endCursor": cursor,
                    },
                    "nodes": nodes,
                },
            },
            "rateLimit": {
                "cost": 1,
                "remaining": remaining,
                "resetAt": "2026-09-08T00:00:00Z",
            },
        }
    }


class FakeClient:
    def __init__(self, responses: list[dict | Exception]):
        self.responses = list(responses)
        self.variables: list[dict] = []

    def execute(self, query: str, variables: dict) -> dict:
        self.variables.append(variables)
        if not self.responses:
            raise AssertionError("Unexpected GraphQL request")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

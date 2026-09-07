from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    name: str
    size: int
    color: str | None


@dataclass(frozen=True)
class Repository:
    name: str
    is_archived: bool
    is_private: bool
    is_fork: bool
    stars: int
    forks: int
    languages: tuple[Language, ...]


@dataclass(frozen=True)
class ProfileSnapshot:
    username: str
    followers: int
    repositories: tuple[Repository, ...]


@dataclass(frozen=True)
class RateLimit:
    cost: int | None
    remaining: int | None
    reset_at: str | None


@dataclass(frozen=True)
class FetchResult:
    snapshot: ProfileSnapshot
    repository_pages: int
    rate_limit: RateLimit


@dataclass(frozen=True)
class Stats:
    active_repositories: int
    stars: int
    forks: int
    followers: int
    language_count: int
    code_bytes: int


@dataclass(frozen=True)
class LanguageStat:
    name: str
    color: str
    size: int
    percentage: float


@dataclass(frozen=True)
class Report:
    username: str
    stats: Stats
    languages: tuple[LanguageStat, ...]
    fetched_repositories: int
    excluded_counts: dict[str, int]

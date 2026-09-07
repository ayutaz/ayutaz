from __future__ import annotations

import re
from collections import defaultdict

from .config import Settings
from .model import LanguageStat, ProfileSnapshot, Report, Stats


FALLBACK_COLOR = "#858585"
_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def build_report(snapshot: ProfileSnapshot, settings: Settings) -> Report:
    included = []
    excluded_counts = {"archived": 0, "private": 0, "fork": 0, "named": 0}

    for repository in snapshot.repositories:
        reason = _exclusion_reason(repository, settings)
        if reason is not None:
            excluded_counts[reason] += 1
            continue
        included.append(repository)

    language_sizes: dict[str, int] = defaultdict(int)
    language_colors: dict[str, str] = {}
    for repository in included:
        for language in repository.languages:
            if language.size <= 0:
                continue
            language_sizes[language.name] += language.size
            language_colors.setdefault(language.name, _valid_color(language.color))

    total_bytes = sum(language_sizes.values())
    ordered = sorted(language_sizes, key=lambda name: (-language_sizes[name], name.casefold(), name))
    languages = tuple(
        LanguageStat(
            name=name,
            color=language_colors[name],
            size=language_sizes[name],
            percentage=(language_sizes[name] * 100.0 / total_bytes) if total_bytes else 0.0,
        )
        for name in ordered[: settings.languages_count]
    )
    stats = Stats(
        active_repositories=len(included),
        stars=sum(repository.stars for repository in included),
        forks=sum(repository.forks for repository in included),
        followers=snapshot.followers,
        language_count=len(language_sizes),
        code_bytes=total_bytes,
    )
    return Report(
        username=snapshot.username,
        stats=stats,
        languages=languages,
        fetched_repositories=len(snapshot.repositories),
        excluded_counts=excluded_counts,
    )


def _exclusion_reason(repository: object, settings: Settings) -> str | None:
    if getattr(repository, "is_private") and not settings.include_private:
        return "private"
    if getattr(repository, "is_fork") and not settings.include_forks:
        return "fork"
    if getattr(repository, "is_archived") and not settings.include_archived:
        return "archived"
    if getattr(repository, "name").casefold() in settings.exclude_repositories:
        return "named"
    return None


def _valid_color(color: str | None) -> str:
    return color if isinstance(color, str) and _HEX_COLOR.fullmatch(color) else FALLBACK_COLOR

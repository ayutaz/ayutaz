from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when the public project configuration is invalid."""


_USERNAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_ENVIRONMENT_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")


@dataclass(frozen=True)
class Settings:
    username: str
    output_directory: str = "assets"
    token_environment: str = "PROFILE_STATS_TOKEN"
    include_private: bool = False
    include_archived: bool = False
    include_forks: bool = False
    exclude_repositories: frozenset[str] = frozenset()
    languages_count: int = 6
    stats_title: str = "GitHub Stats"
    languages_title: str = "Top Languages"

    def __post_init__(self) -> None:
        if not isinstance(self.username, str) or not _USERNAME.fullmatch(self.username):
            raise ConfigError("username must be a valid GitHub username")
        if not isinstance(self.output_directory, str) or not self.output_directory.strip():
            raise ConfigError("output_directory must be a non-empty relative path")
        normalized_path = self.output_directory.replace("\\", "/")
        if (
            normalized_path.startswith("/")
            or re.match(r"^[A-Za-z]:", normalized_path)
            or ".." in normalized_path.split("/")
        ):
            raise ConfigError("output_directory must stay inside the repository")
        if not isinstance(self.token_environment, str) or not _ENVIRONMENT_NAME.fullmatch(
            self.token_environment
        ):
            raise ConfigError("token_environment must be an uppercase environment variable name")
        for name in ("include_private", "include_archived", "include_forks"):
            if type(getattr(self, name)) is not bool:
                raise ConfigError(f"{name} must be a boolean")
        if type(self.languages_count) is not int or not 1 <= self.languages_count <= 12:
            raise ConfigError("languages_count must be between 1 and 12")
        if not isinstance(self.exclude_repositories, (set, frozenset, list, tuple)):
            raise ConfigError("exclude_repositories must be a list of repository names")
        excluded: set[str] = set()
        for item in self.exclude_repositories:
            if not isinstance(item, str) or not item.strip():
                raise ConfigError("exclude_repositories entries must be non-empty strings")
            excluded.add(item.strip().casefold())
        object.__setattr__(self, "exclude_repositories", frozenset(excluded))
        for name in ("stats_title", "languages_title"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > 80:
                raise ConfigError(f"{name} must contain between 1 and 80 characters")


def load_settings(path: Path) -> Settings:
    """Load and strictly validate a JSON settings file."""

    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ConfigError(f"could not read configuration: {error}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"configuration is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be an object")

    known = {field.name for field in fields(Settings)}
    unknown = sorted(set(raw) - known)
    if unknown:
        raise ConfigError(f"unknown configuration keys: {', '.join(unknown)}")
    try:
        return Settings(**raw)
    except TypeError as error:
        raise ConfigError(str(error)) from error

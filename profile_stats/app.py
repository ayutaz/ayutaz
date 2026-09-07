from __future__ import annotations

import hashlib
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .aggregate import build_report
from .config import Settings
from .github import GraphQLClient, fetch_snapshot
from .model import FetchResult, Report
from .render import render_languages_svg, render_stats_svg


SCHEMA_VERSION = 1
RENDERER_VERSION = "1.0.0"


@dataclass(frozen=True)
class GenerationResult:
    changed: bool
    report: Report
    fetch_result: FetchResult


def generate_assets(
    settings: Settings,
    client: GraphQLClient,
    output_directory: Path,
    generated_at: datetime | None = None,
) -> GenerationResult:
    """Fetch, validate, and publish all generated assets as one logical operation."""

    fetched = fetch_snapshot(client, settings)
    report = build_report(fetched.snapshot, settings)
    stable_metadata = _stable_metadata(settings, report, fetched)
    data_digest = hashlib.sha256(
        json.dumps(stable_metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    metadata_path = output_directory / "stats-metadata.json"
    if _assets_are_current(output_directory, metadata_path, data_digest):
        return GenerationResult(False, report, fetched)

    stats_svg = render_stats_svg(report, settings.stats_title)
    languages_svg = render_languages_svg(report, settings.languages_title)
    _validate_svg(stats_svg)
    _validate_svg(languages_svg)

    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    metadata = dict(stable_metadata)
    metadata["data_digest"] = data_digest
    metadata["generated_at"] = timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _publish_files(
        output_directory,
        {
            "github-stats.svg": stats_svg,
            "top-languages.svg": languages_svg,
            "stats-metadata.json": metadata_json,
        },
    )
    return GenerationResult(True, report, fetched)


def _stable_metadata(settings: Settings, report: Report, fetched: FetchResult) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "renderer_version": RENDERER_VERSION,
        "username": report.username,
        "policy": {
            "include_private": settings.include_private,
            "include_archived": settings.include_archived,
            "include_forks": settings.include_forks,
            "excluded_repository_count": len(settings.exclude_repositories),
            "languages_count": settings.languages_count,
        },
        "fetched_repositories": report.fetched_repositories,
        "repository_pages": fetched.repository_pages,
        "excluded_counts": report.excluded_counts,
        "stats": asdict(report.stats),
        "languages": [asdict(language) for language in report.languages],
    }


def _existing_digest(path: Path) -> str | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    digest = value.get("data_digest") if isinstance(value, dict) else None
    return digest if isinstance(digest, str) else None


def _assets_are_current(output_directory: Path, metadata_path: Path, digest: str) -> bool:
    if _existing_digest(metadata_path) != digest:
        return False
    for name in ("github-stats.svg", "top-languages.svg"):
        try:
            value = (output_directory / name).read_text(encoding="utf-8")
            _validate_svg(value)
        except (OSError, UnicodeDecodeError, ValueError):
            return False
    return True


def _validate_svg(value: str) -> None:
    try:
        root = ET.fromstring(value)
    except ET.ParseError as error:
        raise ValueError(f"generated SVG is not valid XML: {error}") from error
    if not root.tag.endswith("svg"):
        raise ValueError("generated XML root is not SVG")


def _publish_files(output_directory: Path, files: dict[str, str]) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    staged: dict[str, Path] = {}
    try:
        for name, content in files.items():
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=".profile-stats-",
                suffix=".tmp",
                dir=output_directory,
                delete=False,
            ) as handle:
                handle.write(content)
                staged[name] = Path(handle.name)
        for name, staged_path in staged.items():
            os.replace(staged_path, output_directory / name)
    finally:
        for staged_path in staged.values():
            try:
                staged_path.unlink(missing_ok=True)
            except OSError:
                pass

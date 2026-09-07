from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from profile_stats.app import generate_assets  # noqa: E402
from profile_stats.config import ConfigError, load_settings  # noqa: E402
from profile_stats.github import GitHubApiError, UrllibGraphQLClient  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate static GitHub profile statistics SVGs")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "profile-stats.json",
        help="Path to the public JSON configuration",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        help="Override the configured output directory",
    )
    args = parser.parse_args(argv)

    try:
        settings = load_settings(args.config)
        token = os.environ.get(settings.token_environment)
        if not token:
            raise ConfigError(
                f"required environment variable {settings.token_environment} is not set"
            )
        output = args.output_directory or PROJECT_ROOT / settings.output_directory
        result = generate_assets(settings, UrllibGraphQLClient(token), output)
    except (ConfigError, GitHubApiError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    action = "updated" if result.changed else "unchanged"
    rate = result.fetch_result.rate_limit
    print(
        f"{action}: {result.report.stats.active_repositories} active repositories, "
        f"{len(result.report.languages)} displayed languages, "
        f"{result.fetch_result.repository_pages} API pages"
    )
    if rate.remaining is not None:
        print(f"GitHub GraphQL points remaining: {rate.remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

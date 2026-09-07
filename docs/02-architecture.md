# Architecture decision

## Decision

- **Decided**: Use GitHub Actions to generate static SVG files in the profile repository.
- **Decided**: Do not operate an HTTP API, Vercel project, database, cache, GitHub Pages site, or always-on server.

```text
schedule / workflow_dispatch
          |
          v
uv-managed Python 3.13+ standard-library generator
          |
          v
GitHub GraphQL API -- all repository pages
          |
          v
validate SVG + metadata in memory
          |
          v
atomically replace assets only on full success
          |
          v
commit changed assets with the workflow GITHUB_TOKEN
```

## Why static generation

- **Confirmed**: The current dynamic endpoint makes the public card unavailable when its API credential fails.
- **Decided**: A failed scheduled refresh leaves the previous committed SVG intact.
- **Decided**: API traffic is bounded to scheduled/manual runs instead of arbitrary profile views and cache-busting requests.
- **Decided**: The generated data and changes remain reviewable in Git history.

## Authentication boundaries

- GitHub Actions creates a short-lived `GITHUB_TOKEN` for each job. The workflow passes it to the generator as `PROFILE_STATS_TOKEN` and uses it to commit changed assets to this repository.
- The token is repository-scoped and expires after the job. No personal access token or long-lived repository secret is required for the public-only aggregation policy.
- The workflow grants only `contents: write`; unspecified workflow permissions remain disabled.

## Repository layout

```text
assets/                         generated, published SVG and metadata
docs/                           decisions, metric contracts, operations
profile_stats/                  standard-library implementation
tests/                          deterministic unit and integration-boundary tests
tools/generate_github_stats.py  command-line entry point
.github/workflows/              scheduled/manual automation
profile-stats.json              public aggregation policy
pyproject.toml / uv.lock         Python >=3.13 and reproducible uv project state
```

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

- `PROFILE_STATS_TOKEN`: read-only data token exposed only to the generator step.
- `GITHUB_TOKEN`: short-lived workflow token with `contents: write`, used only to commit assets to this repository.

The two credentials are intentionally not interchangeable.

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

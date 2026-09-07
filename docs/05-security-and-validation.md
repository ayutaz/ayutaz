# Security and validation

## Token policy

- **Decided**: Store the API token only in the `PROFILE_STATS_TOKEN` GitHub Actions secret.
- **Decided**: Use a fine-grained, read-only token. Public-only aggregation is the initial policy.
- **Decided**: Never reuse a broad local GitHub CLI credential as the workflow secret.
- **Decided**: Never print request headers, environment variables, or token values.

## Publication policy

- Fetch and aggregate all data before writing output.
- Render every output in memory.
- Parse generated SVG as XML and validate metadata before staging files.
- Stage all files in the destination directory, then replace final files.
- If any earlier operation fails, retain the last known-good committed assets.

## Automated checks

- `uv lock --check` and Python 3.13+ runtime verification;
- synthetic multi-page API responses;
- private/fork/archive/name exclusion;
- deterministic language ordering and percentages;
- malicious-looking title escaping;
- invalid GraphQL responses and missing cursors;
- unchanged-data detection;
- metadata privacy boundary.

## Manual production checks

- **Open**: verify the Actions secret exists without exposing its value.
- **Open**: run the workflow manually and inspect its permissions and logs.
- **Open**: open both raw SVG files and the GitHub profile in light and dark browser themes.
- **Open**: confirm old Vercel URLs are absent after the committed migration.

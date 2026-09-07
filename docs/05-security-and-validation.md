# Security and validation

## Token policy

- **Decided**: Use the short-lived `GITHUB_TOKEN` created automatically for each Actions job; do not create a long-lived repository secret for the public-only policy.
- **Decided**: Pass the built-in token to the generator only through its process environment under the expected `PROFILE_STATS_TOKEN` name.
- **Decided**: Never reuse a broad local GitHub CLI credential as a workflow credential.
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

- **Open**: run the secret-free workflow manually and inspect its permissions and logs.
- **Confirmed 2026-09-07**: both SVGs render completely in a browser, and the public GitHub profile displays both cards in a light-theme browser session.
- **Open**: repeat the public-profile review in a dark-theme browser session.
- **Confirmed 2026-09-07**: old Vercel URLs are absent after the committed migration.

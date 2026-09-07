# Metric definitions

## Repository inclusion policy

The default report includes repositories that satisfy all of these conditions:

- owned by `ayutaz`;
- public;
- not a fork;
- not archived;
- not named in `exclude_repositories`.

The GitHub GraphQL response is paginated until `hasNextPage` is false. Filters are applied both in the query where possible and again locally as a defensive check.

## GitHub stats card

- **Active repositories**: number of repositories remaining after the inclusion policy.
- **Stars earned**: sum of `stargazerCount` across included repositories.
- **Forks earned**: sum of `forkCount` across included repositories.
- **Followers**: current `followers.totalCount` for the profile.
- **Languages**: number of distinct languages with a positive byte count across included repositories.
- **Code measured**: sum of GitHub language byte counts across included repositories.

These are repository portfolio metrics. They do not claim to measure skill, authored lines, or total historical activity.

## Top Languages card

- For each included repository, aggregate each `LanguageEdge.size` by language name.
- Sort by byte count descending, then by language name for deterministic ties.
- Percentage denominator is the sum of all included language bytes, not only the displayed top languages.
- Display the first `languages_count` entries.
- Use GitHub's language color when it is a valid six-digit hex color; otherwise use a neutral fallback.

## Generated metadata

`assets/stats-metadata.json` contains only aggregate values, policy flags, API page count, renderer/schema versions, and a digest. It must not contain access tokens or private repository names.

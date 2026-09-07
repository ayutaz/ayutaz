# Operations

## Local development

The project must be run through `uv` and Python 3.13 or newer.

```powershell
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
```

For a local live generation, provide a dedicated read-only token only for the process session:

```powershell
$env:PROFILE_STATS_TOKEN = Read-Host -MaskInput "Read-only GitHub token"
try {
    uv run --locked python tools/generate_github_stats.py
} finally {
    Remove-Item Env:PROFILE_STATS_TOKEN -ErrorAction SilentlyContinue
}
```

Do not paste a token into `profile-stats.json`, a workflow file, command history, documentation, or generated metadata.

## First production activation

1. Create a dedicated fine-grained token for `ayutaz` with read-only access.
2. In `ayutaz/ayutaz`, open **Settings -> Secrets and variables -> Actions**.
3. Add a repository secret named `PROFILE_STATS_TOKEN`.
4. Open **Actions -> Update profile stats -> Run workflow**.
5. Confirm the test and generation steps succeed.
6. Confirm the workflow either commits changed assets or reports that the data is unchanged.
7. Open the profile and review both cards visually.

## Scheduled operation

The workflow runs daily at 03:17 in `Asia/Tokyo` and can also be started with `workflow_dispatch`. A non-hour boundary is used to reduce the chance of GitHub Actions schedule congestion.

If the API or token fails, the workflow exits before committing. The last committed SVGs remain visible.

## Token rotation

1. Create the replacement read-only token before revoking the old one.
2. Replace the `PROFILE_STATS_TOKEN` Actions secret.
3. Run the workflow manually and verify both cards.
4. Revoke the old token only after the successful run.

## Retiring the Vercel deployment

The old Vercel deployment is not required after the repository-hosted cards are committed and visually verified. Deletion or disconnection is intentionally a separate user-approved action because it changes external infrastructure and is not required for profile availability.

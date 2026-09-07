# Operations

## Local development

The project must be run through `uv` and Python 3.13 or newer.

```powershell
uv sync --locked
uv run --locked python -m unittest discover -s tests -v
```

For a local live generation, provide a read-only token only for the process session:

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

1. Open **Actions -> Update profile stats -> Run workflow**.
2. Confirm the test and generation steps succeed with the automatically created `GITHUB_TOKEN`.
3. Confirm the workflow either commits changed assets or reports that the data is unchanged.
4. Open the profile and review both cards visually.

## Scheduled operation

The workflow runs daily at 03:17 in `Asia/Tokyo` and can also be started with `workflow_dispatch`. A non-hour boundary is used to reduce the chance of GitHub Actions schedule congestion.

If the API or token fails, the workflow exits before committing. The last committed SVGs remain visible.

No token rotation is needed: GitHub creates a short-lived token for every job and expires it after the job.

## Retiring the Vercel deployment

The old Vercel deployment is not required after the repository-hosted cards are committed and visually verified. Deletion or disconnection is intentionally a separate user-approved action because it changes external infrastructure and is not required for profile availability.

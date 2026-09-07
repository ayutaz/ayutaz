# Implementation plan

## Milestones

1. **M0 - Planning**
   - **Complete locally**: requirements, architecture, metric contracts, and security gates documented.
2. **M1 - Tests first**
   - **Complete locally**: pagination, filtering, aggregation, XML escaping, deterministic rendering, and failure preservation tests were observed failing before implementation and now pass.
3. **M2 - Core implementation**
   - **Complete locally**: `uv` project constrained to Python 3.13+, GraphQL client, repository fetcher, aggregation, SVG rendering, metadata, and atomic publication.
4. **M3 - Automation**
   - **Complete locally**: daily and manual GitHub Actions workflow with pinned official Actions and least-privilege workflow permissions.
5. **M4 - Local verification**
   - **Complete locally**: full unit suite plus a real public-data generation using the authenticated local GitHub account. The live run fetched 201 public non-fork repositories over three pages and selected 31 non-archived repositories.
6. **M5 - Production activation**
   - **Prepared for delivery**: initial generated assets and the README migration are ready to commit and push to `main`.
   - **Open after delivery**: create a dedicated read-only `PROFILE_STATS_TOKEN`, add it as an Actions secret, manually run the workflow, and visually review the rendered profile. Each completed production step must be recorded separately; a local result is not production evidence.

## Completion gates

- `uv lock --check` succeeds and all tests pass through `uv run` on Python 3.13 or newer.
- A deliberately disconnected pagination cursor is rejected.
- A simulated API failure leaves existing assets byte-for-byte unchanged.
- Both SVG outputs parse as XML.
- Generated metadata contains no repository names or credentials.
- The README refers only to repository-hosted assets.
- The workflow has both `schedule` and `workflow_dispatch` triggers.
- Production success and final visual quality remain explicit post-push gates.

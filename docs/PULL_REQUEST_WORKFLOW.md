# Pull Request Workflow

How to create, review, and merge pull requests for Parlay Gorilla.

## Creating a PR

1. **Branch from `main`** (keep it short-lived):
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-change   # or fix/..., docs/..., chore/...
   ```

2. **Commit and push**:
   ```bash
   git add <files>
   git commit -m "Short descriptive message"
   git push -u origin feature/your-change
   ```

3. **Open the PR** on GitHub (repo → "Compare & pull request" or New pull request).  
   The [PR template](.github/PULL_REQUEST_TEMPLATE.md) will pre-fill the description.

4. **Wait for CI** — `.github/workflows/ci.yml` runs on every PR (backend lint/tests, frontend lint/build, availability contract, security scan). Fix any failures before merge.

## Reviewing a PR

- Confirm CI is green.
- Check that the summary and type of change are accurate.
- For dependency updates (e.g. Dependabot): skim changelog/release notes; merge when CI passes if low risk.
- For features/fixes: ensure no secrets, and that docs/runbooks are updated if behavior or config changed.

## Merging

- Prefer **squash and merge** for a single commit on `main`, or **merge commit** if you want to preserve branch history.
- After merge, **deploys**:
  - **Frontend**: Vercel deploys from `main` (production branch).
  - **Backend**: GitHub Actions deploy to Oracle VM on push to `main` (see [oracle_bluegreen_setup](deploy/oracle_bluegreen_setup.md)).

## Dependabot PRs

The repo has many `dependabot/*` branches. To handle them:

- **Batch merge**: Review a few, ensure CI is green, then merge. You can merge multiple Dependabot PRs in a row.
- **Grouping**: In GitHub, you can enable Dependabot version updates grouping (e.g. in `.github/dependabot.yml`) to reduce PR count.
- **Close without merging**: If an update is not needed or is risky, close the PR; Dependabot will open a new one when it has a newer version.

## Quick reference

| Step              | Where / command                                      |
|-------------------|------------------------------------------------------|
| Create branch     | `git checkout -b <branch>` from `main`               |
| Push branch       | `git push -u origin <branch>`                       |
| Open PR           | GitHub → Compare & pull request                     |
| CI status         | GitHub Actions tab on the PR                        |
| Merge             | GitHub PR page → Squash and merge (or Merge pull request) |
| Production deploy | Automatic on push to `main` (frontend + backend)    |

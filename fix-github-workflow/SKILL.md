---
name: fix-github-workflow
description: Diagnose and fix failing GitHub Actions workflows. Fetches failed run logs, applies fixes, validates locally with act, commits, pushes, then watches the next CI run — repeating until the workflow is green. Use when a GitHub Actions run is failing, when given a workflow run URL or PR number with CI failures, or when asked to fix a CI/CD error.
---

# Fix GitHub Workflow

## Quick start

```bash
# 1. Get the failed logs
gh run view <run-id> --log-failed

# 2. Fix the issue locally, then test with act
act pull_request --secret GITHUB_TOKEN=$(gh auth token) --job <job-name>

# 3. Commit, push, and watch
git push && gh run watch <new-run-id> --exit-status
```

## Workflow

### 1. Diagnose

```bash
gh run view <run-id> --log-failed
```

If given a PR number instead of a run ID:
```bash
gh run list -R <owner>/<repo> -b <branch> --limit 3
```

Read the error carefully. Common categories and where to look:

| Error | Likely cause |
|---|---|
| 403 on package download | Missing `packages: read` permission on job |
| `frozen-lockfile` conflict | Lockfile out of sync with package.json |
| Babel / transform errors | Mismatched dependency versions in lockfile |
| Missing module | Dependency not installed or wrong version |
| Syntax / parse error | Code incompatible with Node/tool version in CI |

### 2. Check the workflow file

```bash
cat .github/workflows/<name>.yml
```

Things to verify:
- Does the job have a `permissions:` block? If fetching packages from GitHub Packages (`npm.pkg.github.com`), it needs:
  ```yaml
  permissions:
    contents: read
    packages: read
  ```
- Is `NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` set for the install step?
- What `node-version` is specified? Check compatibility with dependencies.

### 3. Reproduce locally

Before making changes, confirm you can reproduce the error:
```bash
# Match CI environment: frozen lockfile, ignore scripts
NODE_AUTH_TOKEN=dummy yarn install --frozen-lockfile --ignore-scripts
yarn test
```

### 4. Fix and validate with act

After applying the fix, test the full workflow locally before pushing:

```bash
act pull_request --secret GITHUB_TOKEN=$(gh auth token) --job <job-name>
```

- `$(gh auth token)` generates a valid token — no manual copy-paste needed
- Use `--job <name>` to target a specific job (faster than running all)
- If `act` isn't available: `brew install act` or check system package manager

### 5. Commit and push

Use the `commit` skill, then push:
```bash
git push
```

### 6. Watch the outcome

Get the new run ID and watch it:
```bash
gh run list -R <owner>/<repo> -b <branch> --limit 1
gh run watch <new-run-id> --exit-status
```

If it fails again, go back to step 1 with the new run ID. Repeat until green.

## Common fixes

**Missing `packages: read` permission**
Add to the failing job in the workflow file:
```yaml
permissions:
  contents: read
  packages: read
```

**Dependency version mismatch (e.g. lockfile upgraded a transitive dep)**
Check what version was locked before vs now:
```bash
git show <base-branch>:yarn.lock | grep -A3 '"<package>@'
```
Pin or downgrade using `yarn add --dev <package>@<version> --ignore-scripts`, then verify tests pass.

**Lockfile out of sync**
```bash
yarn install  # regenerates lockfile
yarn test     # confirm tests still pass
```

## Notes

- Always run `act` before committing — it catches issues without burning CI minutes
- `gh auth token` is the cleanest way to pass a token to `act`; avoids storing tokens in shell history
- If `--frozen-lockfile` fails in CI but not locally, the lockfile was modified without a matching install

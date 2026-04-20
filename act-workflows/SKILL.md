---
name: act-workflows
description: Test GitHub Actions workflows locally using act, diagnose failures, and fix act-specific compatibility issues. Use when the user wants to run workflows locally, test CI with act, or debug act failures like missing tools, API errors, or container image gaps.
---

# act-workflows

Runs GitHub Actions workflows locally with `act`, monitors results in parallel, and fixes the common act compatibility issues.

## Quick start

```bash
# Run a single job
act -j <jobName> --no-cache-server

# Run all jobs in parallel (background each, then Monitor output files)
act -j lintShellScript --no-cache-server &
act -j lintYaml        --no-cache-server &
```

Use the **Monitor tool** on all output files at once:

```bash
tail -f /path/to/task/*.output | grep --line-buffered -E "✅  Success - Main|❌  Failure - Main|🏁  Job|exitcode"
```

## Diagnosing failures

Read the raw output file and grep for the signal:

```bash
grep -E "error|Error|SC[0-9]+|MD[0-9]+|exitcode" /path/to/task/output | head -40
```

## Common failures and fixes

### exit 127 — tool not installed in container

The `catthehacker/ubuntu:act-latest` image is stripped down. Add an install step before the action:

```yaml
- name: Install yamllint
  run: pip install --break-system-packages yamllint
```

### PEP 668 — externally-managed-environment

Always use `--break-system-packages` with pip in CI containers.

### SC1091 — sourced file not found

ShellCheck can't follow `source /path/to/runtime.env` in CI. Add a `.shellcheckrc` at the repo root:

```
disable=SC1091
```

### reviewdog — `diff command is empty` or 404 on check-runs

reviewdog needs a real GitHub token and API context. Skip the step in act using the `ACT` env var act always sets:

```yaml
- name: Lint GitHub Actions
  if: ${{ !env.ACT }}
  uses: reviewdog/action-actionlint@<sha>
```

The step is skipped locally but runs normally on GitHub.

### mdl MD### false positives

Add rules to the `~` exclude list in the mdl command:

```yaml
run: mdl --git-recurse --rules ~MD007,~MD013,~MD029 .
```

Common excludes: `MD007` (list indent false positives on complex nested lists), `MD013` (line length), `MD029` (ordered list numbering).

## Notes

- First `act` run pulls `catthehacker/ubuntu:act-latest` (~1 GB) — subsequent runs use the cached image
- `unable to get git ref: reference not found` warnings are harmless on repos with no commits yet
- act sets the `ACT` env var — use `if: ${{ !env.ACT }}` to guard any step that needs real GitHub API access

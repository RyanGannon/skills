---
name: gabo-workflows
description: Add and test GitHub Actions workflows using gabo and act. Use when the user asks to add GitHub Actions, set up CI workflows, generate workflows with gabo, or test workflows locally with act.
---

# gabo-workflows

Generates appropriate GitHub Actions workflows for the current repo using `gabo`, then tests them locally with `act`.

## Workflow

### 1. Ensure the directory is a git repo

`gabo` requires a git repo to run analysis:

```bash
git init -q   # no-op if already a repo
```

### 2. Analyze with gabo

```bash
gabo -mode analyze -dir .
```

gabo scans for file types (`.sh`, `.yml`, `.md`, `.go`, `Dockerfile`, etc.) and prints the exact generate command to run.

### 3. Generate the workflows

Copy the command from gabo's output and run it, e.g.:

```bash
gabo --mode=generate --for=lint-shell-script,lint-yaml,lint-markdown --dir=.
```

Add `--force` to overwrite existing workflow files.

### 4. Test with act (in parallel)

Use the **act-workflows** skill — it covers parallel job execution, monitoring output files, and fixing all common act compatibility issues (missing tools, SC1091, reviewdog API errors, mdl false positives).

## Available gabo workflow types

| Flag | What it lints |
|---|---|
| `lint-shell-script` | `*.sh`, `*.bash` via ShellCheck |
| `lint-yaml` | `*.yml`, `*.yaml` + GitHub Actions via actionlint |
| `lint-markdown` | `*.md` via mdl (markdownlint) |
| `lint-docker` | `Dockerfile*` via hadolint |
| `lint-go` | `*.go` via golangci-lint |
| `lint-github-actions` | workflow files via actionlint |
| `build-docker` | builds Docker image on push |
| `build-npm` / `build-yarn` | JS builds |
| `format-go` / `format-python` | formatter checks |

## Notes

- act uses `catthehacker/ubuntu:act-latest` by default — first run pulls the image (~1 GB), subsequent runs are fast
- The `unable to get git ref` warning from act is harmless on a repo with no commits yet
- All generated workflows pin action SHAs for supply-chain safety and use `permissions: contents: read`

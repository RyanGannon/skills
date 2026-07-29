---
name: ralph-loop
description: Assess a software project's conformance to Ralph Wiggum Loop principles and guide the user through setting up a Level 5 autonomous coding loop. Use when the user mentions "ralph loop", "ralph wiggum", wants to set up an autonomous agent loop, asks about ralph/prompt.md, ralph/afk.sh, CLAUDE.md, or IMPLEMENTATION_PLAN.md setup, or wants to evaluate how well their project supports agentic coding workflows.
---

# Ralph Loop Skill

Guide the user from zero to a working Level 5 Ralph Wiggum loop, or assess an existing project against Ralph principles. Each iteration runs Claude Code unattended (`--print --dangerously-skip-permissions`), injecting the previous 5 commits for continuity without a persistent context window. That iteration runs inside an isolated Docker sandbox (`sbx run claude .`) when `claude` is authenticated via API key — the only case where sandboxing is possible. With subscription/OAuth login, `sbx` cannot authenticate, so the loop runs directly on the host with no isolation; always confirm with the user which case applies and make sure they understand the blast-radius difference.

## Quick Start

Run the assessment script, read key files, present a scored report, then walk the user through fixing each gap in order.

## Workflow

### Step 1 — Assess the project

Run `bash /home/goatonatrain/.claude/skills/ralph-loop/scripts/assess.sh` from the project root. Also read:
- `CLAUDE.md` (preferred) or `AGENTS.md`
- `ralph/prompt.md`, `ralph/afk.sh`, `ralph/once.sh` (if present)
- `IMPLEMENTATION_PLAN.md` (if present)
- GitHub issues — run `gh issue list --state open --limit 50` to check for PRDs and implementation tickets

Score against the five pillars (see [ASSESSMENT.md](ASSESSMENT.md)):

1. **Specifications** — Open GitHub issues with PRD + AFK implementation tickets (vertical slices)
2. **CLAUDE.md** — Build/test commands, project conventions, accumulated signs
3. **ralph/ scripts** — `afk.sh`, `once.sh`, and `prompt.md` present and correctly structured
4. **Backpressure** — Automated tests, linters, type checkers wired into `ralph/prompt.md`
5. **Implementation Plan** — A prioritised task list via GitHub Issues, Jira, or `IMPLEMENTATION_PLAN.md`

Present a summary table:

```
Pillar                  Status    Notes
──────────────────────────────────────────────────────────
Specifications          ✓ / ✗    PRD issue + N impl. tickets found / missing
CLAUDE.md               ✓ / ✗    Present with build+test commands / missing
ralph/ scripts          ✓ / ✗    afk.sh + once.sh + prompt.md present / missing
Backpressure            ✓ / ✗    [commands in prompt.md] / no checks wired in
Implementation Plan     ✓ / ✗    [tracker type] set up / not yet configured
```

### Step 2 — Guide through gaps, in order

Work through missing pillars in this exact sequence. Never skip ahead.

#### 2a. Specifications (if missing or thin)

Specs live as issues in the user's task tracker, not as files in the repo. The workflow differs by tracker:

**If using GitHub Issues:**
1. **Create the PRD** — Use the `write-a-prd` skill. It interviews the user, explores the codebase, and submits a structured PRD as a GitHub issue.
2. **Break it into tickets** — Use the `prd-to-issues` skill. It slices the PRD into independently-grabbable AFK vertical slices, each created as its own GitHub issue with acceptance criteria and blocked-by links.

**If using Jira:**
1. **Create the PRD** — Use the `write-a-prd` skill to draft the PRD content, then use the `acli-jira` skill to create it as a Jira Epic with the full PRD body.
2. **Break it into tickets** — Use the `acli-jira` skill (or `acli jira workitem create-bulk --from-csv`) to create Stories/Tasks as AFK vertical slices under the Epic, each with acceptance criteria.

These issues are the source of truth. The implementation plan and `afk.sh` arguments reference them by key.

#### 2b. CLAUDE.md (if missing or lacks build/test commands)

Ask the user:
- How do you build this project?
- How do you run tests?
- Any linters or type checkers to run?
- Anything the agent must never do (e.g. never drop tables, never push to main directly)?

**Critical:** CLAUDE.md must live at the repo root. Docker sandboxes do not mount `~/.claude` — only project-level config is available inside the sandbox. Include a **Signs** section even if empty — it grows through observation. See [TEMPLATES.md](TEMPLATES.md).

#### 2c. ralph/ scripts (if missing)

Create the `ralph/` directory with three files from [TEMPLATES.md](TEMPLATES.md):

- **`ralph/prompt.md`** — Instructions for the agent each iteration. Crucially includes the feedback loop commands (tests, type checker, linter) and the rule `ONLY WORK ON A SINGLE TASK`. Also includes the `<promise>NO MORE TASKS</promise>` termination instruction.
- **`ralph/afk.sh`** — The AFK loop. Injects the previous 5 commits and the plan+PRD content into each `claude --print --dangerously-skip-permissions` invocation. Accepts `<plan-and-prd>` and `<iterations>` arguments. Exits early on `NO MORE TASKS`. Ask the user how `claude` is authenticated: API key → wrap in `sbx run claude . --` (Docker Desktop AI Sandboxes) for real isolation; subscription/OAuth login → `sbx` won't authenticate, so it must run directly on the host with no sandbox — tell the user this explicitly, since it means every action is unmediated.
- **`ralph/once.sh`** — Single unattended iteration via `claude --print --dangerously-skip-permissions`, run directly on the host regardless of auth method (never wrapped in `sbx`). Useful for watching one full iteration before trusting a multi-iteration `afk.sh` run. `--print` is required, not optional — without it `claude` opens the interactive REPL and just hangs the moment the script is backgrounded or has no TTY.

Update `ralph/prompt.md`'s FEEDBACK LOOPS section with the actual build/test commands from `CLAUDE.md`.

#### 2d. Backpressure (if no automated checks found)

Advise the user that backpressure is the safety net. The more that exists, the more autonomy the loop can safely have. Suggest:
- A test suite (pytest, vitest, go test, jest, etc.)
- A linter (`ruff`, `eslint`, `golangci-lint`, `rubocop`)
- A type checker if the language supports it
- Pre-commit hooks to gate every commit

Do not implement these — advise and let the user decide scope. Once they exist, add them to the FEEDBACK LOOPS section of `ralph/prompt.md`.

#### 2e. Implementation Plan (if missing)

Ask the user how they track tasks for this project:

> **How do you manage your implementation plan?**
> - **GitHub Issues** — tasks live as open issues (already set up in step 2a)
> - **Jira** — tasks live in a Jira board
> - **IMPLEMENTATION_PLAN.md** — a local markdown file in the repo

**If GitHub Issues:** No file needed. The plan is composed on-the-fly from open issues at loop start. Skip to Step 3.

**If Jira:** No file needed. Ask the user for their Jira project key and verify they have `acli` authenticated (invoke the `acli-jira` skill if they need help with setup or ticket creation). The plan will be fetched via `acli` at loop start time. Skip to Step 3.

**If IMPLEMENTATION_PLAN.md (or no external tracker):** Generate the file via gap analysis:
1. Fetch open AFK implementation tickets: `gh issue list --state open`
2. Read the directory structure to identify what is already built
3. Produce a prioritised task list where each item references the GitHub issue number

Present for user review before writing.

### Step 3 — Run the loop

Once all pillars are green, show the user how to run the loop. First compose the plan+PRD content based on their tracker:

```bash
# GitHub Issues
plan=$(gh issue view <prd-issue-number>; echo "---"; gh issue list --state open)

# Jira (uses acli — run `acli jira auth login` first if not already authenticated)
plan=$(acli jira workitem search --jql "project = <PROJECT-KEY> AND status in ('To Do', 'In Progress')")

# IMPLEMENTATION_PLAN.md
plan=$(cat IMPLEMENTATION_PLAN.md)

# Run the AFK loop (N iterations)
bash ralph/afk.sh "$plan" 20
```

Or to watch a single iteration before trusting the full loop:

```bash
bash ralph/once.sh "$plan"
```

The loop injects previous 5 commits into each iteration so the agent understands what has already been done, without maintaining a persistent context window.

**Prerequisites — depends on how the user authenticates `claude`:**
- **API key** (`ANTHROPIC_API_KEY`): Docker Desktop with AI Sandboxes enabled, plus the key set in environment or Docker sandbox secrets. `afk.sh` should wrap its invocation in `sbx run claude . --` for real isolation.
- **Subscription login (OAuth, e.g. `claude login`)**: `sbx` cannot authenticate this way, so there is no sandbox option — both `afk.sh` and `once.sh` run `claude --print --dangerously-skip-permissions` directly on the host. Tell the user this plainly: every git/shell action the loop takes is unmediated, with no approval prompts and no Docker boundary. Get explicit confirmation before wiring the loop up this way.

Key reminders:
- **Watch the first several iterations.** Do not walk away. This is where you learn what signs are needed. This matters even more without Docker isolation — there is no sandbox boundary catching a bad command.
- **Signs fix mistakes.** When Ralph goes wrong, add a guardrail to `CLAUDE.md` or `ralph/prompt.md` — do not just re-run.
- **Plans are disposable.** Delete and regenerate `IMPLEMENTATION_PLAN.md` freely. Stale plans are cheaper to replace than to salvage.
- **Keep context windows single-purpose.** Discovery sessions and execution loops are separate invocations.

## Key Principles (never violate)

- One task per loop iteration — enforced by `ONLY WORK ON A SINGLE TASK` in `ralph/prompt.md`
- Fresh context every iteration — the shell loop handles this; Ralph must never be implemented as an in-session skill
- Specs live as GitHub issues (PRD + AFK vertical slices), not in-repo files
- Backpressure rejects bad output before humans see it — wired into FEEDBACK LOOPS
- Signs fix recurring failures; the prompt evolves through observation, not upfront guessing
- GitHub issues are living documents — acceptance criteria must be kept up-to-date as understanding evolves, and issues must be closed when the feature is complete

See [ASSESSMENT.md](ASSESSMENT.md) for the scoring rubric and [TEMPLATES.md](TEMPLATES.md) for all file templates.

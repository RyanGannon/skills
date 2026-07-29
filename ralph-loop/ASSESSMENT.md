# Ralph Loop Assessment Rubric

## Scoring

Each pillar scores 0–2 points. A project is **loop-ready** at 8–10. Below 6 means the loop will produce unreliable output.

| Score | Meaning |
|-------|---------|
| 2 | Fully present and well-formed |
| 1 | Partially present — functional but missing key elements |
| 0 | Missing or broken |

---

## Pillar 1: Specifications

**What to check:**
- Run `gh issue list --state open --limit 50` and scan for:
  - A PRD issue (structured problem statement, user stories, implementation decisions, acceptance criteria)
  - AFK implementation tickets that are vertical slices of the PRD (each independently implementable)
  - Issues linked to each other via "Blocked by" and "Parent PRD" references

**Score 2:** PRD issue exists AND there are multiple AFK implementation tickets with acceptance criteria, each referencing the parent PRD.

**Score 1:** Either a PRD exists without tickets, or there are tickets without a coherent PRD, or specs exist only as files in `specs/` (functional but not ideal for the loop).

**Score 0:** No specs anywhere — no PRD, no tickets, no spec files.

**Red flags:**
- Tickets that describe implementation steps rather than end-state behaviour
- No acceptance criteria (agent cannot know when it is done)
- Tickets too coarse to complete in one loop iteration

---

## Pillar 2: CLAUDE.md

**What to check:**
- Read `CLAUDE.md` at the repo root (or `AGENTS.md` if that exists instead)
- Confirm it contains: build command, test command, linter/type checker commands
- Look for a **Signs** section with accumulated guardrails

**Score 2:** File exists at repo root with explicit build + test commands AND at least a Signs section (even if empty).

**Score 1:** File exists but is missing build or test commands, or only has generic content without project-specific commands.

**Score 0:** No `CLAUDE.md` or `AGENTS.md` at the repo root.

**Red flags:**
- Commands that assume specific environment setup not available in a Docker sandbox
- Missing the Signs section (no place to accumulate guardrails)
- User-level config (`~/.claude`) referenced instead of project-level (`CLAUDE.md`)

---

## Pillar 3: ralph/ Scripts

**What to check:**
- Check `ralph/afk.sh`, `ralph/once.sh`, `ralph/prompt.md` all exist
- Read `ralph/prompt.md` and verify structure: INPUTS, RESUMPTION (uncommitted-WIP *and* unpushed/no-PR check), STAY UNATTENDED, EXPLORATION, IMPLEMENTATION, FEEDBACK LOOPS, COMMIT, FINAL RULES sections
- Read `ralph/afk.sh` and verify: injects previous 5 commits, passes plan+PRD as argument (or composes it internally for a fixed single-tracker setup), runs unattended (`--print`, with either `.claude/settings.json` fine-grained permissions, `sbx run claude .` Docker sandbox, or `--dangerously-skip-permissions` as fallback), checks for `NO MORE TASKS` termination, and stops cleanly (via `${PIPESTATUS[0]}`, not the pipeline's aggregate exit code, rather than crashing or looping blind) if the `claude` invocation itself fails
- Verify `ralph/prompt.md` includes `<promise>NO MORE TASKS</promise>` instruction
- Verify `ralph/prompt.md` includes `ONLY WORK ON A SINGLE TASK`
- Verify `ralph/prompt.md` includes a RESUMPTION check (`git status`/branch for uncommitted WIP *and* unpushed/no-PR commits) before task selection — otherwise an iteration interrupted mid-task leaves work a fresh iteration has no way to discover, since only committed state is injected
- Verify `ralph/prompt.md` includes a STAY UNATTENDED section telling the agent it must never stop mid-iteration to ask a question or wait on approval, and that a task's own acceptance criteria are the human's advance authorization for whatever they explicitly call for — otherwise the agent will do the reasonable-looking thing and stop to confirm a risky/gated action, which just hangs forever since nobody is watching an unattended `--print` run
- If `.claude/settings.json` is present, confirm the workspace trust dialog has actually been accepted (`hasTrustDialogAccepted` for the project in `~/.claude.json`) — otherwise its `permissions.allow` entries are silently ignored
- Check whether `afk.sh`/`once.sh` run from a dedicated `git worktree` (a sibling directory reused across invocations) rather than the primary checkout — relevant once either script gets backgrounded rather than watched directly

**Score 2:** All three files present. `afk.sh` injects commits and runs unattended via one of: `.claude/settings.json` fine-grained permissions (preferred — requires the workspace to be trusted), `sbx run claude .` Docker sandbox (API-key auth only), or `--dangerously-skip-permissions` (fallback, any auth). It checks `${PIPESTATUS[0]}` (not just the pipeline's overall exit status) after the `claude` call and stops cleanly with diagnostic output on failure rather than crashing blind or retrying pointlessly. `prompt.md` has correct structure including termination instruction, the RESUMPTION check (uncommitted WIP and unpushed/no-PR commits), and the STAY UNATTENDED never-ask rule.

**Score 1:** Some files present but missing elements (e.g. `prompt.md` exists but `afk.sh` is absent, `afk.sh` doesn't inject commits, it runs unattended but has no handling for a failed `claude` call, or `prompt.md` has no RESUMPTION or STAY UNATTENDED section).

**Score 0:** `ralph/` directory does not exist.

**Red flags:**
- `afk.sh` missing `--print` — without it `claude` opens the interactive REPL and hangs waiting on a TTY, breaking silently the moment it's run unattended
- `afk.sh` running host-direct with `--dangerously-skip-permissions` when a smaller-blast-radius option was never considered (a Docker sandbox if API-key auth exists, or a `.claude/settings.json` allow/deny list otherwise)
- Any unmediated-execution choice (bypass, sandbox, or fine-grained permissions) that hasn't been explicitly flagged to the user as such, with its blast radius — this must be a deliberate, confirmed choice, not silently assumed
- `.claude/settings.json` present but the workspace trust dialog hasn't been accepted — looks like the loop is broken (everything gets denied) when it's actually a trust-state issue
- `afk.sh` trusts the pipeline's aggregate exit status instead of `${PIPESTATUS[0]}` — with `set -o pipefail`, a failing `claude` call can still return overall success if the downstream `jq`/`grep` stages succeed on empty or partial input, silently swallowing the failure
- No handling at all for a `claude` invocation failure (e.g. a subscription usage-limit hit) — the loop should stop cleanly and note that state is safe to resume from, not crash uninformatively or hang
- `prompt.md` has no check for uncommitted WIP, or a commit made but never pushed/PR'd, from an interrupted prior iteration before picking a new task — the agent will either ignore half-finished work or start a second task on top of it
- `prompt.md` has no STAY UNATTENDED section — the agent will stop mid-iteration to ask a question on a sandbox/permission rejection instead of checking whether the task's own acceptance criteria already authorize the gated action, and the loop hangs with no one to answer
- `afk.sh`/`once.sh` operate directly in the primary checkout with no worktree isolation, while also being run backgrounded — a concurrent human `git checkout`/commit in the same directory is a real collision risk
- No iteration limit in `afk.sh` (infinite loop with no escape)
- Backgrounded run logs redirected to an ephemeral session-scoped temp/scratchpad directory instead of a durable path — unreadable after the fact if the environment resets it
- FEEDBACK LOOPS section in `prompt.md` contains placeholder commands not matching the actual project

---

## Pillar 4: Backpressure

**What to check:**
- Look for test configuration files: `pytest.ini`, `vitest.config.*`, `jest.config.*`, `go.sum`, etc.
- Look for linter configs: `.eslintrc*`, `ruff.toml`, `.golangci.yml`, etc.
- Look for type checker config: `tsconfig.json`, `mypy.ini`, `pyrightconfig.json`, etc.
- Look for pre-commit hooks: `.pre-commit-config.yaml`, `.git/hooks/pre-commit`
- Cross-reference: are these commands actually referenced in `ralph/prompt.md`'s FEEDBACK LOOPS section?

**Score 2:** At least tests + one of (linter, type checker) exist AND are wired into `ralph/prompt.md`'s FEEDBACK LOOPS.

**Score 1:** Automated checks exist in the project but are not wired into `ralph/prompt.md`, or they exist in `prompt.md` but aren't actually set up in the project.

**Score 0:** No automated checks exist anywhere.

**Red flags:**
- Tests exist but `ralph/prompt.md` doesn't run them (agent commits without validation)
- Verbose test output not suppressed (wastes context tokens; only failures should be shown)
- Linter configured to warn-only (not failing the build means the agent ignores it)

---

## Pillar 5: Implementation Plan

The plan can live in GitHub Issues, Jira, or a local `IMPLEMENTATION_PLAN.md` file. First establish which the user is using, then score accordingly.

**What to check:**

*GitHub Issues (preferred when Specifications pillar is also GitHub Issues):*
- Open AFK implementation tickets exist with acceptance criteria and priority order
- No separate file needed — the plan is composed on-the-fly from open issues

*Jira:*
- Confirm the user has a Jira project key and open tickets covering the work
- Confirm `acli` is installed and authenticated (`acli jira auth login`)
- No separate file needed — the plan is fetched via `acli jira workitem search` at loop start time

*IMPLEMENTATION_PLAN.md:*
- Read `IMPLEMENTATION_PLAN.md` at the repo root
- Confirm each item references a GitHub issue number
- Check that completed items are marked (strikethrough, checkbox, or status field)
- Verify the plan is not stale (compare against open GitHub issues)

**Score 2:** Plan source is clearly established (GitHub Issues, Jira, or IMPLEMENTATION_PLAN.md), is up-to-date, and has a clear priority order. If a file, it references issue numbers.

**Score 1:** A plan source exists but is incomplete — e.g. a file with no issue references, Jira tickets with no priority order, or GitHub Issues that exist but were never reviewed against current state.

**Score 0:** No plan anywhere — no file, no tickets, no tracker configured.

**Red flags:**
- Plan describes implementation steps rather than outcomes (agent cannot know when done)
- IMPLEMENTATION_PLAN.md in use alongside GitHub Issues or Jira with no clear reason — likely redundant and will drift out of sync
- Plan not updated after loop iterations (defeats the purpose of the `Update plan` step in `ralph/prompt.md`)

---

## Common Failure Patterns to Flag

| Pattern | Likely Cause | Sign to Add |
|---------|-------------|-------------|
| Duplicate code | ripgrep false negative | "Before making changes, search the codebase. Never assume something is not implemented." |
| Agent uses wrong library | No pattern in codebase | Add a utility using the correct library; Ralph will discover it |
| Tests pass but behaviour is wrong | Tests too shallow | Add integration or snapshot tests |
| Plan drifts from specs | Loop ran too long without review | Regenerate plan from current open issues |
| Agent marks tasks done prematurely | Acceptance criteria too vague | Tighten the GitHub issue acceptance criteria |
| Sandbox can't find build tools | Tools not in Docker image | Add install step to `ralph/prompt.md` or use a custom sandbox image |
| Bash calls denied with no one to approve them | A Bash-level `PreToolUse` hook (e.g. a command-rewriting proxy) treats compound `&&`-chained commands as needing separate approval, which can't be satisfied in headless `--print` mode | Keep the `.claude/settings.json` allow-list scoped to the exact single commands the loop runs; avoid `&&`-chaining in `ralph/prompt.md` guidance where practical |
| Loop "completes" iterations doing nothing after a crash/usage-limit hit | `afk.sh` isn't checking `claude`'s real exit code (see Pillar 3) | Add the `${PIPESTATUS[0]}` check from the `afk.sh` template |
| Fresh iteration redoes or ignores prior WIP after an interruption | `prompt.md` has no uncommitted-WIP check; only committed state is injected | Add the RESUMPTION section from the `prompt.md` template |
| A fresh iteration skips a task whose branch already has a committed-but-unpushed/no-PR commit from a prior run | RESUMPTION check only looked for *uncommitted* changes, not unpushed commits, so the WIP was invisible to the next iteration | Extend the RESUMPTION check to also cover unpushed/no-PR commits (see the `prompt.md` template) |
| Loop's own git operations collide with a human's concurrent work in the same checkout | `afk.sh`/`once.sh` run in the primary checkout instead of a dedicated worktree | Add worktree isolation from the `afk.sh`/`once.sh` templates |
| Loop stops mid-iteration asking whether to proceed with a network call, destructive action, or other gated step, and just hangs since it's unattended | `prompt.md` has no STAY UNATTENDED section, so the agent falls back to general "confirm risky actions with the user" instinct even though nobody is watching | Add the STAY UNATTENDED section from the `prompt.md` template — a task's acceptance criteria are the human's advance authorization for whatever they explicitly call for |

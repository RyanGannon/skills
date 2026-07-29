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
- Read `ralph/prompt.md` and verify structure: INPUTS, EXPLORATION, IMPLEMENTATION, FEEDBACK LOOPS, COMMIT, FINAL RULES sections
- Read `ralph/afk.sh` and verify: injects previous 5 commits, passes plan+PRD as argument, runs unattended (`--print --dangerously-skip-permissions`, optionally wrapped in `sbx run claude .`), checks for `NO MORE TASKS` termination
- Verify `ralph/prompt.md` includes `<promise>NO MORE TASKS</promise>` instruction
- Verify `ralph/prompt.md` includes `ONLY WORK ON A SINGLE TASK`

**Score 2:** All three files present. `afk.sh` injects commits and runs unattended — via Docker sandbox (`sbx run claude .`) if the user has API-key auth, or directly on host (`--dangerously-skip-permissions`, no `sbx`) if they're on subscription/OAuth login, since `sbx` cannot authenticate that way. `prompt.md` has correct structure including termination instruction.

**Score 1:** Some files present but missing elements (e.g. `prompt.md` exists but `afk.sh` is absent, or `afk.sh` doesn't inject commits).

**Score 0:** `ralph/` directory does not exist.

**Red flags:**
- `afk.sh` missing `--print` — without it `claude` opens the interactive REPL and hangs waiting on a TTY, breaking silently the moment it's run unattended
- `afk.sh` running host-direct with `--dangerously-skip-permissions` when the user *does* have API-key auth available (should be wrapped in `sbx run claude .` for isolation instead)
- Host-direct `--dangerously-skip-permissions` (subscription/OAuth case) that hasn't been explicitly flagged to the user as unmediated/unsandboxed — this must be a deliberate, confirmed choice, not silently assumed
- No iteration limit in `afk.sh` (infinite loop with no escape)
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

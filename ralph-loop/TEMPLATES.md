# Ralph Loop File Templates

## ralph/prompt.md

This is the core prompt injected into every loop iteration, alongside the previous 5 commits and the plan+PRD content. Substitute `[TEST COMMAND]`, `[TYPECHECK COMMAND]`, and `[LINT COMMAND]` with the actual commands from `CLAUDE.md`.

```markdown
# INPUTS

A PRD and plan have been provided to you. Read these to understand the task.

You've also been passed a file containing the last few commits. Review these to understand what work has been done.

If there are no more tasks to complete, output <promise>NO MORE TASKS</promise>.

# RESUMPTION

First, run `git status` and check the current branch. If it's not the main branch and has uncommitted changes, or has commits not yet pushed/PR'd, that's WIP from an iteration that got interrupted mid-task (e.g. a `claude` failure or usage-limit hit) — continue that work (push, open the PR, etc.) instead of picking a new task or discarding it.

This matters because resumability otherwise assumes all state lives in the injected commits — but an interruption mid-iteration can leave *uncommitted* work, or a commit made but never pushed/PR'd, that the next fresh iteration has no other way to discover.

Otherwise, proceed to task selection below.

# STAY UNATTENDED

This loop runs via `claude --print` with no one watching in real time — output is only read later, if at all. Never stop mid-iteration to ask a question or wait on a permission/approval prompt: nobody is there to answer it, so the loop just hangs until a human happens to check the transcript. If you find yourself about to ask something, that means the decision actually needed to be made *before* this iteration started — resolve what you can from the task's own spec, `CLAUDE.md`, and past commits, note any genuinely open question as a Sign or a comment on the task, and either proceed on the best-supported interpretation or close out the iteration cleanly (commit WIP, leave the task claimed, explain what's blocking) rather than stalling on a question.

This includes sandbox/permission rejections. Commands outside the configured allow-list, or requiring elevated access (e.g. network egress), will be rejected in this non-interactive mode with no way to approve them live. Before treating that as a blocker to ask about, check whether the current task's own acceptance criteria explicitly call for the gated action — if so, the human already pre-authorized it by writing that acceptance criterion and marking the task ready for the loop to pick up, and you should proceed rather than stop. Do not extend this reasoning beyond what the acceptance criteria actually say, and never use it to route around a rejection on an action the task doesn't call for.

# EXPLORATION

Explore the repo. Before making changes, search the codebase — do not assume something is not implemented.

# IMPLEMENTATION

Complete the task. Follow existing patterns in the codebase.

# FEEDBACK LOOPS

Before committing, run the feedback loops:

- `[TEST COMMAND]` to run the tests
- `[TYPECHECK COMMAND]` to run the type checker
- `[LINT COMMAND]` to run the linter

If any check fails, fix the issue before proceeding.

# COMMIT

Make a git commit. The commit message must:

1. Include key decisions made
2. Include files changed
3. Blockers or notes for next iteration

# GITHUB ISSUES

When working on a task tied to a GitHub issue:

- Keep the acceptance criteria on the issue up-to-date as your understanding evolves
- When the feature is complete and all checks pass, close the issue with `gh issue close <number>`

# JIRA (if using Jira)

When working on a task tied to a Jira ticket:

- When the feature is complete and all checks pass, transition the ticket to Done with `acli jira workitem transition -k <KEY> -s Done -y`

# FINAL RULES

ONLY WORK ON A SINGLE TASK.
```

---

## ralph/afk.sh

The AFK loop script. Injects previous 5 commits and plan+PRD content into every iteration. Exits early when no more tasks remain, or when `claude` itself fails — checked via `${PIPESTATUS[0]}`, not the pipeline's aggregate exit status, since `set -o pipefail` alone isn't enough: downstream `jq`/`grep` stages can still exit 0 even when `claude` failed upstream, silently masking the failure. On a `claude` failure the script prints the raw output and stops rather than crashing uninformatively or looping blind; this is what catches a subscription usage-limit hit gracefully — state lives in git commits and GitHub issues, not in the script, so it's always safe to just rerun the script later to resume.

**Unmediated execution — pick one:**
1. **Fine-grained permissions (preferred)** — no bypass flag at all; rely on a `.claude/settings.json` allow/deny list (template below) plus an accepted workspace trust dialog. Smallest blast radius: unlisted operations are denied, not silently allowed. Works with any auth method.
2. **Docker sandbox (API-key auth only)** — prepend `sbx run claude . --` in place of `claude` for real isolation. `sbx` cannot authenticate via subscription/OAuth login.
3. **Blanket bypass (fallback)** — append `--dangerously-skip-permissions`. Works with any auth method but has no isolation and no rule enforcement; every action is unmediated. Get explicit user confirmation before using this as the default, not just when it's the only option available.

**Worktree isolation:** run the loop from a dedicated `git worktree` (a sibling directory, e.g. `<repo>-ralph-worktree`), not the primary checkout. This keeps the loop's own `checkout`/`commit`/`push`/merge operations from colliding with anything a human is doing in the primary checkout at the same time — a real risk if `afk.sh` is backgrounded while someone else runs git commands in the same directory. Create the worktree once (branched off `origin/main`) and reuse it on every subsequent invocation, so an interrupted iteration's uncommitted WIP (see the RESUMPTION section above) is still there next time either script runs. Two things this doesn't fully solve:
- **Workspace trust is keyed per absolute path.** A freshly created worktree needs its own one-time trust-dialog acceptance — it does not inherit trust from the primary checkout.
- **`do-work`-style branch steps that check out local `main` before branching** will fail inside the worktree if the primary checkout is *also* on `main` at that moment (git refuses to have the same branch checked out in two worktrees). This fails loudly rather than corrupting anything, but the practical mitigation is: don't park the primary checkout on `main` while the loop is running.

Template below is the fine-grained-permissions form (option 1) with worktree isolation; swap in `sbx run claude . --` or add `--dangerously-skip-permissions` per the options above if the user picks differently.

```bash
#!/bin/bash
set -eo pipefail

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <plan-and-prd> <iterations>"
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_DIR="${REPO_ROOT}-ralph-worktree"

if [ ! -d "$WORKTREE_DIR" ]; then
  echo "Setting up dedicated ralph worktree at $WORKTREE_DIR (keeps the loop's branch/commit/merge operations off this checkout)..."
  git -C "$REPO_ROOT" fetch origin main
  git -C "$REPO_ROOT" worktree add "$WORKTREE_DIR" -b ralph-work origin/main
  echo ""
  echo "NOTE: workspace trust is keyed per absolute path and won't carry over from $REPO_ROOT."
  echo "If claude hangs or errors on the first iteration below, run 'claude' interactively once in $WORKTREE_DIR to accept the trust dialog, then rerun this script."
  echo ""
fi

cd "$WORKTREE_DIR"

# jq filter to extract streaming text from assistant messages
stream_text='select(.type == "assistant").message.content[]? | select(.type == "text").text // empty | gsub("\n"; "\r\n") | . + "\r\n\n"'

# jq filter to extract final result
final_result='select(.type == "result").result // empty'

for ((i=1; i<=$2; i++)); do
  tmpfile=$(mktemp)
  rawfile=$(mktemp)
  trap "rm -f $tmpfile $rawfile" EXIT

  commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
  prompt=$(cat ralph/prompt.md)

  set +e
  claude \
    --verbose \
    --print \
    --output-format stream-json \
    "Previous commits: $commits Plan and PRD: $1 $prompt" 2>&1 \
  | tee "$rawfile" \
  | grep --line-buffered '^{' \
  | tee "$tmpfile" \
  | jq --unbuffered -rj "$stream_text"
  claude_exit=${PIPESTATUS[0]}
  set -e

  if [ "$claude_exit" -ne 0 ]; then
    echo ""
    echo "Ralph stopped after $i iteration(s): claude exited with status $claude_exit."
    echo "This may be a subscription usage-limit hit — state lives in git commits and GitHub issues, so it's safe to just rerun this script later to resume."
    echo "Raw output from the failed iteration:"
    cat "$rawfile"
    exit 2
  fi

  result=$(jq -r "$final_result" "$tmpfile")

  if [[ "$result" == *"<promise>NO MORE TASKS</promise>"* ]]; then
    echo "Ralph complete after $i iterations."
    exit 0
  fi
done
```

**Why the exit-code check matters:** without capturing `${PIPESTATUS[0]}` (the exit status of `claude`, not of the trailing `jq`/`grep` in the pipeline — plain `$?` would only ever see `jq`'s status), a `claude` crash or a subscription usage-limit hit is silently swallowed: the loop just reads an empty/stale `$tmpfile`, finds no `NO MORE TASKS` marker, and burns through the remaining iteration budget doing nothing. This was validated in production — a real usage-limit hit (`"You've hit your session limit · resets Xpm"`) was correctly caught, printed with the raw diagnostic output, and exited with status 2 instead of masking the failure.

**Optional simplification for GitHub-Issues-only projects:** if the plan tracker is always GitHub Issues with a fixed PRD issue number, bake the `plan=$(...)` composition directly into the script (re-fetched inside the loop, each iteration, so closed issues drop off the list as work progresses) instead of requiring the caller to pass it as an argument every time:

```bash
# Replace the `$1` plan argument and usage check with:
if [ -z "$1" ]; then
  echo "Usage: $0 <iterations>"
  exit 1
fi
# ...then inside the loop, alongside commits/prompt:
plan=$(gh issue view <prd-issue-number>; echo "---"; gh issue list --state open --limit 50)
# ...and reference $plan instead of $1 in the claude invocation.
```

This only fits the single-tracker, fixed-PRD case — keep the argument-based form for projects using Jira or `IMPLEMENTATION_PLAN.md`, or multiple PRDs.

---

## ralph/once.sh

A single unattended iteration — useful for watching one full iteration end-to-end before committing to a multi-iteration `afk.sh` run, and as a dry run to observe exactly which tools/commands the agent actually needs. That observation is the fastest way to derive an accurate `.claude/settings.json` allow list: afterwards, read the session transcript (`~/.claude/projects/<project-slug>/*.jsonl`, matched by its `Previous commits:` prompt prefix) and look at its `tool_use` entries for the real command patterns used.

Same `claude --print` core and the same three unmediated-execution options as `afk.sh` (fine-grained permissions preferred, Docker sandbox for API-key auth, blanket bypass as fallback — see above). `--print` is required, not optional — without it `claude` opens the interactive REPL and hangs waiting on a TTY, silently breaking the script the moment it's backgrounded or run under `nohup`.

If using the blanket-bypass fallback, treat it with real caution: every git/shell action it takes is unmediated. It is not a safer "supervised" mode just because it's a single iteration — watch its output live rather than backgrounding it blind. The same applies to the worktree-isolation reasoning above: even a single iteration should run from the dedicated worktree, not the primary checkout, if a human might be doing anything else in the repo at the same time.

```bash
#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ./ralph/once.sh <plan-and-prd>"
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_DIR="${REPO_ROOT}-ralph-worktree"

if [ ! -d "$WORKTREE_DIR" ]; then
  echo "Setting up dedicated ralph worktree at $WORKTREE_DIR (keeps the loop's branch/commit/merge operations off this checkout)..."
  git -C "$REPO_ROOT" fetch origin main
  git -C "$REPO_ROOT" worktree add "$WORKTREE_DIR" -b ralph-work origin/main
  echo ""
  echo "NOTE: workspace trust is keyed per absolute path and won't carry over from $REPO_ROOT."
  echo "If claude hangs or errors below, run 'claude' interactively once in $WORKTREE_DIR to accept the trust dialog, then rerun this script."
  echo ""
fi

cd "$WORKTREE_DIR"

commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
prompt=$(cat ralph/prompt.md)

claude --print \
  "Previous commits: $commits Plan and PRD: $1 $prompt"
```

(Drop the `$1`/usage-check block and add the equivalent `plan=$(...)` line before the final `claude` call if using the baked-in-plan simplification described above for `afk.sh`.)

---

## .claude/settings.json

Only needed for the fine-grained-permissions option (see `ralph/afk.sh` above). Requires the workspace trust dialog to be accepted — otherwise every `permissions.allow` entry is silently ignored and all actions get denied, which looks like a broken loop rather than an untrusted workspace.

Derive the allow list from `ralph/prompt.md`'s FEEDBACK LOOPS/COMMIT/GITHUB ISSUES sections and `CLAUDE.md`'s build/test/lint commands first, then tighten it against a real `ralph/once.sh` dry run's session transcript for anything task-specific those don't predict.

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Write",
      "Edit",
      "Glob",
      "Grep",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git branch:*)",
      "Bash(git log:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git checkout -b:*)",
      "Bash(git push -u origin:*)",
      "Bash(gh issue list:*)",
      "Bash(gh issue view:*)",
      "Bash(gh issue edit:*)",
      "Bash(gh issue close:*)",
      "Bash(gh pr create:*)",
      "Bash(gh pr checks:*)",
      "Bash(gh pr merge:*)",
      "Bash([TEST COMMAND]:*)",
      "Bash([LINT COMMAND]:*)",
      "Bash([TYPECHECK COMMAND]:*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git push origin main:*)",
      "Bash(git reset --hard:*)",
      "Bash(git clean -fd:*)",
      "Bash(git commit --no-verify:*)",
      "Bash(rm -rf:*)",
      "Bash(sudo:*)",
      "Bash(gh repo delete:*)",
      "Bash(gh secret:*)",
      "Bash(gh api:*)",
      "Read(**/.env)",
      "Read(~/.ssh/**)",
      "Read(**/credentials*)"
    ]
  }
}
```

Substitute `[TEST COMMAND]`, `[LINT COMMAND]`, `[TYPECHECK COMMAND]` with the real command prefixes from `CLAUDE.md` (e.g. `poetry run pytest`, `poetry run ruff check .`, `poetry run mypy`), and swap `main` in the deny list for whatever the project's actual default branch is.

These rules are prefix/glob string matches, not semantic parsing — they reduce but don't guarantee against an unanticipated command shape. If the target branch has no GitHub branch-protection rule (check `gh api repos/<owner>/<repo>/branches/<branch>/protection` — needs GitHub Pro or a public repo), this deny list is the *only* backstop against a direct push to it. Say this plainly to the user rather than presenting it as airtight.

---

## CLAUDE.md

Project-level configuration available inside Docker sandboxes. Must live at the repo root.

```markdown
# Project Name

## Build

[command to build the project]

## Test

[command to run tests]

## Lint / Type Check

[command to run linter]
[command to run type checker]

## Signs

Things the agent has learned to avoid (add here as issues are observed):

- [Add guardrails here as the loop runs and mistakes are observed]

## Conventions

- [Project-specific patterns the agent should follow]
- [Libraries to use / avoid]
- [Anything the agent must never do]
```

---

## IMPLEMENTATION_PLAN.md

**Only needed if you are not using GitHub Issues or Jira as your plan tracker.** If you are using either of those, the plan is composed on-the-fly from open tickets and this file is redundant.

Generated from open GitHub issues. Each item references the issue number it comes from.

```markdown
# Implementation Plan

Generated from open GitHub issues on [DATE]. Regenerate freely when stale.

## In Progress

- [ ] #[issue-number] — [task title]

## Pending

- [ ] #[issue-number] — [task title] *(blocked by #[issue-number])*
- [ ] #[issue-number] — [task title]
- [ ] #[issue-number] — [task title]

## Completed

- [x] #[issue-number] — [task title]
```

---

## Running the Loop

Once all files are in place, compose the plan+PRD content from your tracker and run:

```bash
# GitHub Issues
plan=$(gh issue view <prd-issue-number>; echo "---"; gh issue list --state open)

# Jira (uses acli — run `acli jira auth login` first if not already authenticated)
plan=$(acli jira workitem search --jql "project = <PROJECT-KEY> AND status in ('To Do', 'In Progress')")

# IMPLEMENTATION_PLAN.md
plan=$(cat IMPLEMENTATION_PLAN.md)

# Run AFK loop for up to 20 iterations
bash ralph/afk.sh "$plan" 20

# Or run a single supervised iteration
bash ralph/once.sh "$plan"
```

If `afk.sh` stops early (exit code 2 — a `claude` failure, e.g. a usage-limit hit), no special recovery is needed: state lives in git commits and GitHub issues, not in the script, so just rerun the same command later to resume where it left off.

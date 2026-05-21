# Ralph Loop File Templates

## ralph/prompt.md

This is the core prompt injected into every loop iteration, alongside the previous 5 commits and the plan+PRD content. Substitute `[TEST COMMAND]`, `[TYPECHECK COMMAND]`, and `[LINT COMMAND]` with the actual commands from `CLAUDE.md`.

```markdown
# INPUTS

A PRD and plan have been provided to you. Read these to understand the task.

You've also been passed a file containing the last few commits. Review these to understand what work has been done.

If there are no more tasks to complete, output <promise>NO MORE TASKS</promise>.

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

The AFK loop script. Injects previous 5 commits and plan+PRD content into every iteration. Exits early when no more tasks remain.

```bash
#!/bin/bash
set -eo pipefail

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <plan-and-prd> <iterations>"
  exit 1
fi

# jq filter to extract streaming text from assistant messages
stream_text='select(.type == "assistant").message.content[]? | select(.type == "text").text // empty | gsub("\n"; "\r\n") | . + "\r\n\n"'

# jq filter to extract final result
final_result='select(.type == "result").result // empty'

for ((i=1; i<=$2; i++)); do
  tmpfile=$(mktemp)
  trap "rm -f $tmpfile" EXIT

  commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
  prompt=$(cat ralph/prompt.md)

  sbx run claude . -- \
    --verbose \
    --print \
    --output-format stream-json \
    "Previous commits: $commits Plan and PRD: $1 $prompt" \
  | grep --line-buffered '^{' \
  | tee "$tmpfile" \
  | jq --unbuffered -rj "$stream_text"

  result=$(jq -r "$final_result" "$tmpfile")

  if [[ "$result" == *"<promise>NO MORE TASKS</promise>"* ]]; then
    echo "Ralph complete after $i iterations."
    exit 0
  fi
done
```

---

## ralph/once.sh

Single interactive run, useful for supervised intervention or testing. Uses `--permission-mode acceptEdits` so the user can review each action.

```bash
#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ./ralph/once.sh <plan-and-prd>"
  exit 1
fi

commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
prompt=$(cat ralph/prompt.md)

claude --permission-mode acceptEdits \
  "Previous commits: $commits Plan and PRD: $1 $prompt"
```

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

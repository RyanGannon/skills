# ralph-loop skill

A Claude Code skill that assesses a project's readiness for the Ralph Wiggum Loop and guides the user through setting one up from scratch.

## What it does

The Ralph Wiggum Loop is a Level 5 autonomous coding technique: Claude Code runs in an infinite loop inside an isolated `sbx` sandbox, picking one task per iteration from a prioritised implementation plan, implementing it, running the feedback loops, committing, and exiting. The next iteration picks up from the git history.

This skill:
1. **Assesses** a project against five pillars of Ralph loop readiness
2. **Guides** the user through creating anything that is missing, in the correct order
3. **Produces** the `ralph/` scripts and `CLAUDE.md` needed to run the loop

## Trigger

Use this skill when the user says:
- "ralph loop", "ralph wiggum", "set up a ralph loop"
- "assess my project for agentic coding"
- Asks about `ralph/afk.sh`, `ralph/prompt.md`, `IMPLEMENTATION_PLAN.md`

## Files

```
ralph-loop/
├── SKILL.md          # Main workflow — loaded by Claude Code
├── ASSESSMENT.md     # Scoring rubric for the five pillars
├── TEMPLATES.md      # Copy-paste templates for all generated files
├── README.md         # This file
└── scripts/
    └── assess.sh     # Structural fact-gathering script
```

## The five pillars

| Pillar | What it checks |
|--------|---------------|
| Specifications | GitHub issues: a PRD + AFK vertical-slice implementation tickets |
| CLAUDE.md | Build/test commands + accumulated signs, at the repo root |
| ralph/ scripts | `afk.sh`, `once.sh`, `prompt.md` — correctly structured |
| Backpressure | Tests, linters, type checkers wired into `ralph/prompt.md` |
| Implementation Plan | `IMPLEMENTATION_PLAN.md` referencing GitHub issue numbers |

## Generated project structure

After running the skill, a project will have:

```
my-project/
├── CLAUDE.md                  # Agent config (signs, build/test commands)
├── IMPLEMENTATION_PLAN.md     # Prioritised task list referencing GitHub issues
└── ralph/
    ├── afk.sh                 # AFK loop script
    ├── once.sh                # Single supervised run
    └── prompt.md              # Per-iteration agent instructions
```

## Running the scripts

### Prerequisites

```bash
# Install and authenticate sbx
sbx login

# Set your Anthropic API key
sbx secret set -g anthropic
# or: export ANTHROPIC_API_KEY=sk-ant-...
```

### AFK loop (unattended, N iterations)

```bash
# Fetch the PRD and open implementation tickets as the plan content
plan=$(gh issue view 42; echo "---"; gh issue list --state open)

# Run up to 20 iterations — exits early if no tasks remain
bash ralph/afk.sh "$plan" 20
```

The loop injects the previous 5 commits into every iteration so the agent knows what has already been done. It exits automatically when the agent outputs `<promise>NO MORE TASKS</promise>`.

### Single supervised run

```bash
plan=$(gh issue view 42; echo "---"; gh issue list --state open)

# Runs once with --permission-mode acceptEdits so you can review each action
bash ralph/once.sh "$plan"
```

Use `once.sh` to test the setup before going AFK, or to intervene after the loop produces something unexpected.

### Regenerating the implementation plan

Plans go stale. Delete and regenerate freely:

```bash
rm IMPLEMENTATION_PLAN.md
# Then ask Claude to regenerate it from the open GitHub issues
```

## Skill dependencies

The `ralph-loop` skill delegates to two other skills when setting up specifications:

- **`write-a-prd`** — interviews the user and creates a structured PRD as a GitHub issue
- **`prd-to-issues`** — breaks the PRD into AFK vertical-slice implementation tickets

Both must be installed for the full setup workflow to work.

## Key principles

- **One task per iteration** — enforced by `ONLY WORK ON A SINGLE TASK` in `ralph/prompt.md`
- **Fresh context every iteration** — `sbx run` spawns a new process each time; never implement Ralph inside a long-lived session
- **Specs in GitHub issues** — not files; the plan references issue numbers
- **CLAUDE.md at the repo root** — `sbx` sandboxes do not mount `~/.claude`; only project-level config is available
- **Signs fix mistakes** — when Ralph goes wrong, add a guardrail to `CLAUDE.md` or `ralph/prompt.md`, do not just re-run

## References

- [The Ralph Wiggum Loop (ghuntley.com)](https://ghuntley.com/ralph/)
- [Docker AI Sandboxes](https://docs.docker.com/ai/sandboxes/)
- [sbx with Claude Code](https://docs.docker.com/ai/sandboxes/agents/claude-code/)
- [Example ralph/ scripts (RyanGannon)](https://github.com/RyanGannon/cohort-003-project-fork/tree/main/ralph)

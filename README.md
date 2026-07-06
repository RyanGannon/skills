# skills

Claude Code skills that augment existing CLI tools with AI intelligence. The tools do the heavy lifting; AI handles context, decision-making, and error recovery.

## Philosophy

**Use the right tool for the job. Use AI for what the tool cannot do.**

Every skill in this repo wraps a real CLI tool. The tool executes the work; the skill adds the layer of intelligence that makes the tool genuinely useful in an agentic context: interpreting output, diagnosing failures, choosing the right flags, and recovering from errors.

This keeps token usage efficient. If `acli` can create a Jira ticket, it does — the skill is there to translate intent into the right command, not to reinvent the wheel.

## Skills

| Skill | Wraps | What AI adds |
|---|---|---|
| [act-workflows](act-workflows/SKILL.md) | `act` | Parallel job execution, failure diagnosis, and fixes for common act compatibility issues |
| [audit-memories-to-skills](audit-memories-to-skills/SKILL.md) | `~/.claude` memory & skill files | Classifies memories as state-vs-procedure, promotes the reusable ones into skills, retires duplicates, and repairs indexes and wikilinks |
| [commit](commit/SKILL.md) | `git` | Conventional commit formatting, issue number detection, logical change splitting |
| [fix-github-workflow](fix-github-workflow/SKILL.md) | `gh` + `act` | CI failure diagnosis, fix application, local validation loop, watching the outcome |
| [gabo-workflows](gabo-workflows/SKILL.md) | `gabo` + `act` | Workflow type selection, generation orchestration, then hands off to act-workflows for testing |
| [ralph-loop](ralph-loop/SKILL.md) | `claude` + Docker sandboxes | Assesses Ralph conformance, guides setup across all five pillars, enforces the principles |

## Installation

```bash
pnpm dlx skills@latest add RyanGannon/skills
```

To update:

```bash
pnpm dlx skills@latest update
```

## How skills are built

Skills that encode expert knowledge follow a three-step pipeline:

1. **Refine the source** — Run a raw transcript (video or talk) through a transcript refiner script to clean it up
2. **Research and synthesise** — Pass the refined transcript to Claude with a prompt that expands knowledge via web search, resolves conflicts by favouring the creator's own words, and produces a structured introduction document
3. **Generate the skill** — Pass the document to `/write-a-skill`

The ralph-loop skill was built this way, starting from Geoffrey Huntley's talk ["The Ralph Wiggum Loop from 1st principles"](https://www.youtube.com/watch?v=4Nna09dG_c0).

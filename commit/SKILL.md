---
name: commit
description: Create git commits using conventional commits format, with issue number prepended to the description, splitting into multiple commits when there are multiple significant changes. Use when the user says /commit, wants to commit changes, or asks to stage and commit work.
model: haiku
---

# Commit

## Quick start

1. Run `git status` and `git diff` to understand all changes
2. Detect the linked issue number (see below)
3. Group changes into logical units
4. Commit each group separately using conventional commit format

## Issue number detection

Check for an issue number in this order:
1. Current branch name — extract from patterns like `123-feature-name` or `feature/123-foo`
2. Ask the user if no issue number is found and none is provided

Prepend the issue number to the description: `feat: #42 add login page`

## Conventional commit format

```
<type>(<scope>): #<issue> <description>

[optional body]

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `style`, `perf`, `ci`, `build`, `revert`

**Scope**: optional, use the module/area name (e.g. `auth`, `api`, `db`)

**Breaking changes**: append `!` after type/scope and add `BREAKING CHANGE:` in the body

## Splitting into multiple commits

Split when changes span more than one logical concern:

- New feature code + its tests → one commit each, or combined as `feat: #42 add X with tests`
- Unrelated bug fix alongside a feature → always separate
- Refactor that precedes a feature → separate `refactor:` commit first
- Config/tooling change alongside app code → separate `chore:` commit

**Do not split** when all changes implement a single coherent unit of work.

## Workflow

1. `git status` + `git diff` — read all changes
2. `git log --oneline -5` — match existing commit style
3. Group changes into logical units (see splitting rules above)
4. For each group:
   - Stage the relevant files with specific paths (not `git add -A`)
   - Commit using a HEREDOC to preserve formatting
5. Run `git status` after all commits to confirm clean state

## Safety rules

- Never `--amend` a previous commit; always create new ones
- Never `--no-verify`
- Never `git add -A` — stage files explicitly by path
- Never push unless the user asks

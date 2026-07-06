---
name: audit-memories-to-skills
description: Audit Claude Code memories and promote the reusable how-to ones into skills (new or merged), retiring the duplicates and fixing the indexes. Use when the user asks to review, clean up, consolidate, or "turn memories into skills" across global and per-project memory stores.
---

# Auditing memories → promoting them to skills

Memories accumulate the same facts across many project scopes. Procedural knowledge
("how to do X") belongs in a **skill**, where it is discoverable and reusable; memories should
hold **state and context** (who the user is, what a ticket needs, project constraints). This skill
turns that clean-up into a repeatable, safe process.

**Default to a report first.** Enumerate, classify, and present a table for approval **before**
touching any file, unless the user has explicitly said to just do it. Creating/merging/retiring is
destructive and cross-cutting — get sign-off on the classification first.

## 1. Enumerate every memory

Memories live in two places. Miss neither:

```bash
# Global
ls ~/.claude/memory/*.md 2>/dev/null
# Per-project (dir name = slugified cwd path)
ls ~/.claude/projects/*/memory/*.md 2>/dev/null
```

Each project dir also has a `MEMORY.md` index (one `- [Title](file.md) — hook` line per memory).
The same fact often appears in 5–10 project scopes — that redundancy is the main thing you are
consolidating.

## 2. Enumerate every skill — **follow symlinks**

```bash
find -L ~/.claude/skills -name SKILL.md        # -L is mandatory: many skills are symlinks
find -L ~/.claude/skills -maxdepth 1 -type l   # see which are symlinked, and to where
```

A plain `find` (no `-L`) silently misses every symlinked skill. **This is the single most costly
mistake:** if you miss an existing skill you will propose a duplicate (e.g. a `tdd` skill already
exists via symlink). Always cross-check candidates against the full `-L` list before proposing NEW.

Also scan for skills you should not overwrite in place — see step 4.

## 3. Classify each memory

For every memory decide:

- **STAYS A MEMORY** — it is state/context, not procedure: user identity, a ticket's current
  status, a project constraint, a credential location, a decision still pending. Keep it.
- **SKILL CANDIDATE** — it is reusable procedure or a durable gotcha. Then either:
  - **MERGE** into a named existing skill — say exactly *what* to add and *where* (which section).
  - **NEW SKILL** — sketch the `name`/`description` frontmatter and a section outline.

Output a table: `memory file | scope | current type | verdict | rationale`. Group duplicates:
"this appears in 8 scopes; promote once, retire the other 7."

## 4. Where skill edits are allowed to land

Not every skill is safe to edit in place:

- **Symlinked / user-authored skills** → edit the **source repo**, not the installed copy. See the
  `edit-installed-skill` skill for the two source repos and the symlink check.
- **Third-party / marketplace skills** (e.g. `atlassian-jira-confluence`, `acli-skill`, the
  mattpocock skills) → **do not edit**; they are overwritten on reinstall. If a gotcha only fits a
  third-party skill, keep **one canonical memory** for it instead of promoting it.

## 5. Execute (only after approval)

1. **Create / merge skills first**, so nothing is lost before you delete.
2. **Retire the promoted memories.** `rm` is commonly aliased to `rm -i`; in a non-interactive
   shell every prompt auto-declines and **nothing is deleted** (a silent no-op). Always use:
   ```bash
   /bin/rm -f -- <files>
   ```
   Then confirm with a per-directory remaining-file count — do not trust exit code alone.
3. **Rewrite every affected `MEMORY.md` index.** Remove the retired lines. If a whole dir is now
   empty, leave a one-line placeholder noting where the content went
   (`_No active project memories. The X rule moved to the Y skill._`).
4. **Fix dangling `[[wikilinks]]`** in kept memories that pointed at retired ones — repoint them to
   the skill ("see the `create-jira-issue` skill") rather than leaving a dead link.

## 6. Verify

- No memory `.md` file is missing from its dir's `MEMORY.md`, and no index line points at a
  deleted file.
- Every proposed NEW skill still doesn't collide with an existing one (re-run the `-L` find).
- Report back: skills created, merges applied, memories retired (with count + scopes), indexes
  rewritten, and **any deliberate deviations** from the approved plan (e.g. "did not create a `tdd`
  skill — one already exists; kept the memory as a project mandate instead").

## Guiding split

| Belongs in a **skill** | Stays a **memory** |
|---|---|
| How to build/authenticate a client | Where the credentials file lives |
| The steps of a workflow | The current status of a specific ticket |
| A durable API gotcha + its fix | A pending decision the user still owns |
| Naming/formatting conventions | Who the user is and their preferences |

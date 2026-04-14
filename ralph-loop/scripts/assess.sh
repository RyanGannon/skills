#!/bin/bash
# Ralph Loop Assessment Script
# Run from the project root. Outputs a quick structural check.
# The agent reads and interprets the results — this script just gathers facts.

set -eo pipefail

echo "=== Ralph Loop Assessment ==="
echo ""

# Pillar 1: Specifications (GitHub issues)
echo "--- Pillar 1: Specifications ---"
if command -v gh &>/dev/null && git remote get-url origin &>/dev/null 2>&1; then
  issue_count=$(gh issue list --state open --limit 100 --json number --jq 'length' 2>/dev/null || echo "0")
  echo "Open GitHub issues: $issue_count"
  gh issue list --state open --limit 20 --json number,title,labels --jq '.[] | "#\(.number) [\(.labels | map(.name) | join(", "))] \(.title)"' 2>/dev/null || echo "(could not fetch issues)"
else
  echo "gh CLI not available or no git remote — cannot check GitHub issues"
  if [ -d "specs" ]; then
    echo "specs/ directory found:"
    ls specs/ 2>/dev/null
  else
    echo "No specs/ directory found"
  fi
fi
echo ""

# Pillar 2: CLAUDE.md / AGENTS.md
echo "--- Pillar 2: CLAUDE.md / AGENTS.md ---"
if [ -f "CLAUDE.md" ]; then
  echo "CLAUDE.md: FOUND"
  echo "Size: $(wc -l < CLAUDE.md) lines"
  grep -c "Signs\|sign" CLAUDE.md 2>/dev/null && echo "Signs section: present" || echo "Signs section: NOT FOUND"
elif [ -f "AGENTS.md" ]; then
  echo "AGENTS.md: FOUND (consider renaming to CLAUDE.md)"
  echo "Size: $(wc -l < AGENTS.md) lines"
else
  echo "CLAUDE.md: NOT FOUND"
  echo "AGENTS.md: NOT FOUND"
fi
echo ""

# Pillar 3: ralph/ scripts
echo "--- Pillar 3: ralph/ scripts ---"
for f in ralph/afk.sh ralph/once.sh ralph/prompt.md; do
  if [ -f "$f" ]; then
    echo "$f: FOUND"
  else
    echo "$f: NOT FOUND"
  fi
done
if [ -f "ralph/prompt.md" ]; then
  grep -q "NO MORE TASKS" ralph/prompt.md && echo "Termination instruction: present" || echo "Termination instruction: MISSING"
  grep -q "ONLY WORK ON A SINGLE TASK" ralph/prompt.md && echo "Single-task rule: present" || echo "Single-task rule: MISSING"
  grep -q "FEEDBACK LOOPS" ralph/prompt.md && echo "Feedback loops section: present" || echo "Feedback loops section: MISSING"
fi
if [ -f "ralph/afk.sh" ]; then
  grep -q "git log" ralph/afk.sh && echo "Commit injection: present" || echo "Commit injection: MISSING"
  grep -q "sbx run" ralph/afk.sh && echo "Docker sandbox (sbx): present" || echo "Docker sandbox (sbx): NOT FOUND (check loop command)"
fi
echo ""

# Pillar 4: Backpressure
echo "--- Pillar 4: Backpressure ---"
# Tests
found_tests=false
for f in pytest.ini pyproject.toml vitest.config.js vitest.config.ts jest.config.js jest.config.ts go.sum package.json; do
  [ -f "$f" ] && found_tests=true && echo "Test config found: $f"
done
$found_tests || echo "No test configuration files detected"

# Linters
found_linters=false
for f in .eslintrc .eslintrc.js .eslintrc.json .eslintrc.yml ruff.toml .ruff.toml .golangci.yml .rubocop.yml; do
  [ -f "$f" ] && found_linters=true && echo "Linter config found: $f"
done
$found_linters || echo "No linter configuration files detected"

# Type checkers
found_tc=false
for f in tsconfig.json mypy.ini pyrightconfig.json .mypy.ini; do
  [ -f "$f" ] && found_tc=true && echo "Type checker config found: $f"
done
$found_tc || echo "No type checker configuration files detected"

# Pre-commit
[ -f ".pre-commit-config.yaml" ] && echo "Pre-commit hooks: FOUND" || echo "Pre-commit hooks: NOT FOUND"
echo ""

# Pillar 5: Implementation Plan
echo "--- Pillar 5: Implementation Plan ---"
if [ -f "IMPLEMENTATION_PLAN.md" ]; then
  echo "IMPLEMENTATION_PLAN.md: FOUND"
  echo "Size: $(wc -l < IMPLEMENTATION_PLAN.md) lines"
  incomplete=$(grep -c '^\- \[ \]' IMPLEMENTATION_PLAN.md 2>/dev/null || echo "0")
  complete=$(grep -c '^\- \[x\]' IMPLEMENTATION_PLAN.md 2>/dev/null || echo "0")
  echo "Incomplete tasks: $incomplete"
  echo "Completed tasks: $complete"
  grep -q '#[0-9]' IMPLEMENTATION_PLAN.md && echo "Issue references: present" || echo "Issue references: MISSING"
else
  echo "IMPLEMENTATION_PLAN.md: NOT FOUND"
fi
echo ""
echo "=== Assessment complete. Claude will interpret results and score each pillar. ==="

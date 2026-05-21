---
name: acli-jira
description: Manage Jira work items using the official Atlassian CLI (acli): create, bulk-create, edit, transition, view, search, assign, comment, and handle custom fields. Use when the user wants to create Jira issues/stories/tasks/bugs, edit or transition Jira tickets, run JQL queries, bulk-update work items, or use acli to automate Jira workflows. Also triggers on: "jira cli", "acli workitem", "transition to done", "create jira issue from CLI".
---

# acli-jira

## Quick start

```bash
# Auth (one-time)
echo $JIRA_API_TOKEN | acli jira auth login \
  --site "mysite.atlassian.net" --email "me@example.com" --token
# or browser OAuth:
acli jira auth login --web

# Create
acli jira workitem create -s "Fix login bug" -p TEAM -t Bug -a @me -l auth,p1

# Edit
acli jira workitem edit -k TEAM-123 -s "Updated title"

# Transition
acli jira workitem transition -k TEAM-123 -s "In Progress" -y

# Search
acli jira workitem search --jql "project = TEAM AND status = Open" --json
```

## Workflows

### Create with custom fields
```bash
acli jira workitem create --generate-json > item.json
# fill in additionalAttributes, then:
acli jira workitem create --from-json item.json
```

**`additionalAttributes` value shapes:**
```json
{
  "projectKey": "PROJ", "type": "Task", "summary": "Title",
  "additionalAttributes": {
    "customfield_10319": [{ "value": "Common" }],
    "customfield_10122": 1234,
    "customfield_10200": { "accountId": "abc123" },
    "customfield_10300": { "value": "Parent", "child": { "value": "Child" } }
  }
}
```
> Discover the right shape: `GET /rest/api/3/issue/{key}` on a populated item and mirror it.

### Bulk operations (edit / transition by JQL)
```bash
acli jira workitem edit \
  --jql "project = TEAM AND labels = stale" --remove-labels stale -y
acli jira workitem transition \
  --jql "project = TEAM AND fixVersion = 2.0" -s Done -y
```

### Bulk create
```bash
# CSV columns: summary, projectKey, issueType, description, label, parentIssueId, assignee
acli jira workitem create-bulk --from-csv issues.csv
acli jira workitem create-bulk --from-json issues.json  # array of create-JSON objects
```

## Gotchas

| Situation | Fix |
|---|---|
| Custom field silently dropped on create | Field must be on the project's **Create screen** for that issue type |
| `edit --from-json` fails for custom fields | Known bug — use `PUT /rest/api/3/issue/{key}` instead |
| Sprint field won't set via acli | Use `POST /rest/agile/1.0/sprint/{id}/issue` |
| Need available transitions for a ticket | `GET /rest/api/3/issue/{key}/transitions` (not exposed by acli) |

See [REFERENCE.md](REFERENCE.md) for full flag tables and all subcommands.

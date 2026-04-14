# acli-jira Reference

## All `acli jira workitem` subcommands

`archive`, `assign`, `attachment-delete`, `attachment-list`, `clone`,
`comment-create`, `comment-delete`, `comment-list`, `comment-update`,
`comment-visibility`, `create`, `create-bulk`, `delete`, `edit`, `link`,
`search`, `transition`, `unarchive`, `view`, `watcher-remove`

---

## `create` flags

| Flag | Short | Description |
|---|---|---|
| `--summary` | `-s` | Work item title |
| `--project` | `-p` | Project key |
| `--type` | `-t` | Issue type (Epic, Story, Task, Bug, …) |
| `--description` | `-d` | Plain text or ADF |
| `--description-file` | | Read description from file |
| `--assignee` | `-a` | email / accountId / `@me` / `default` |
| `--label` | `-l` | Comma-separated labels |
| `--parent` | | Parent work item key |
| `--editor` | `-e` | Open `$EDITOR` for summary + description |
| `--from-file` | `-f` | Read summary+description from file |
| `--from-json` | | Full payload from JSON file |
| `--generate-json` | | Print a JSON template |
| `--json` | | JSON output |

---

## `edit` flags

**Selection (pick one):** `--key/-k`, `--jql`, `--filter`

| Flag | Short | Description |
|---|---|---|
| `--summary` | `-s` | |
| `--description` | `-d` | Plain text or ADF |
| `--description-file` | | |
| `--assignee` | `-a` | |
| `--remove-assignee` | | |
| `--labels` | `-l` | |
| `--remove-labels` | | |
| `--type` | `-t` | |
| `--from-json` | | Edit via JSON file |
| `--generate-json` | | Print edit template |
| `--yes` | `-y` | Skip confirmation |
| `--ignore-errors` | | Continue on errors |
| `--json` | | JSON output |

---

## `transition` flags

| Flag | Short | Description |
|---|---|---|
| `--key` | `-k` | Comma-separated keys |
| `--jql` | | |
| `--filter` | | Filter ID |
| `--status` | `-s` | Target status name |
| `--yes` | `-y` | Skip confirmation |
| `--ignore-errors` | | |
| `--json` | | |

---

## `view` flags

| Flag | Short | Description |
|---|---|---|
| `--fields` | `-f` | Comma-separated fields. Wildcards: `*all`, `*navigable`. Prefix `-` to exclude. Default: `key,issuetype,summary,status,assignee,description` |
| `--json` | | JSON output |
| `--web` | `-w` | Open in browser |

---

## `search` flags

| Flag | Description |
|---|---|
| `--jql` | JQL query |
| `--filter` | Filter ID |
| `--fields` | Default: `issuetype,key,assignee,priority,status,summary` |
| `--count` | Return total count |
| `--limit N` | Cap results |
| `--paginate` | Fetch all pages |
| `--csv` | CSV output |
| `--json` | JSON output |
| `--web` | Open in browser |

---

## `create-bulk` flags

| Flag | Description |
|---|---|
| `--from-csv` | CSV with columns: `summary, projectKey, issueType, description, label, parentIssueId, assignee` |
| `--from-json` | JSON array of create-payload objects |
| `--generate-json` | Print template |
| `--ignore-errors` | Continue past failures |
| `--yes` | Skip confirmation |

---

## Custom field JSON shapes

Determined by field type. Discover via `GET /rest/api/3/issue/{key}`.

| Field type | Shape |
|---|---|
| Multi-select / label array | `[{"value": "Opt1"}, {"value": "Opt2"}]` |
| Single select / radio | `{"value": "Option"}` |
| Number | `1234` |
| Text / string | `"free text"` |
| User picker | `{"accountId": "abc123"}` |
| Cascading select | `{"value": "Parent", "child": {"value": "Child"}}` |
| Date | `"2026-04-14"` |
| DateTime | `"2026-04-14T10:00:00.000+0000"` |

---

## REST fallbacks (for acli gaps)

```bash
# Edit custom fields
curl -X PUT "https://mysite.atlassian.net/rest/api/3/issue/TEAM-123" \
  -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"customfield_10319": [{"value": "Common"}]}}'

# Move issue to sprint
curl -X POST "https://mysite.atlassian.net/rest/agile/1.0/sprint/42/issue" \
  -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"issues": ["TEAM-123"]}'

# List available transitions
curl "https://mysite.atlassian.net/rest/api/3/issue/TEAM-123/transitions" \
  -H "Authorization: Bearer $JIRA_API_TOKEN"
```

# ClickUp Conventions (shared)

Single source of truth for ClickUp rules used by `/create-cu-card`, `/comment-on-cu`, `/nr-alert-triage`, `/git-cb`, `/slack-msg`, and `/standup`. If a skill contradicts this file, this file wins.

## Access: the bundled CLI

The ClickUp MCP server was removed. The team standard is the CLI bundled with the repo's `clickup` skill. Never call `mcp__clickup__*` tools, they do not exist.

Run every command from the repository root:

```bash
node .agents/skills/clickup/query.mjs <command> [options] [--json]
```

If that path does not exist in the current repository, stop and say so. These skills target HouseNumbers repos that ship the `clickup` skill.

### Check auth before the first call in a session

```bash
node .agents/skills/clickup/query.mjs auth-status --json
```

It answers `{"configured":true}` or `{"configured":false}` and never exposes the token.

The token is expected in the environment as `CLICKUP_API_TOKEN`, exported from `~/.zshrc`. The CLI loads its own `.env` file without overriding variables already present in the environment (`api/client.mjs`: `if (!process.env[key]) process.env[key] = value`), so the shell always wins and no secret needs to live inside the repo.

On `{"configured":false}`, the usual cause is a name mismatch rather than a missing token: the shell exports `CLICKUP_API_KEY` for direct API calls, while the CLI reads `CLICKUP_API_TOKEN`. Tell the user to alias it in `~/.zshrc` instead of renaming, so direct `curl` calls keep working:

```bash
export CLICKUP_API_TOKEN="$CLICKUP_API_KEY"
```

Never ask for the token in the conversation and never print it. `CLICKUP_TEAM_ID` is already exported; `CLICKUP_USER_ID` is auto-detected on first use and cached into the skill's gitignored `.env`, which holds the id only and never the token when the token comes from the shell.

### Commands these skills need

| Intent | Command |
|---|---|
| Read a card | `get <url\|id>`, add `--subtasks` for children |
| Read comments | `comments <url\|id>` |
| Post a comment | `comment <url\|id> "markdown body"` |
| List the valid statuses of a card | `status <url\|id>` with no status argument |
| Move a card | `status <url\|id> "in progress"` (case insensitive, partial match) |
| Create a card | `create <list_id> "title" --description "markdown"` |
| Create a subtask | `subtask <parent_id> "title"`, then `description <new_id> "markdown"` |
| Tag and prioritize | `tag <id> "name"`, `priority <id> <urgent\|high\|normal\|low\|none>` |
| Cards in a list | `tasks <list_id>`, add `--me` for mine |
| Cards assigned to me | `my-tasks` |
| My own identity | `me` |

`--json` prints the raw ClickUp payload for any of them. Use it whenever you need to filter or compare programmatically instead of parsing the human-readable output.

### Gaps to work around

- **No server-side filtering by status or date.** `tasks` filters by assignee only. Fetch with `--json` and filter locally on `status.status` and `date_updated` (epoch milliseconds).
- **Closed-type statuses are not returned** by `tasks` and `my-tasks`; the CLI never passes `include_closed`. A card missing from those listings may be closed rather than absent.
- **`subtask` takes a title only** and inherits the parent's list, so a separate destination list is not selectable. Set description, tag, and priority in follow-up calls.
- **`create` also accepts `--description`/`--desc`, `--assignee`/`-a` and `--due`/`-d`**, even though the `clickup` skill's command table omits them.
- **Writes are not idempotent.** After an ambiguous failure or timeout, read the card before retrying, so you do not post a duplicate comment or create a duplicate card.

## Card ID from branch name

Branch names embed the card ID after the type prefix: `feat/868fwym2r-scraping-error-improvements` → card ID `868fwym2r`.

## Rendering rules — per surface

ClickUp renders markdown differently depending on the surface. Apply the rules for the surface you are writing to:

**Task descriptions** (creating/editing a card):
- `###` (H3) for section titles, `####` (H4) for nested sub-titles; never H1/H2.
- `-` for bullets; **bold** sparingly for inline labels.
- NEVER inline code spans (backticks) — the description renderer breaks each span onto its own line, shattering sentences. Write identifiers as plain text or bold.
- Blank lines ONLY before a new section title — every blank line renders as a large paragraph gap.

**Comments** (`comment_text` API):
- `**bold**` is NOT rendered — it shows up literally. Never use it. Visual hierarchy comes from emoji prefixes + Title Case section titles.
- Inline code spans (`` `name` ``) and short code fences DO render and are allowed when a 2–3 line snippet adds real signal.

## Language

- Card descriptions: English, third person.
- Comments: English, first person.

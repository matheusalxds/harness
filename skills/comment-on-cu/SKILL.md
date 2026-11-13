---
name: comment-on-cu
description: Posts a progress comment on the ClickUp card matching the current branch's PR (Full Format for the first comment, delta-only Update Format afterwards) and moves the card to "In Review". Use when the user asks to comment on the ClickUp card, update the card, or post PR progress to ClickUp.
disable-model-invocation: true
---

# Comment on ClickUp Card

Shared conventions (card-ID-from-branch, per-surface rendering rules, language): read `~/.claude/shared/clickup-conventions.md` first and follow it.

- Find the ClickUp card via the card ID embedded in the branch name.
- Check if there's already a comment on the card.
- If there's no comment, generate a concise summary of what has been done so far and post it as a new comment using the **Full Format** below.
- If there's an existing comment, review it and add a new one using the **Update Format** — only with updates or new information since the last comment. Do NOT repeat Project / Key Changes / Technical Improvements from prior comments.
- Avoid repeating any existing content.
- Mention which projects the comment refers to. The "project" is the name of a folder under `apps/*` (NOT the repository name like `zora-pantheon`). Inspect the PR diff to find every `apps/<name>/...` path that received changes and list each unique `<name>` after the 📦 emoji, comma-separated, in alphabetical order. Skip changes confined to `packages/`, `workers/`, root config, or other non-app paths — those don't count as projects for this header. If no app under `apps/*` was touched, fall back to the most relevant `packages/<name>` or `workers/<name>`. Section titles use Title Case without brackets and without trailing colons (e.g. `Key Changes`, `Technical Improvements`).
- Formatting follows the **comments** surface rules in the shared conventions file: no `**bold**` (renders literally — hierarchy via emoji + Title Case), code spans allowed, short code fences only when a 2–3 line snippet adds real signal.
- Change the card status to "In Review".
- Write in English, in first person.
- Keep the text clear, simple, and under **175 words**.

---

## Full Format (no prior comment exists)

📦 [app-name-1, app-name-2, ...] (one or more apps from `apps/*` that received changes; e.g. `loan-application-service, web-app`)

⚙️ Key Changes
• Briefly describe what was added, changed, or fixed in plain language.
• Keep sentences short and clear (1–5 bullets).

💻 Technical Improvements
• Open with one line listing surfaces touched — packages/services/apps that received changes. Example: `Surfaces: shared-domains, loan-application-service, web-app`.
• Then 1–4 bullets describing ONLY what was technically implemented, in dev language: concrete modules/files/services, schemas/types/enums added, endpoints/routes/handlers introduced, data shapes, validation rules, message channels, jobs, queries, tests added.
• Be concrete enough that another dev reading the bullet can understand what was built and where, without opening the PR.
• Avoid soft phrasing ("improved", "enhanced", "made consistent") — name the actual change ("added `X` schema in Y", "exposed `Z` endpoint", "subscribed handler to `W` channel").
• Skip business-flow restating already covered in Key Changes — this section is the technical breakdown.

🚧 Out of Scope (include only when the card explicitly defers something OR the PR consciously skipped a related concern)
• 1–3 bullets stating what was deliberately not done and why ("deferred per card", "follow-up ticket", "needs migration plan").
• Documents the conscious decision so reviewers/PMs don't re-litigate it later.

🔐 New Env Vars (include only when new environment variables were added)
• List each new environment variable name and a brief description of its purpose.
• Example: `MESSAGE_BUS_NOTIFICATION_CHANNEL_NAME` — Channel for job completion events.

PR: [PR Link]

---

## Update Format (a prior comment from me already exists)

When there's a previous comment, post **only the delta**. Do not restate Project, Key Changes, or Technical Improvements that haven't changed.

🔁 Update Since Last Comment
• 1–4 bullets covering ONLY new commits/changes/decisions since the last comment.
• Use the same dev-language tone as Technical Improvements — be concrete.
• Examples: "Addressed Gemini review feedback (4 inline comments)", "Reordered `SIDEBAR_EDITABLE_FIELDS` to match sidebar render order", "Added boundary tests for `MAX_VESTING_ENTITY_NAME_LENGTH`".

🚧 Out of Scope (only if newly identified or changed)

🔐 New Env Vars (only if newly added)

PR: [PR Link]

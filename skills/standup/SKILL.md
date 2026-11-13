---
name: standup
description: Generate a standup update by pulling activity from GitHub and ClickUp (HouseNumbers only) for pasting into Slack. Use when the user asks for a standup update, daily update, or says "write my standup". Smart window — 72h on Mondays (covers Friday), 24h on other days. Produces a simple, direct first-person update with each bullet tagged by the plain ClickUp URL (or "- no ticket" when none exists). "Done:" / "Doing:" format with short bullet points.
---

# Standup Generator

Produces a standup update by gathering recent activity across GitHub and ClickUp, scoped exclusively to HouseNumbers work.

## Identity

- **GitHub handle**: matheusalxds
- **GitHub org**: HouseNumbers (only this org — ignore all other repos/orgs)
- **ClickUp user ID**: 87340345
- **ClickUp list ID**: 901103697260

## Step 0 — Ask for yesterday's standup (MANDATORY)

**Before doing anything else**, ask the user to paste yesterday's standup so today's update doesn't duplicate items that were already reported.

Prompt the user with something like:

> Você pode colar o standup de ontem? Vou usar como referência pra não duplicar itens que já foram reportados.
>
> Se não tiver, é só responder "não tem" que eu sigo gerando sem essa referência.

**Wait for the user's response before proceeding.** Three possible outcomes:
- **User pastes yesterday's standup** → parse it; record every "Done" item and every "Doing" item. Use this when filtering today's results in Step 4 / Step 5.
- **User says they don't have it / skip / não tem / etc.** → proceed without the reference; note in the final output that no dedup against yesterday was performed.
- **User pastes something that isn't a standup** → ask for clarification once; if unclear, proceed without it.

This step is **non-negotiable** — duplicating yesterday's items in today's standup is the most common failure mode of this skill, and the user pays the cost reading it. The 5-second prompt is cheaper than the regenerate cycle.

## Step 1 — Compute the time window

The window is **day-of-week aware** to account for weekends:
- **Monday**: 72 hours back (covers Friday)
- **Tuesday–Friday**: 24 hours back (covers yesterday)

Run this to get the cutoff:

```bash
DOW=$(date +%u)
if [ "$DOW" = "1" ]; then HOURS=72; else HOURS=24; fi
# ISO date for GitHub
date -v-${HOURS}H '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -d "${HOURS} hours ago" '+%Y-%m-%dT%H:%M:%SZ'
# YYYY-MM-DD for ClickUp
date -v-${HOURS}H '+%Y-%m-%d' 2>/dev/null || date -d "${HOURS} hours ago" '+%Y-%m-%d'
```

Save both values — you'll use them in Steps 2 and 3.

## IMPORTANT: Both sources are mandatory

Steps 2 (GitHub) and 3 (ClickUp) **must both be executed** before writing the standup. Never skip or defer either — each source may contain activity not reflected in the other.

## Step 2 — Gather GitHub activity (HouseNumbers only)

```bash
gh search prs --author matheusalxds --owner HouseNumbers --sort updated --limit 20 --json title,state,createdAt,updatedAt,repository,number
```

**Scope rules:**
- Only repos under the `HouseNumbers` org — the search is org-wide so work in any HouseNumbers repo appears; no other orgs
- Only PRs **authored** by Matheus — exclude reviews, approvals, or comments on others' PRs
- Only include PRs with `createdAt` or `updatedAt` within the computed window
- Focus on what problem each PR solves, not the PR number

## Step 3 — Gather ClickUp activity (HouseNumbers only)

ClickUp access (CLI invocation, auth check, known gaps): read `~/.claude/shared/clickup-conventions.md` first and follow it.

The CLI filters by assignee only, so the status and date filtering happens locally. Run from the repository root, reusing `$HOURS` from Step 1:

```bash
node .agents/skills/clickup/query.mjs tasks 901103697260 --me --json | python3 -c "
import json, sys, time
cutoff = (time.time() - $HOURS * 3600) * 1000
for t in json.load(sys.stdin):
    if int(t.get('date_updated') or 0) >= cutoff:
        print(t['status']['status'], t['id'], t['name'], t['url'], sep=' | ')
"
```

Split the result by the printed status: in-progress and in-review cards feed "Doing" and "Done" per the criteria below.

**Scope rules:**
- Only list `901103697260` — no other lists, spaces, or workspaces
- The `--me` flag resolves to the cached ClickUp user ID, which must be `87340345`; run `me` once if the cache is empty
- The date filter above already drops old backlog items; do not re-add them from another source
- Cards in a **closed-type** status are not returned by this command (the CLI never passes `include_closed`). A card that vanished from the listing but appears in the GitHub activity as merged is very likely closed, so treat it as Done rather than as missing
- For richer context on a specific card, run `node .agents/skills/clickup/query.mjs get <card-id>`

## Step 4 — Correlate and deduplicate

Group raw activity from GitHub and ClickUp into **work items** — one item per piece of actual work, regardless of how many sources mention it.

**Dedup signals:**
- PR branch name contains ClickUp task ID (e.g., `fix/868j4gpwz-...` → task `868j4gpwz`)
- Same technical term or feature name across sources
- Same bug/feature description

For each work item, merge all signals and use the richest source for the description. A GitHub PR + a ClickUp task about the same fix = **one bullet**, not two.

## Step 5 — Write the standup

### Format
```
Done
• <what I finished — short, direct, first person> — <ticket-url>
• ...

Doing
• <what I'm working on or picking up next — short, direct> — <ticket-url>
• ...
```

**Section headers have no trailing colon** — write `Done` and `Doing` as bare words, never `Done:` or `Doing:`. The bullet list itself signals the section break; the colon adds visual noise on Slack without conveying meaning.

**Ticket tag at the end of each bullet** — every bullet ends with ` — ` (space, em dash `—`, space — NOT a hyphen `-`) followed by the plain ClickUp URL, e.g. ` — https://app.clickup.com/t/868jey840`. The em dash is visibly longer than a hyphen and reads cleaner as a section separator. This tag is a deliberate exception to the global no-em-dash rule: it applies only here, and the bullet text itself uses no em dashes. Slack auto-links the URL on paste. Build the URL by appending the task ID to `https://app.clickup.com/t/`. If the work has no associated ClickUp ticket (ad-hoc fix, unblocking work, etc.), use the plain text ` — no ticket` instead (no link).

**No trailing period before the tag** — the sentence preceding the ticket tag must NOT end with a period (or any other terminal punctuation). Writing `... awaiting review. — https://app.clickup.com/t/868ju8r1j` looks awkward because of the dangling period before the dash. Always strip the final period so the bullet flows directly into the tag, e.g. `... awaiting review — https://app.clickup.com/t/868ju8r1j`. This applies to every bullet, including the ` — no ticket` form.

The tag goes at the very end of the bullet. Do not use parentheses, do not use markdown `[id](url)` syntax, do not use the Slack mrkdwn `<url|id>` form — always output the plain URL.

### "Done" criteria
Items where **the coding work is finished** within the window. This includes:
- Merged PRs
- Tasks moved to done/closed
- **PRs in review** (open, awaiting merge) — once a PR is up there's no more code to write from the dev's side, so it counts as Done. The same applies to ClickUp tasks moved to "in review".
- PRs where review feedback was addressed and pushed back — that round of work is done.

**Phrasing for review-state items** — never use the bare phrase "in review" at the end of a bullet (it reads like a status field, not a sentence). Instead, weave it in naturally with one of:
- "the PR is up for review"
- "the PR is awaiting review"
- "shipped the PR, now in reviewers' hands"
- "handed off to reviewers"
- "out for review"

Pick whichever flows best with the rest of the sentence — vary it across bullets so the standup doesn't feel templated.

**Punctuation consistency**: when appending the review-state clause to a bullet, separate it with `;` (semicolon) in every bullet of the standup, e.g. `...; back with reviewers — <ticket-url>`.

### "Doing" criteria
Items where **code is still being actively written**. Keep it minimal — just state what's in progress. One line per item.

A PR sitting in review is **not** "Doing" — it's Done. Only put something in "Doing" if there's real implementation work still happening (writing code, debugging, designing, testing locally before opening the PR).

### Rules
- **First person** — write as if Matheus is speaking: "I fixed...", "I'm testing...", "I shipped..."
- **Simple and direct** — short sentences, plain language, no fluff. Write like you're telling a teammate in one line, not narrating. Avoid adjectives like "nasty", "sneaky", "a bit of". Skip meta-commentary ("to walk through every step", "to catch anything"). State the fact and move on.
- **Natural, conversational verbs** — open bullets with the phrasing a dev would actually type on Slack, not report-style verbs. For multi-day work reaching its end, prefer "Wrapped up…" or "Closed out…" over the drier "Finished…" / "Completed…" — they carry the sense of closing a cycle that earlier standups reported as in-progress. For new work landing, "Shipped…" beats "Implemented…" / "Developed…". Vary the opener across bullets so the standup doesn't feel templated. Natural ≠ slangy: never "crushed it", "banged out", "knocked out".
- **One sentence per bullet when possible** — if a bullet needs two sentences, it probably needs trimming.
- **What + why, not how** — state what was delivered and the problem it solves. DO NOT mention the mechanism (field names, schema names, library/package names, function names, configuration keys, cast types, regex patterns, file paths, commit hashes). If a non-technical teammate couldn't follow the bullet, the implementation leaked in.
  - The reader wants to know "what changed for the user/system" and "what pain this fixes" — not "how it was wired".
  - Replace `zod v3/v4 cast`, `attachments field on the MCP tool schema`, `runtime prompt field`, `Record<string, unknown>`, etc. with the user-visible effect: "the conditional approval letter is now attached correctly to the LO email".
  - If the bullet reads like a commit message, rewrite it.
- **No process narration about review rounds** — phrases like "addressed review feedback", "applied review notes", "shipped review fixes", "responded to PR comments", or "second round of review" describe your workflow, not the feature. They tell the reader nothing about what was actually delivered. Even when the day's work was literally a review-feedback round, describe the **feature itself** — what it does, who benefits, what pain it solves — and only add the review state (e.g., "back with reviewers", "out for review", "merged") as a trailing clause.
  - The reader doesn't care which round of review the PR is on. They care what the feature does.
  - If the only thing you can say is "addressed review feedback", you haven't thought about the bullet enough — open the PR description or your last commit and pull out the user-visible purpose.
- **No PR numbers, no GitHub URLs** — never mention PR numbers or GitHub URLs in the bullet body. The only link allowed is the ClickUp ticket tag defined in the Format section above (that section is the single source for the tag rules — em dash, plain URL, no trailing period).
- **Describe the actual problem or feature** — not "Worked on ticket X".
- **Don't repeat yesterday** — use the prior standup captured in Step 0 (if the user provided one) as the dedup reference.
  - Any item already reported as "Done" yesterday MUST be removed from today, even if its state changed (e.g. "in review" → "merged"). The work was already reported; merging is not a new delivery from the dev's perspective.
  - Any "Doing" item from yesterday that finished today should move into "Done" today with an outcome-focused description (not "finished what I started yesterday").
  - Any "Doing" item from yesterday that is **still in progress** today should be omitted unless there's a meaningful new sub-deliverable to report. Re-listing the same Doing line two days in a row adds no information.
- **Exclude PR reviews** — reviewing/approving someone else's PR is not standup-worthy.
- **Include support/ops work** — infra fixes, unblocking teammates, triaging bugs, etc.
- **No blockers section** — only mention blockers inline if genuinely blocked.
- **Language** — write the standup in **English**.

### Good vs bad examples

**Bad** (leaks implementation: "unix math", "deterministic code", "pre-computed string into the prompt"):
> Fixed a P4 bug where the agent was drifting on "days since last contact" — it was doing unix math itself and missing days, so I moved that calculation to deterministic code — https://app.clickup.com/t/868jey840

**Good** (outcome-focused — what was fixed and why it matters):
> Fixed a P4 bug where the agent's "days since last contact" references were off by a day or two, so follow-up timing is now accurate — https://app.clickup.com/t/868jey840

**Bad** (process narration, filler words):
> Verifying the end-to-end flow for the email draft and SMS send actions in the agent inbox, running everything manually instead of relying on the hotkeys so I can actually walk through every step and catch anything the shortcuts skip over — https://app.clickup.com/t/868jpx123

**Good** (trimmed to the fact):
> Testing the email draft and SMS send flow end-to-end before the pilot — https://app.clickup.com/t/868jpx123

**Bad** (mentions mechanism: "pre-resolved runtime prompt field", "zod v3/v4 cast", "attachments field on the tool schema"):
> Addressed review feedback on the R9 LO email PR: locked the CC-LO behavior through a pre-resolved runtime prompt field and replaced a broken zod v3/v4 cast in mcp-gateway that was silently dropping the attachments field from the tool schema — https://app.clickup.com/t/868jr9lo1

**Good** (describes the feature, not the review round):
> Shipped the R9 LO email, so the loan officer is now reliably CC'd on borrower outreach and the conditional approval letter is attached when applicable; back with reviewers — https://app.clickup.com/t/868jr9lo1

**Bad** (process narration — "addressed review feedback round" tells the reader nothing about the feature):
> Addressed the review feedback round on the R4 Needs List Review PR — the editable checklist is hardened against duplicate LO email drafts and edge-case PATCH failures, with full error-path test coverage; back with reviewers — https://app.clickup.com/t/868k3twm4

**Good** (describes what the feature does and who benefits):
> Shipped the R4 Needs List Review inbox action: processors get an editable checklist of outstanding initial-submission docs right after disclosures are signed, and on confirm the agent drafts the LO email asking for them; back with reviewers — https://app.clickup.com/t/868k3twm4

**Bad** (reads like a commit message):
> Added two new values (`alreadyPaidFor`, `orderedNotYetPaidFor`) to the `appraisalOrderIntent` enum and suppressed two alert rules — https://app.clickup.com/t/868japp01

**Good** (describes the problem solved):
> Added two new appraisal order intent options to unblock Ben's intake form mapping, and suppressed the false "missing appraisal" alerts that would have fired for them — https://app.clickup.com/t/868japp01

**Ad-hoc work with no ticket** (use ` — no ticket`):
> Unblocked Marcos by pairing on the local extractor setup so he could keep moving on his branch — no ticket

## Step 6 — Merge user-provided plans (optional)

If the user passes additional text alongside the `/standup` command (e.g., `/standup vou trabalhar no deploy do staging e reunião com o time de produto`), treat it as **future plans** to append to the "Doing" section.

**Rules for user-provided plans:**
- **Translate to English** — the user may write in Portuguese or any language; always output in English
- **Summarize** — condense verbose input into 1-2 concise bullet points
- **Append, don't replace** — add these bullets after the items discovered from GitHub/ClickUp
- **If no text is provided** — skip this step entirely, do not add anything extra

## Step 7 — Present the standup

Show the standup draft formatted and ready to copy/paste. Ask if the user wants to adjust anything before copying.

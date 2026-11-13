---
name: nr-alert-triage
description: >
  Triage New Relic production alerts — analyze error logs, check for existing ClickUp subtasks,
  create new subtask if needed, and return a brief summary with card link.
  Trigger when user pastes a New Relic alert block with "Activated on", "Duration", "Current state",
  and a production service name (e.g. "production-agent-service").
allowed-tools: Bash, Read, Grep, Glob, mcp__newrelic__execute_nrql_query
argument-hint: |
  Activatedon <date> <time>
  Duration:<duration>
  Last updated:<date> <time>
  Current state:<state>
  <production-service-name>
---

# New Relic Alert Triage

Fast triage for production alerts: analyze logs, match or create ClickUp ticket, return summary.

## Input

```
$ARGUMENTS
```

Parse the input to extract:
- **Activation date/time**
- **Duration**
- **Service name** (the line that starts with `production-`)

## Config (single source for IDs — referenced by name below)

- `NR_ACCOUNT` = `3729514` (New Relic account)
- `PARENT_BUG_CARD` = `868gg9u3v` (parent bug tracking card)
- `SUBTASK_LIST` = `901103697260` (ClickUp list for new subtasks)

## Step 1 — Query Error Logs

Run these queries **in parallel** against New Relic account `NR_ACCOUNT`:

**a) Error breakdown by message (last 3 days):**
```sql
SELECT count(*) FROM Log
WHERE `level` = 'error'
AND `metadata.service` = '<SERVICE_NAME>'
SINCE 3 days ago FACET message LIMIT 20
```

**b) Error trend (last 7 days):**
```sql
SELECT count(*) FROM Log
WHERE `level` = 'error'
AND `metadata.service` = '<SERVICE_NAME>'
SINCE 7 days ago TIMESERIES 1 day
```

**c) Error details with metadata:**
```sql
SELECT * FROM Log
WHERE `level` = 'error'
AND `metadata.service` = '<SERVICE_NAME>'
SINCE 1 day ago LIMIT 20
```

If the `*` query returns too much data, use a targeted query instead:
```sql
SELECT message, `metadata.error`, `metadata.error.message`, `metadata.error.name`,
       `metadata.loanApplicationId`, `metadata.loanId`, `metadata.loanFileId`
FROM Log
WHERE `level` = 'error'
AND `metadata.service` = '<SERVICE_NAME>'
SINCE 1 day ago LIMIT 20
```

If metadata fields come back null, extract details from the full log output using `Bash` with `python3`/`jq` to parse the saved JSON file.

## Step 2 — Identify Root Causes

From the error data, group errors into **distinct root causes**. For each root cause identify:
- Error message pattern
- Specific error detail (from `metadata.error`, `metadata.error.message`, or stack traces)
- Number of occurrences
- Affected handlers/jobs
- Affected loan IDs (list up to 5)
- **Priority assessment** (see rubric below)

If needed, run additional targeted queries per error type to get full details:
```sql
SELECT message, `metadata.error.message`, `metadata.payload.*`
FROM Log WHERE `level` = 'error'
AND `metadata.service` = '<SERVICE_NAME>'
AND message = '<SPECIFIC_ERROR_MESSAGE>'
SINCE 3 days ago LIMIT 5
```

### Priority Rubric

Assign exactly ONE priority per root cause based on **availability first, then volume, blast radius, and recoverability**:

**Hard rule — total unavailability is P0, period.** If a service, feature, or critical dependency is fully down/off at triage time (or was down and could go down again the same way), assign **P0 immediately**. No modifier (self-healing, trend, volume) can demote a total outage. Recurrence is not required — one full outage is enough.

**P0 is NOT limited to unavailability.** Severe production impact also qualifies: if the issue effectively prevents users from using the platform (core flows unusable, users blocked from working — even with services technically "up"), it is P0. Judge by user impact, not by uptime.

| Priority | Criteria |
|----------|----------|
| **P0** | Total unavailability OR severe production impact leaving users unable to use the platform: service/feature/critical dependency fully down or fully broken, core flows unusable, data loss risk, blocks core loan processing, OR sustained spike >100 errors/hour |
| **P1** | Production impact that is recurring or high volume (>100 errors in 3 days), affects multiple handlers, customer-impacting feature degraded, no automatic recovery |
| **P2** | Small/partial impact: moderate volume (10-100 errors in 3 days), single handler/feature, partial impact, OR recoverable upstream issue with no automatic recovery |
| **P3** | Low volume (<10 errors in 3 days), OR system already self-heals (e.g., SQS retries + DLQ worker), OR transient upstream noise with no customer impact |

**Factor in self-healing (P1–P3 only — never demotes a total outage).** If the failure path is already recovered automatically (SQS retries succeed on redelivery, DLQ worker picks up, etc.), drop the priority to **P3** even if error volume is high — the right fix is usually to lower the log level, not to add resilience. Check the affected service's CLAUDE.md and existing infrastructure before assuming recovery is manual.

Also factor in **trend direction** (from query b): a rising 7-day trend bumps priority up one level; a fully flat/decreasing trend with self-healing in place bumps it down one level. Trend modifiers also never demote a P0 total outage.

## Step 3 — Check Existing ClickUp Subtasks

ClickUp access (CLI invocation, auth check, known gaps): read `~/.claude/shared/clickup-conventions.md` first and follow it. All ClickUp work here runs through the bundled CLI via `Bash`.

Fetch the parent bug card with all subtasks, from the repository root:

```bash
node .agents/skills/clickup/query.mjs get <PARENT_BUG_CARD> --subtasks
```

Compare each subtask name/description against the root causes found in Step 2:
- Match by **service name**, **error type**, or **error message pattern**
- A subtask "covers" a root cause if it addresses the same service + same category of error

Classify each root cause as:
- **EXISTING** — a subtask already covers this error
- **NEW** — no subtask covers this error

## Step 4 — Ground Solutions in the Codebase (MANDATORY before suggesting fixes)

**Before writing any "Suggested solutions", acceptance criteria, recovery-posture claim, or fix recommendation in a comment or card, you MUST verify the claims against the actual code.** Do not rely on:
- What the user/teammate said is happening in the code
- What a previous card description claimed
- What seems "likely" based on error messages alone
- Memory entries that name file paths or behaviors

The cost of one wrong fix recommendation (rejected by reviewer, re-scoped card, lost trust) is much higher than the few minutes of reading code.

### What to read

For each root cause you intend to make a recommendation for:

1. **Locate the exact `logger.error(...)` call site(s)** that produce the error message you saw in NR. Grep the service repo for a distinctive substring of the message:
   ```bash
   grep -rn "Orq deployment invocation failed" apps/communication-service/src
   ```
   Record the file:line of every site that emits this log.

2. **Trace the caller chain** to understand recovery behavior. For each call site:
   - Does the function `throw` after logging? (Determines whether SQS sees the failure.)
   - If invoked from an SQS consumer, does the consumer re-throw, swallow with `Promise.allSettled`, or wrap in try/catch?
   - Is there graceful degradation (null defaults, partial results)?

3. **Verify infrastructure claims.** If you're about to claim "SQS retries handle this" or "the worker picks up DLQ":
   - Find the consumer file and check it actually re-throws.
   - Find the worker — it must exist as code in `workers/*` or `apps/*-worker`. If it doesn't, the claim is false.
   - If retry policy / DLQ config is "in IaC, not in code", say so explicitly rather than asserting specific retry counts.

4. **Check for double-logging.** If both the client/service layer and the consumer/use case log the same failure, demoting one level may be more correct than the other. Flag this explicitly in your recommendation.

### Reporting findings in the card

When you list affected handlers and propose a fix:
- Use exact `file:line` references for every `logger.error` call site you want demoted.
- State recovery posture per path with evidence (e.g. "Email enrichment re-throws — see `on-messages-ready-for-enrichment.ts:229-230`. QUO path uses `Promise.allSettled` — see `extract-loan-info.use-case.ts:97-154`.").
- If you couldn't verify a claim (e.g. "DLQ worker exists"), call it out explicitly under an **"Out of scope but worth confirming"** section instead of asserting it as fact.

### When this step is OPTIONAL

If you're ONLY adding an incident-update comment to an existing card (no new solution proposed, no acceptance criteria, no behavioral claims beyond what's already in the card), you may skip codebase grounding. But the moment you propose a fix, demote a log level, recommend retry/circuit-breaker, or restate recovery behavior — go read the code first.

## Step 5 — Take Action

### For EXISTING root causes:
Add a **comment** to the existing subtask with updated incident data. **Always include the priority assessment from Step 2**:
```
Incident Update — <TODAY'S DATE>

**Priority: <P0|P1|P2|P3>** — <one-line justification (volume + blast radius + recovery)>

Alert: <SERVICE_NAME> (activated <DATE>, duration <DURATION>)
- <ERROR_COUNT> errors in last 3 days
- 7-day trend: <e.g. 8 → 17 → 52 → 3 → 0 → 5 → 16>
- Affected loans: <LOAN_IDS>
- Error detail: <ERROR_MESSAGE>
- Recovery: <"automatic via SQS retries + DLQ worker" | "manual intervention required" | "N/A">

NR query: <QUERY_USED>
```

Post it with:

```bash
node .agents/skills/clickup/query.mjs comment <subtask-id> "<comment body>"
```

The priority line is mandatory — it's how the team prioritizes triage backlog at a glance.

### For NEW root causes:
Create a **new subtask** under `PARENT_BUG_CARD`. The subtask inherits the parent's list, so it lands in `SUBTASK_LIST` as long as the parent card lives there; verify that in the `get` output from Step 3 and use `move <id> SUBTASK_LIST` only if it does not.
- **Name**: Non-technical, impact-focused, include error count. Example: `Agent service loan analysis failing — Gemini quota exceeded (142 errors in 3 days)`
- **Tags**: map from Step 2 priority — P0 → `p0-bug`, P1 → `p1-bug`, P2 → `p2-bug`, P3 → `p3-bug` (no tag if no p3-bug tag exists in the space)
- **Priority** (ClickUp field): P0 → `urgent`, P1 → `high`, P2 → `normal`, P3 → `low`
- **Description** in markdown with:
  - **Priority assessment** at the top (matches the tag/priority above, with justification)
  - Problem summary
  - Root cause details (error messages, stack traces, affected handlers)
  - Affected loans (list IDs)
  - Error trend table (last 7 days)
  - Recovery posture (automatic vs manual) — this determines whether the fix is "add resilience" vs "lower log level". **Must be grounded in code per Step 4.**
  - Suggested solutions (immediate / short-term / long-term) — **each solution must reference a concrete `file:line` from the codebase grounding in Step 4**
  - Acceptance criteria — must list the exact files/lines that need to change
  - Out of scope but worth confirming — claims you couldn't verify in code (e.g. DLQ worker existence, retry policy in IaC)
  - New Relic query reference

The CLI creates the subtask with a title only, so the description, tag, and priority are follow-up calls against the returned id:

```bash
node .agents/skills/clickup/query.mjs subtask <PARENT_BUG_CARD> "<name>"   # prints the new id
node .agents/skills/clickup/query.mjs description <new-id> "<markdown body>"
node .agents/skills/clickup/query.mjs tag <new-id> "p1-bug"
node .agents/skills/clickup/query.mjs priority <new-id> high
```

If a call fails midway, read the card with `get <new-id>` before retrying, so the run does not create a second subtask for the same root cause.

## Step 6 — Return Summary

Output a short text block the user can share (e.g. on Slack). Format:

```
**<Service display name> — <brief problem description>** (Priority: <P0|P1|P2|P3>)

<2-3 sentences explaining what happened, the root cause, and the impact. Include whether recovery is automatic or manual.>

**Related ticket(s):**
- <clickup-url-1>
- <clickup-url-2> (if multiple)

URGENT! NOTIFY THE ENG TEAM!
```

### Urgent escalation line

Append the line `URGENT! NOTIFY THE ENG TEAM!` after **Related ticket(s)** ONLY when the incident is critical — something is genuinely broken and needs a human NOW:

- Any root cause assessed **P0 or P1** (e.g. a feature fully down like the OpenAI quota exhaustion breaking all embeddings), OR
- Core infrastructure failing with no automatic recovery — SQS/SNS/message bus not delivering, AWS service outage, database unreachable, DLQ filling with no worker draining it

Do NOT add the line for P2/P3, self-healing blips, or log-noise incidents — it must stay meaningful when it appears.

Rules:
- Write the summary in **English**
- Keep it concise — max 5 sentences
- Always include the **priority** in the headline (matches Step 2 assessment)
- Include ALL relevant ClickUp links (both existing and newly created)
- If multiple root causes, mention each briefly with its individual priority
- The urgent escalation line, when present, is always the LAST line of the summary

## Important Notes

- All IDs come from the Config block at the top — never hardcode variants
- Always write ClickUp task names and descriptions in **English**
- Do NOT ask the user intermediate questions — run the full flow autonomously and return the final summary
- If a root cause spans multiple services, focus only on the service from the alert input

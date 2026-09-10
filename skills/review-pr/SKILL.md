---
name: review-pr
description: Rigorous multi-agent code review of the current branch — security (security-sentinel), API contracts, patterns, simplicity, test hygiene (feature-test-architect), dead code, and agentic systems (agentic-reviewer, conditional) — producing a severity report and user-approved inline GitHub comments. Use when the user asks for a full PR or branch review. Accepts optional scope arguments to limit the review to the N most recent commits and the N most changed files.
argument-hint: "[num-commits] [num-files]"
---

# Senior Security-First Node.js Architect & GitHub Reviewer

Performs a rigorous code review focused on Node.js, Security, and API Consistency, followed by a collaborative GitHub commenting process.

## Hard Safety Rules (non-negotiable — apply to every step and every delegated agent)

1. **NEVER close or merge a PR.** Do not run `gh pr close`, `gh pr merge`, `gh pr edit --base`, or any command that closes, merges, retargets, or transitions a PR's state. No exceptions — if asked mid-flow, re-confirm in plain text and prefer to refuse and explain.
2. **NEVER commit or push to a PR that is not authored by the current user.**
3. **Ownership detection is mandatory.** If the caller did not pass `IS_OWN_PR`, determine it: compare `gh api user --jq .login` with `gh pr view --json author --jq .author.login`. If detection fails or is ambiguous, stop and ask the user.
4. **Teammate's PR (`IS_OWN_PR=false`)**: the ONLY allowed write actions are `gh pr review`, `gh pr comment`, and inline review comments via `gh api`. No local file edits, commits, pushes, or branch switches that abandon local state.
5. **User's own PR (`IS_OWN_PR=true`)**: findings are surfaced for approval; apply local fixes only after explicit per-item or per-batch confirmation.

Execution Protocol

0. Branch Scope Lock (MANDATORY - Before anything else)
CRITICAL RULE: You MUST ONLY review code from the CURRENT branch's commits that diverge from the base branch (usually `main`).

Optional scope arguments:
- **$0** = number of recent commits to review (e.g., `2`)
- **$1** = number of top changed files to review (e.g., `12`)

If no arguments are provided, review all commits and all changed files since the merge base. If only one argument is provided, treat it as the number of commits and review all changed files. When an argument is absent, omit the corresponding limiter from the commands below (`-n $0` in step 3, `| head -n $1` in step 4) — never run them with a literal unexpanded value.

Steps:
1. Run `git branch --show-current` to identify the current branch.
2. Run `git merge-base main HEAD` to find the common ancestor.
3. Run `git log --oneline <merge-base>..HEAD -n $0` to list ONLY the commits unique to this branch (limited to the last **$0** commits when given).
4. Get the changed files. Without `$1`: `git diff <merge-base>..HEAD --name-only`. With `$1`, take the top **$1** files sorted by change volume:
   ```bash
   git diff <merge-base>..HEAD --numstat | awk '{print $1+$2 "\t" $0}' | sort -nr | cut -f2- | head -n $1
   ```
5. When scope arguments were given, display the scoped review plan to the user before proceeding: how many commits and which files (with line counts) will be reviewed. If the branch has fewer commits or files than requested, review all of them.
6. ALL review analysis MUST be scoped exclusively to these changed files and these commits.
7. NEVER review, comment on, or flag issues in code that was NOT changed in this branch's commits — or that falls outside the argument-limited scope.
8. If a file was only partially modified, only review the changed lines and their immediate context.

This ensures the review is focused, actionable, and doesn't generate noise from pre-existing code.

Model strategy: cheap models do retrieval and mechanics; the smartest model judges. Steps 1–2 run on cheap models as factual inventory, the review agents in step 3 inherit the session model (do NOT pass a `model` override — running /review-pr from a Fable/Opus session gives the reviewers that model), and the comment posting in step 6 is delegated to a Haiku subagent. The review agents must read the raw diff themselves — never judge from a summary alone.

1. Context Discovery (Haiku Agent — `model: "haiku"`)
Action: Scan the repository to identify existing "Tools" and architectural patterns.

Goal: Determine established conventions (Export styles, Error handling, Zod schemas). Inventory only — collect facts (files, patterns, conventions), do not interpret or filter what "matters".

2. Change Summarization (Haiku Agent — `model: "haiku"`)
Action: Summarize the branch's changes (scoped to commits from step 0), focusing on new endpoints, DB queries, and LLM integrations.

3. Parallel Specialized Reviews (Specialized Sub-Agents)

All agents MUST only analyze code within the branch scope defined in step 0.

Agent 1: Security — delegated to `security-sentinel`

Do NOT implement security review logic inline here. The `security-sentinel` agent (defined in `~/.claude/agents/security-sentinel.md`) is the **single source of truth** for security review rules — tenant scoping/ownership (BOLA/IDOR), webhook signature/raw-body/idempotency, the mandatory secrets/PII diff pass, injection surfaces (NoSQL, prompt/LLM, command/path, SSRF, XSS), the data-flow trace (input → validation → auth → authorization → sink), lockfile-anchored dependency severity, the false-positive rulebook, and the mandatory verify pass before any CRITICAL/HIGH. Duplicating those rules here creates drift.

Invoke it via the `Agent` tool with `subagent_type: "security-sentinel"` and a prompt that:

Note: this agent is pinned to `model: opus` in its frontmatter (not session-inherited) — Fable's elevated cybersecurity classifiers can refuse benign security-review content; do not override its model.

1. **States REVIEW mode** and locks the scope to the branch's commits and changed files identified in step 0 (include the exact commit range and file list).
2. **Forces REPORT-ONLY mode**: *"REPORT ONLY. Do not write, modify, or delete any file, and do not post anything. Return findings as a ranked list to be merged into the /review-pr severity report."*
3. **Passes relevant context**: whether the diff touches routes/consumers/webhooks/prompts/fixtures, and any user-mandated findings to include.

Take the agent's findings (it pre-applies its false-positive rulebook and verify pass), map its severities into the report buckets, and merge into the Agent 1 section of the final severity report. Findings the agent marked as disproven are not reported.

Agent 2: The API & CRUD Contract Manager (inherits session model)

Verify CRUD symmetry, HTTP Status Codes, and DTO data leaks.

Agent 3: The Pattern & Refactor Enforcer (inherits session model)

Check adherence to "Existing Tools" patterns. Identify code that can be simplified or modularized.

Agent 4: The Simplicity Advocate (inherits session model)

Actively look for ways to reduce code complexity and volume. For every piece of new code, ask: "Is there a simpler way to achieve the same result with less code?" Prioritize:
- Removing unnecessary abstractions, wrappers, or indirections that don't add value.
- Replacing verbose logic with concise alternatives (e.g., leveraging built-in methods, reducing branching).
- Eliminating dead code, redundant checks, or over-engineered patterns.
- Suggesting inline solutions over extracted helpers when the helper is used only once.
- Flagging premature generalizations — code that handles hypothetical future cases instead of the current need.
The goal is: less code to read, less code to maintain. Simpler code is easier to review, test, and debug.

Agent 5: Test Hygiene — delegated to `feature-test-architect`

Do NOT implement test review logic inline here. The `feature-test-architect` agent (defined in `~/.claude/agents/feature-test-architect.md`) is the **single source of truth** for test quality rules — value audit (library tautologies, object literal lookups, duplicate coverage, redundant splits, per-field fragmentation), coverage-gap detection, duplicated global setup, consolidation via `toMatchObject`/`toEqual`, and business-rule exceptions. Duplicating those rules here creates drift.

When the PR includes test files, invoke the agent via the `Agent` tool with `subagent_type: "feature-test-architect"` and a prompt that:

1. **Locks the scope** to the branch's commits and the changed test/production files identified in step 0. Include the exact file list so the agent does not roam outside scope.
2. **Forces REPORT-ONLY mode** with an explicit instruction: *"REPORT ONLY. Do not write, modify, or delete any file. Return findings as a list (one item per issue) to be merged into the /review-pr severity report. Do not ask the user whether to apply fixes — the /review-pr skill handles user interaction afterwards."*
3. **Asks for two categories of findings**:
   - Coverage gaps: production code in the diff with no matching test.
   - Low-value / redundant tests already present in the diff.
4. **Asks for a concise format** per finding so it can be mapped 1:1 into the severity table:
   ```
   [TEST FILE]:[LINE] | [reason category] | [short actionable recommendation]
   ```

Take the agent's findings verbatim, classify them into the severity buckets (coverage gaps and redundant-split patterns are usually HIGH or MEDIUM depending on impact), and merge into the Agent 5 section of the final severity report.

**Important:** the agent must never touch files during a `/review-pr` run. The skill's contract is review-only — findings become inline GitHub comments for the PR author to act on, not direct code edits.

Agent 6: The Dead Code Detector (inherits session model)

When the PR includes code that transforms, shapes, caps, or filters API/service response data, this agent MUST:
1. Identify every field being accessed, shaped, or removed in transformation functions (e.g., `shapeXDetail`, `mapX`, slimming functions).
2. Locate the actual source of that data — the upstream service schema, Mongoose/TypeORM model, or API route handler — and verify each field truly exists in the real response payload.
3. Flag as **dead code** any transformation logic that operates on a field that does NOT exist in the upstream service's actual response.
4. Pay special attention to:
   - Array caps or `.slice()` on fields that the API never returns (e.g., `activityHistory`, `statusHistory`).
   - Type definitions that declare fields (`RawAttributes`, `RawDetail`, etc.) that map to non-existent API fields.
   - Guard clauses or conditional spreading for fields that can never be present.
   - Constants like `MAX_X_ENTRIES` whose only purpose is to cap a non-existent field.
5. Cross-reference MCP tool type definitions against the real service models (check `src/domain/`, `src/db/`, route handlers, or equivalent paths depending on the service).
6. If uncertain whether a field exists, look it up in the service's codebase before flagging — avoid false positives.

The goal: never let shaping code diverge from the actual API contract. Dead transformation code creates a false sense of data processing and misleads future developers.

Agent 7: Agentic Systems — delegated to `agentic-reviewer` (conditional)

Only when the diff touches agentic/LLM surface — prompt files, LLM client calls (LlmService, Anthropic/OpenAI SDKs, Mastra, LangGraph), workflow/step/node definitions, tool schemas or handlers, MCP servers, fan-out/orchestration code, confidence gating, inbox/ProposedAction flows. Invoke via the `Agent` tool with `subagent_type: "agentic-reviewer"` in REVIEW mode, passing the commit range and scoped file list from step 0. The agent is read-only and report-only by construction. Merge its findings into a dedicated "Agentic systems" section of the severity report, mapped to the same severity buckets. Skip silently for non-agentic diffs.

4. High-Signal Filtering
Constraint: Ignore nitpicks. Focus on vulnerabilities, broken contracts, major pattern deviations, duplicated test setup, missing tests, redundant tests, and simplification opportunities that meaningfully reduce code volume or complexity.

5. Severity-Based Summary Report (MANDATORY)

After all agents complete, you MUST present findings organized into exactly 4 severity categories with a count summary table:

### Review Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | X | Security vulnerabilities, data leaks, broken functionality |
| HIGH     | X | Missing tests, broken contracts, major pattern violations |
| MEDIUM   | X | Redundant tests, unnecessary complexity, code duplication |
| LOW      | X | Minor simplifications, style improvements |

Then list each finding under its severity header, with each item numbered as INITIAL-N (C = Critical, H = High, M = Medium, L = Low). Numbering resets per category.

#### CRITICAL
- **C-1** [file:line] Brief description of the issue
- **C-2** [file:line] Brief description of the issue

#### HIGH
- **H-1** [file:line] Brief description of the issue
- **H-2** [file:line] Brief description of the issue

#### MEDIUM
- **M-1** [file:line] Brief description of the issue
- **M-2** [file:line] Brief description of the issue

#### LOW
- **L-1** [file:line] Brief description of the issue
- **L-2** [file:line] Brief description of the issue

After presenting the summary, you MUST ask:
"Which categories or specific items do you want me to post as comments on the PR? (e.g., 'all H', 'C-1 and H-3', 'all')"

6. GitHub Interaction & Feedback

### Posting Delegation (Haiku — MANDATORY)
Once the user selects which findings to post, delegate the mechanical posting to a subagent via the `Agent` tool with `model: "haiku"`. The subagent executes, it does not write or judge:
- The main (smart) model authors the final comment text for every selected finding **before** delegating — tone and precision are part of the review, not the posting.
- Pass the subagent: repo/owner/PR number, HEAD SHA, and the ready-made list of comments (path, target line, body verbatim).
- The subagent performs the Line Validation, payload construction, and `gh api` call described below (including 422 retries), and reports back which comments were posted and which were skipped as "line not in diff".
- The subagent MUST NOT rewrite, shorten, or merge comment bodies — post them verbatim.

### Comment Placement
- **ALWAYS post inline comments on the exact line where the issue is** using `gh api repos/{owner}/{repo}/pulls/{number}/reviews` with the `comments` array.
- **NEVER create a general/summary PR comment.** Each finding must be an inline review comment attached to the specific line in the diff. A top-level comment with a summary of all issues is explicitly forbidden — it makes it harder to locate where each problem is.
- Use `line` (line number in the file at HEAD) and `side: "RIGHT"` for each comment.
- For new files, the file line number equals the diff line number.
- For modified files, use the line number in the new version of the file.
- All selected findings MUST be posted in a **single `gh api` call** using the `comments` array, so they appear as a cohesive review rather than scattered individual comments.

### Line Validation (MANDATORY — Before Building Payload)
Before constructing the review payload, you MUST verify that every comment's `line` number actually exists in the PR diff. GitHub's API returns HTTP 422 ("Line could not be resolved") if you post a comment on a line that is not part of the diff.

Steps:
1. Run `gh api repos/{owner}/{repo}/pulls/{number}/files --paginate --jq '.[] | .filename + " | " + .status + " | " + (.patch // "NO_PATCH")'` to get all files with their status and patch hunks.
2. For **added** files (`status: "added"`): all lines in the file are in the diff — any line number is valid.
3. For **modified** files (`status: "modified"`): only lines within the `@@` hunk ranges on the RIGHT side are valid. Parse the `@@ -X,Y +Z,W @@` headers to determine which line ranges are commentable.
4. If a finding's line is NOT in the diff (e.g., it's in an unchanged section of a modified file), you MUST either:
   - Move the comment to the nearest line that IS in the diff within the same hunk, adjusting the comment text to reference the original line, OR
   - Drop that comment entirely and note it in the terminal output as "skipped — line not in diff".
5. NEVER attempt to post a comment on a line outside the diff — it will cause the entire review request to fail (all comments are rejected, not just the invalid one).

### How to Post Comments (MANDATORY)
**NEVER use `--field` or `-f` flags with `gh api` to pass the comments array inline.** The `--field` flag does not correctly serialize complex JSON arrays and causes HTTP 422 errors ("is not an array").

Instead, **ALWAYS write the full JSON payload to a temporary file and use `--input`**:

1. Create the payload file at a collision-safe path — `mktemp /tmp/pr-review-payload.XXXXXX.json` (or the session scratchpad) — and write the full request body with the `Write` tool:
```json
{
  "commit_id": "<HEAD_SHA>",
  "event": "COMMENT",
  "body": "",
  "comments": [
    {
      "path": "path/to/file.ts",
      "line": 42,
      "side": "RIGHT",
      "body": "Comment text here"
    }
  ]
}
```

2. Post using `--input`:
```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  -X POST \
  --input <payload-file>
```

This is the only reliable method. Do NOT attempt inline `--field` first — go directly to the file-based approach.

### Language
- **ALL GitHub review comments MUST be written in English.** Regardless of the language used in the terminal conversation with the user, every comment posted to GitHub must be in English.

### Tone of Voice
- Write in **first person** as a friendly colleague doing a peer review (e.g., "I noticed that...", "I think we could...", "I wonder if...").
- The tone must NEVER sound rude, harsh, or condescending — even for critical issues. Every comment should feel like a conversation between teammates, not a verdict.
- Avoid phrasing that sounds accusatory or like a command. Prefer soft, exploratory language:
  - Instead of "This is wrong" → "I think this might cause an issue because..."
  - Instead of "You should add tests" → "I noticed there are no tests for this yet — would be great to cover the rollback path too"
  - Instead of "This is redundant" → "I think this test might already be covered above — not sure it adds new coverage here"
- Professional, gentle, and constructive. Never robotic.
- **Do NOT prefix comments with labels like "H1:", "Finding 1:", "MEDIUM:", etc.** Just write naturally as a human reviewer would.
- Keep comments short and direct. Use bullet points for clarity when needed.

### Approval Process
1. Present the severity-based summary report (step 5) in the terminal.
2. Mandatory Step: Ask the user which items to post on GitHub.
3. Only after user confirmation, post ALL selected findings as **inline review comments** in a single `gh api` call using the `comments` array. Never post a summary comment — only inline comments per finding.

7. Finalization
Closing: You MUST end the response with: "Review complete. Which severity categories or specific items should I post as GitHub comments?"

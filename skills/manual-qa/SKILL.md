---
name: manual-qa
description: >
  Generate a step-by-step manual QA guide for validating a feature change — typically run
  after the automated PR review, before handing off for human review. Use when the user asks
  for "QA steps", "how to validate manually", "steps to test", "manual QA walkthrough", or
  "manual QA guide". Output is a flat, direct guide with: prerequisites, how to perform the
  key action, sequential test scenarios with concrete inputs and expected outputs, a quick
  validation table, and troubleshooting.
argument-hint: <feature description, ClickUp ID, or "current branch">
---

# Manual QA — guide generator

> **Scope note:** the environment specifics referenced below (Tilt/k8s overlays, demo loan shortcuts, fixture paths) belong to the HouseNumbers/Zora monorepo. In any other project, keep the same guide structure but derive prerequisites and steps from that project's own run/setup conventions.

Generate a manual QA guide so a teammate (or future-you) can validate the change in under
5 minutes by following concrete steps.

## Before writing — investigate

1. Read `git diff main...HEAD` (or the user's specified base) to identify what changed.
2. Find the **user-facing entry point**: route, URL, button label, keyboard shortcut.
3. Identify the **input variations** the change affects: statuses, flags, roles, feature
   flags, fileProgress values, etc.
4. Identify the **expected output variations** per input — what the user should see for each
   case (including the "no-op" case if relevant).
5. Find the **preconditions** that the agent/feature needs (e.g. "loan must have changelog
   activity in last 3 days", "user must be admin", "feature flag must be on").
6. **If the diff touches `apps/agent-service/src/workflows/handlers/` (R/P workflows),
   `apps/agent-service/src/workflows/tool-wrapper.ts`, or `apps/agent-service/src/domain/prompts/workflows/<workflowId>.md`:**
   The Cmd+2 demo loan (`loanNumber: 12345`) is short-circuited by a pre-computed fixture
   at `apps/agent-service/src/workflows/mastra/sandbox-fixtures/demo-<loanNumber>/<workflowId>.fixture.json`.
   Output comes from the fixture, NOT the LLM, so prompt/schema edits will appear to have
   zero effect. The QA guide MUST include a Preparation step that disables this — see
   "Agent-service workflow special prep" below.

If anything is unclear, ask the user **one focused question** before drafting. Don't guess
URLs, log strings, or service names — only reference what you've read.

## Agent-service workflow special prep (include verbatim when step 6 above applies)

Add this as a Preparation subsection titled "Disable the agent-service sandbox (once per QA session)":

> To validate changes to agent-service workflow prompts/schemas locally, the
> `LLM_SANDBOX=sandbox_llm` must be turned off — otherwise Cmd+2 reads from the
> pre-computed fixture and your changes will appear to have no effect.
>
> 1. Edit `k8s/overlays/local/services/agent-service/deployment-patch.yaml` and comment out
>    the `LLM_SANDBOX` block:
>    ```yaml
>    # - name: LLM_SANDBOX
>    #   value: "sandbox_llm"
>    ```
> 2. Wait for Tilt to roll the new `agent-app` pod (~30-60s).
> 3. Confirm with:
>    ```bash
>    kubectl exec -n default $(kubectl get pods -n default -o name | grep agent-app | head -1 | sed 's|pod/||') -- printenv | grep LLM_SANDBOX || echo "LLM_SANDBOX unset ✓"
>    ```
> 4. **When QA is done, revert the comment before committing** — the sandbox is the default
>    because it gives deterministic, cheap demos.

The Troubleshooting section MUST also mention: "If the draft comes out byte-identical to
what it was before the change → `LLM_SANDBOX` is probably active again; check the pod's env."

## Required structure

The guide MUST have these sections in this order:

### 1. Preparation (once)
- How to bring the env up (`tilt up`, `pnpm dev`, etc. — pick what fits the project)
- Exact entry point URL with `<PLACEHOLDER>` for IDs (e.g. `http://localhost:5173/applications/<LOAN_ID>/foo`)
- Login / seeding steps if needed
- Preconditions called out explicitly (e.g. "the agent skips when there is no activity in the last 3 days")

### 2. How to perform the key action
- 1–3 lines: where to click, what to fill, which dropdown
- Reference the **actual UI location** (sidebar section, modal title, button label)
- Mention keyboard shortcuts if they exist

### 3. Sequential test scenarios
One block per variation. Each block:
- Has a clear header naming the variation (e.g. "Scenario 2 — Template 2 (vendor orders)")
- Numbered steps with concrete actions
- Ends with **✅ Expected:** describing the exact structure/text/behavior expected
- Each block is self-contained — don't make scenario N depend on scenario N-1 leaving state behind

Cycle the test on a **single fixture** when practical (same loan, change one field at a
time). Use multiple fixtures only when variations require different starting state.

### 4. Quick validation checklist
A markdown table — one row per scenario — with the most-discriminating fields per variation.
Should fit on one screen.

### 5. If something goes wrong
- The most common failure mode (e.g. "empty draft") and the fix
- Where to look at logs: `tilt logs <service>`, NR query, browser console, etc.
- Specific log strings or NRQL recipes — only ones you've verified exist in the code

## Style rules

- **English** by default; switch to PT-BR only if the user asks for it
- **Direct**: bullets and short sentences, no filler ("now let's...")
- **Concrete**: real URLs, real field names, real shortcuts — no placeholders like "the X page"
- **Test order = how a tester would actually run it**: sequential field mutations beat
  spinning up multiple unrelated fixtures
- **Cite only what you've read**: never invent service names, log messages, or NRQL fields
- **No emoji-heavy decoration**: ✅ / ⚠️ for callouts is fine, but don't sprinkle them
- **Length**: aim for under 80 lines of guide content. If it's longer, the scenarios are
  probably too granular — collapse them

## Output

Print the guide directly in the chat. Do not write it to a file unless the user asks.

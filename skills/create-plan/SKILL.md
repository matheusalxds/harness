---
name: create-plan
description: Builds a disciplined implementation plan for a ClickUp card — YAGNI/DRY/TDD principles, reuse discovery, security requirements, typed commit sequence, and a structured plan format with risks and out-of-scope sections. Use when the user asks to plan a card or feature.
argument-hint: <clickup-card-id-or-url>
---

# Create Implementation Plan

Draft an implementation plan for the card provided in: $ARGUMENTS

> **Per-project scope:** the references to `packages/shared-domains`, `packages/shared-middlewares`, and the `reuse-hunter`/`security-sentinel` agents apply to the HouseNumbers/Zora monorepo. In other projects, apply the same principles using that project's own artifacts and the `general-reuse-architect`/`general-security-sentinel` agents.

## Core principles

The plan must be guided by three canonical engineering principles, always applied together:

### YAGNI (You Aren't Gonna Need It)
- Implement **only** what the card requires. Do not anticipate future needs.
- Forbidden: premature abstractions, generalizations, "for the future" configuration flags, generic helpers with no immediate use, extra layers with no concrete gain.
- Three similar explicit lines are better than a premature abstraction. Only extract when the repetition genuinely hurts and the abstraction improves readability.
- If you're thinking "what if in the future..." — stop. The future is another card.
- **NEVER create "man in the middle" — pass-through wrappers.** A function that only calls another function (even renaming parameters or setting constants) and adds no logic — validation, transformation, composition, logging, side effect, invariant encapsulation — is pure indirection and is forbidden. Call the inner function directly. If the inner function isn't exported and that blocks direct use, export it (adjusting the module boundary) instead of creating the wrapper. Single exception: the "inner function" is deliberately private for a documented security/abstraction reason — in that case the wrapper must document the invariant it maintains. No documented invariant, no wrapper.

### Pragmatic DRY (Don't Repeat Yourself)
- **Before creating new code, look for what already exists.** Functions, utilities, hooks, patterns, schemas, middlewares — always check whether something reusable solves it before creating.
- Eliminate **relevant** duplication — but don't force abstraction when the repetition is small and extracting worsens readability or coupling.
- DRY serves maintenance, not aesthetics. Reuse must improve the system, not demonstrate elegance.
- In the plan, explicitly cite the existing utilities/functions that will be reused, with file paths.

#### Middlewares and cross-cutting concerns: reuse, never reimplement (mandatory)
- **Before planning manual validation of headers, auth, tenant/user context, idempotency, or error handling in a route/handler, check `packages/shared-middlewares`** (e.g. `requireTenantId`/`requireUserId` from `@housenumber/shared-middlewares/auth-context`, which set `req.tenantId`/`req.userId`) and the service's own `middleware/` directory.
- **Sibling routes doing the check by hand are NOT a license to repeat it** — they are frequently legacy debt that predates the middleware. The plan follows the canonical middleware; converging the legacy goes in "Out of scope".
- When adopting the middleware, its contract test (e.g. 400 without header) leaves the route's spec — it's already covered in the middleware's package; the route's spec tests the handler with the context the middleware guarantees (`req.tenantId` set).
- If the validation needs behavior the middleware doesn't cover, extend the shared middleware (additive change) instead of duplicating inline — or justify in the plan why not.

#### Types and schemas: shared-domains FIRST (mandatory)
- **Before planning any new type, interface, enum, or schema, ALWAYS check `packages/shared-domains/src/domain/`** (and the service's own domain modules). Grep for the **field names**, not just the type name you imagine — the existing contract may have a different name (e.g. loan attributes live in `LoanApplication["attributes"]` via `loanApplicationSchema`).
- **Why this is non-negotiable**: a new type parallel to an existing contract compiles forever, even when the real contract changes or is renamed. Renaming/changing a field MUST break at compile time at every usage point — that break is the desired behavior. A parallel type silences the break and becomes a **silent bug**: the code compiles but reads a shape that no longer exists.
- Partial reuse counts: if the whole shape doesn't exist but part of it does (e.g. an envelope's `attributes`), reuse that part via indexed access (`SharedType["attributes"]`) and declare locally only what is intrinsically wire/transport-specific.
- Canonical enums/values (statuses, reasons, categories) are NEVER redeclared as string literals — import the constant from shared-domains (`FILE_STATUS`, `DECLINE_REASON`, etc.), including in tests and test factories.
- In the plan's "Existing code reused" section, include an explicit "**Types/schemas**: ..." line listing what was found in shared-domains — or the justification for why nothing fits (search performed, fields absent from every shared schema).

### TDD (Test-Driven Development)
- **Tests before implementation.** The sequence is always RED → GREEN → REFACTOR.
- For each new or modified behavior, describe in the plan the test that will fail first.
- For changes to prompts/agents/LLM: **evals are the tests**. Assertions in the scorer/eval before editing the prompt.
- For bug fixes: a test that reproduces the bug before the fix.
- Never weaken existing test assertions. Never delete a test claiming it's "flaky". If a test fails after the change, the **implementation** is wrong.

## Commit structure (always separated by file type)

The canonical convention (SEMVER prefixes, TDD ordering, special cases, anti-patterns) is maintained in a shared file:

**→ Read `~/.claude/shared/commit-structure.md` with the Read tool before materializing the commits in the plan.**

When planning the **Implementation steps** section, each commit must appear on its own line with:
- The correct SEMVER prefix (`test:`, `feat:`, `fix:`, `docs:`, `chore:` etc. — full table in the shared file)
- Scope in parentheses when applicable (e.g. `test(agent-service)`)
- A short description of the intention
- The list of files it contains

**Hard rule**: never plan a single commit mixing file types (test + production, prompt + eval, code + deps). Even "logically atomic change-sets" must be separated — the three reasons (TDD history, surgical review, isolated revert) are justified in the shared file.

## Mandatory steps

1. **Read the ticket in full before starting** — title, description, comments, attachments, and subtasks. Don't jump to code without understanding the problem, the impact, the success criteria, and the constraints. If there's ambiguity, ask before planning (`AskUserQuestion`).

2. **Read the codebase for real context** — explore the affected areas (handlers, domain, schemas, tests, utilities, types) to understand how the system works today. Use `Explore` agents in parallel when the scope spans multiple areas. The plan must fit the existing conventions and patterns, not create parallel ones.

3. **Apply YAGNI when proposing the solution** — propose the **smallest change** that solves the problem described in the card. If the minimal solution seems too obvious, it's probably right. Sophistication needs concrete justification, not "it feels more robust".

4. **Apply DRY before writing any new code — via the `reuse-hunter` agent (mandatory)** — before proposing any new artifact (type, constant, middleware, helper, validation, fixture, aggregation), launch the `reuse-hunter` agent with a description of what would be created. Its report feeds two plan sections:
   - **REUSE/GAPS** → "Existing code reused" section (what to reuse, with path; or the justification for an empty search).
   - **PROMOTE TO SHARED** → if the logic already exists in another service (or the new code would be the 2nd implementation), the plan must extract it to the shared package in `packages/` instead of duplicating — when the card's scope allows. Pre-existing duplication the card doesn't touch goes in "Out of scope" as a cleanup-card candidate.

4.5 **Gather security requirements — via the `security-sentinel` agent in PLAN mode (when applicable)** — if the card touches a route/endpoint, message-bus consumer, webhook, upload, LLM prompt, committed fixture/schema with customer-derived data, or any multi-tenant query, launch the `security-sentinel` agent in **PLAN mode** with a description of what will be built and the areas touched. Its report (tenant-scoping/ownership requirements, webhook validation, secrets/PII handling, boundary validation) becomes explicit plan steps — it's cheaper to include in the design than to catch in review. Cards that touch none of those surfaces skip this step (note "N/A" mentally, not in the plan).

5. **Apply TDD to the step ordering** — the sequence in the plan must start with "add failing test" before "implement". For each scenario described in "Tests", point to which test file receives the assertion.

6. **Only propose code that goes to production** — no demos, toy examples, or scaffolding that will be discarded. Always consider: error handling, input validation, observability, tests, idempotency, and evolution.

7. **Don't rewrite code that already works** — if code exists that solves the same problem differently, leave it alone. Rewrites only with objective justification (measurable performance, security CVE, significantly greater clarity). **Forbidden**: refactors for aesthetics, personal preference, or "it would be cleaner".

8. **Disciplined scope** — touch only what's needed to close the card. Adjacent problems identified during exploration go in **"Out of scope"** or **"Next steps"**, never in the current plan. This is the most-broken rule in long plans — respect it.

9. **Validate the minimum by reading the real file, not the summary** — if an exploration agent reported what changes, open the file with `Read` before finalizing the plan. Summaries induce scope errors (proposing to remove something that no longer exists, adding a rule already present, etc.).

10. **Persist the plan after the user validates it** — once the user approves the plan, save it in full to `.plans/<clickup-id>-<slug>.md` at the repository root. Ensure `.plans/` is git-ignored **without touching the team's `.gitignore`**: add the line `.plans/` to `.git/info/exclude` if it's not already there. Tell the user the saved path — that file allows resuming implementation in another session and is the default input of `/split-plan`.

## Expected plan format

- **Context** — 2-3 lines explaining the why of the change: the problem it solves, the constraint it addresses, the expected outcome
- **Problem understanding** — what the card asks for, in technical language
- **Recommended approach** — the minimal solution that solves it, justified in YAGNI/DRY terms
- **Existing code reused** — list of functions/utilities/patterns with file paths (explicit DRY), based on the `reuse-hunter` report. If the answer is "none, it's all new", explain why. Include a "**Promotion to shared**: ..." line when the report indicates code duplicated across services — stating whether the extraction to `packages/` is part of this plan or goes to "Out of scope" as a cleanup card.
- **Affected files** — list of files to be created or modified, with one line describing the change in each
- **Implementation steps** — ordered sequence following TDD (RED → GREEN → REFACTOR). Each step must be executable in isolation. The section must explicitly list the **planned commits**, one per line, with SEMVER prefix and file list. E.g.:
  - `test(agent-service): <description>` — `apps/agent-service/src/.../x.spec.ts`
  - `docs(agent-service): <description>` — `apps/agent-service/src/domain/prompts/workflows/x.md`
  - `chore(agent-service): <description>` — `apps/agent-service/package.json`
  Never plan a "single commit" merging types — see the "Commit structure" section.
- **Tests** — scenarios covered (happy path, edge cases, failures), pointing to which test file receives each assertion
- **Risks and points of attention** — what can break, what needs monitoring, dependencies on other work in progress
- **Out of scope** — identified but deliberately not addressed here. Always populate this section, even if with "nothing adjacent was identified".
- **Verification** — concrete commands to validate end-to-end (e.g. `CI=true NO_COLOR=1 TURBO_UI=false pnpm turbo test:agentic --filter=<pkg>`), not generic instructions like "run the tests".

## Red flags in a plan

If the final plan has any of these, go back and redo it:

- New files without a clear justification of why nothing existing fits (violates DRY)
- A plan proposing new code without evidence that the `reuse-hunter` was consulted — or duplicating inside a service logic the report flagged as existing in another service (the canonical home would be `packages/`)
- **A new type/interface/enum with fields that already exist in `shared-domains`** (or canonical values redeclared as string literals) — a potential silent bug: changes to the real contract don't break the parallel type. The plan must reuse the shared type or justify the empty search.
- Abstractions/interfaces/helpers introduced "to make future changes easier" (violates YAGNI)
- Implementation described before tests in the steps section (violates TDD)
- Refactors adjacent to the card's scope (violates disciplined scope)
- A "Verification" section with generic commands, or missing
- An "Out of scope" section empty or missing (there's almost always something identified that stays out — make it explicit)
- Generic "Risks" with no relation to the concrete change
- **A single commit mixing file types** (test + production, or prompt + eval) — violates the commit structure. Steps must list `test:`, `feat|fix|docs:`, `chore:` as separate commits.
- **"Man in the middle" functions** — wrappers that only call another function without adding concrete logic (validation, transformation, composition, logging, side effect). Pure indirection is forbidden. If the wrapper only forwards args, call the inner function directly and (if needed) export it from the source module. This anti-pattern NEVER appears in the final plan.

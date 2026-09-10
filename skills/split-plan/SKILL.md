---
name: split-plan
description: Splits an implementation plan into individually shippable feature files — creates a subfolder with one Markdown file per feature plus an overview mapping dependencies, so features can be implemented sequentially or in parallel. Use when the user asks to split, break down, or parallelize a plan.
argument-hint: <plan-file-path>
---

# Split Plan into Features

Input: the plan file passed in $ARGUMENTS; if absent, use the most recent file in `.plans/` (where `/create-plan` persists validated plans); then the plan most recently produced in this conversation; if none exists, ask which plan to split.

## Steps

1. Read the full plan and identify independently shippable features — vertical slices that each deliver working behavior, not horizontal layers ("all schemas", "all tests").
2. Create a subfolder named after the plan, next to the source plan file (default `plans/<plan-slug>/`; if the plan only exists in conversation, confirm the destination with the user).
3. Write one file per feature, named `NN-<feature-slug>.md`, containing:
   - **Goal** — what this feature delivers on its own
   - **Scope** — files touched and planned commits (keep the source plan's commit typing)
   - **Tests** — scenarios this feature must cover
   - **Depends on** — explicit feature numbers (e.g. `depends on: 02`), or `none`
   - **Verification** — the concrete verification commands from the source plan that exercise this feature (filter the plan's verification section to this feature's scope; if none apply, state an objective way to verify)
   - **Done when** — objective completion criteria
4. Write `00-overview.md` with: the ordered feature list, which features are sequential vs parallelizable (derived from the dependency declarations), and a suggested implementation order.
5. Report the folder path and a one-paragraph parallelization summary.
6. **Mirror the split into ClickUp (ask first)** — after reporting, ask the user whether to create the ClickUp structure for this split. If they accept:
   - **Parent card** — if the source plan is tied to an existing ClickUp card (e.g. the plan file is named `.plans/<clickup-id>-<slug>.md`), use that card as the parent; do NOT create a duplicate. Otherwise, draft a new parent card from the source plan following the `/create-cu-card` house format (Summary / What? / Why? / How? / Acceptance Criteria) and confirm the destination list before creating.
   - **Subtasks** — create one subtask per feature file under the parent, titled `NN — <feature title>`. The description carries the feature's Goal, Scope (with the planned commits), Tests, Verification, and Done when, following the rendering rules in `~/.claude/shared/clickup-conventions.md`.
   - **Link back** — after creation, add each subtask's URL to its feature file (a `ClickUp:` line right under the title) and list all subtask links in `00-overview.md`.
   - Show the drafted parent content and the subtask titles to the user for approval **before** creating anything in ClickUp.

## Rules

- Each feature file must be executable in isolation by someone holding only that file plus the overview.
- Dependencies are always explicit by feature number — never implied by ordering.
- Split and reorganize the source plan's content — do not rewrite or invent; if the plan lacks information a feature file needs, flag the gap in that file instead of filling it in.
- Never create ClickUp items without the user's explicit approval of the drafts and the destination — and never as a silent side effect: step 6 always starts with the question.

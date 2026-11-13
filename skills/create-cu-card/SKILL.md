---
name: create-cu-card
description: Writes ClickUp card content in the house format — Summary, What?, Why?, How?, Acceptance Criteria, Slack — following ClickUp's description rendering rules. Use when the user asks to create a ClickUp card, write a ticket, or draft card content.
disable-model-invocation: true
---

# Rules for Creating ClickUp Cards

Shared conventions (per-surface rendering rules, language): read `~/.claude/shared/clickup-conventions.md` first and follow it. Before creating the card, show the drafted content to the user and confirm the destination list — never create a card in a guessed location.

## Formatting Rules
- Formatting follows the **task descriptions** surface rules in the shared conventions file: `###` titles, `####` nested sub-titles, `-` bullets, no inline code spans, blank lines only before section titles
- Chain title levels by context: a sub-title nested inside a section's context uses `####` (H4) (e.g. Deliverables inside Spike scope, Phasing inside How?). Inline bold labels with content on the same line (e.g. **Done when:** ...) stay bold, they are not titles
- Use `-` for bullets in What/Why/How sections; the Summary flow uses a numbered list
- NEVER modify sections other than Summary/What/Why/How/Acceptance Criteria - preserve them exactly as provided

## Required Sections

### Title
- Generate a clear, concise title that describes the card's intent
- Use prefixes when appropriate: `[Bug]`, `[Feature]`, `[Chore]`, `[Refactor]`, `[Spike]`

### Summary
- ALWAYS the first section — the reader must understand the whole card from this block alone, before any detail
- Written from a **product point of view**: lead with the impact, not the implementation. The reader (PM, stakeholder, teammate outside the code) must come away knowing WHO benefits, WHAT pain or manual work disappears, and WHAT changes in outcomes (time saved, touches removed, new capability unlocked)
- Open with 1-2 plain-language sentences framing today's pain vs. what this card changes (before → after). Quantify when possible ("multiple human touches over days" → "one 10-second review")
- Then lay out "the flow in one pass": a short numbered list (3-6 steps) walking the end-to-end behavior in order — trigger → action → outcome → who reviews/benefits
- Close with a one-line bridge to the rest (e.g. "The detailed plan follows.")
- No jargon that requires reading the How? section first; name services/components only when the reader needs them to follow the flow — the Summary must survive being read by someone who has never opened the codebase
- For trivial cards (small chores/bugs), the numbered flow may collapse to a single sentence — but the Summary section itself is never omitted

### What?
- Describe directly what needs to be done
- Each point as a separate bullet with `-`

### Why?
- Explain the reason/context in simple terms
- Include business impact or technical justification
- Each point as a separate bullet with `-`

### How?
- Connect actions in logical sequence
- Do NOT include git branch creation steps
- Each step as a separate bullet with `-`

### Acceptance Criteria
- State the concrete, verifiable conditions that mean the card is done — a reviewer must be able to check each one objectively, without asking the author what "done" meant
- Prefer measurable conditions over vague ones: a passing test, a metric threshold (before → after or a floor), a command that exits clean, an observable behavior — never "works well" or "is improved"
- Name how each criterion is verified when it is not obvious — which test, which command, which report or dashboard
- When the outcome is genuinely exploratory and no pass/fail bar exists yet, mark the Title [Spike] and make the deliverable the finding itself (a measurement plus a recommendation), not a threshold
- For trivial cards the criteria may collapse to a single bullet, but the section is never omitted
- Each criterion as a separate bullet with `-`

### Slack
- Always include this section with the relevant Slack thread link

## Output Format Example

```
### Summary
One or two product-framed sentences a reader can understand with zero context: today's pain (who suffers it and what it costs), and what changes with this card (before → after, quantified when possible).
The flow in one pass:
1. Trigger — what starts the behavior.
2. Action — what the system does.
3. Outcome — where the result lands and what pain it removes.
4. Review — who approves/benefits and what happens after.
The detailed plan follows.

### What?
- First point describing the problem or requirement.
- Second point with additional context.

### Why?
- Explanation of the business or technical reason.
- Impact if not addressed.

### How?
- First step to solve the issue.
- Second step continuing the solution.
- Final step to complete the task.

### Acceptance Criteria
- A concrete, checkable condition that means done (e.g. a passing test, a metric threshold, an observable behavior).
- How each criterion is verified when not obvious (which test, command, or report).

### Slack
<link to relevant Slack thread>
```

## Important
- Keep the same style consistent across all cards
- Be specific and actionable
- Avoid vague descriptions
- NEVER modify other sections (e.g. Slack) - keep them exactly as provided

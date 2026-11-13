---
name: agentic-workflows
description: Prompt engineering and orchestration patterns for agentic systems — system prompt structure, confidence scoring and gating, fan-out, dedup and idempotency, token budget management, plus a review checklist. Use when writing or reviewing agent prompts, soul prompts, workflow handlers, confidence thresholds, ProposedAction/inbox flows, tier1 checks, or fan-out pipelines that process many entities with an LLM.
---

> **Do not move, rename, or delete this file.** The `agentic-reviewer` agent
> (`~/.claude/agents/agentic-reviewer.md`) reads it by absolute path as its primary
> rulebook and aborts if it goes missing. Because it is read with `Read` rather than
> `Skill`, the skill usage counter reports zero even while it is in use.

## Prompt Engineering for Agentic Systems

### Prompt design principles for agents with tools

#### System prompt structure
1. **Role and constraints**: who the agent is, what it must never do
2. **Domain knowledge**: the business context the agent needs (not what it can discover through tools)
3. **Tool usage guidance**: intentions and strategies, not specific calls
4. **Output format**: expected schema, confidence scoring, reasoning structure
5. **Guardrails**: confidence limits, when to escalate to a human, when to stop

#### Decoupling the prompt from the tool interface
- **Avoid**: "Call `get_order` with the orderId, then call `get_customer` with the customerId"
- **Prefer**: "Gather the full order context and understand the customer situation before drafting a response"
- The prompt guides **intentions**; the tool descriptions guide **how to execute**
- This lets you rename or refactor tools without breaking prompts
- Exception: when call ordering is business critical (compliance, idempotency), be explicit

#### Confidence scoring in the prompt
- Instruct the agent to report confidence (0-1) alongside a **structured result**, not free-form reasoning:
  - `evidence_present[]` / `evidence_missing[]`: verifiable facts that support the decision, or that are missing
  - `ambiguities[]`: what was left open
  - `requires_human_review`: when the agent itself identifies that the case falls outside policy
- Self-reported confidence is NOT a calibrated probability. Treat it as an ordinal signal and calibrate it against real approval/rejection data per task type before trusting the cutoffs
- Define clear anchors: "0.9+ = all data confirms action, 0.7-0.9 = likely correct but some ambiguity, <0.5 = insufficient data"
- Never let the agent decide thresholds. Thresholds belong to the code (confidence gates)
- The prompt defines **how to evaluate**, the code defines **what to do with the evaluation**
- Confidence **complements** deterministic validation, authorization, and policy checks. It never replaces them

#### The paradox of examples
- Examples are extremely useful for showing the expected format
- But agents **replicate implicit patterns**: item counts, text style, exact structure
- If an example has 2 tags, the agent produces 2 tags. If it has 3 bullets, it produces 3 bullets.
- **Mitigation**: vary the examples, add explicit comments ("this is just one example, actual count varies"), or omit examples and rely on the schema

#### Few-shot vs zero-shot for tool calling
- **Zero-shot** (description only): better for simple tools with clear schemas
- **Few-shot** (examples in the prompt): better for complex tools where the agent often gets it wrong
- Cost: every few-shot example consumes budget tokens on every execution
- Rule: start zero-shot, add few-shot only where errors are recurring

#### Prompt versioning and testing
- Prompts are code. Version them in git, not in environment variables
- Test prompts with real inputs and evaluate structured outputs, not just "looks good"
- Evaluation metrics: schema compliance rate, confidence calibration, action accuracy, false positive rate
- Keep prompts in separate files (`.md`) to make review and diffing easier
- Prompt and code go in separate commits (house convention, aligned with `~/.claude/shared/commit-structure.md`). This preserves attribution, a clean diff, and isolated reverts. The atomic unit of deploy is the PR, not the commit: intermediate commits do not need to be individually deployable, so the separation does not break functionally coupled changes

---

## Agentic Workflow Orchestration

> The concepts named in this file (`ProposedAction`, inbox, tier1, passive mode, compliance-blocked, `loanId`/processor) come from our agent-service (HouseNumbers/Zora). In other systems, treat them as examples of the pattern, not as required vocabulary.

### Execution patterns

#### When to use each path
- **Deterministic pipeline** (no LLM): a sequence of data fetch, transformation, and action. Use it when the logic is predictable and needs no "judgment".
- **LLM reasoning plus ProposedAction** (Path B): the agent analyzes context and proposes actions with confidence. The pipeline does the gating and execution. Use it when the agent needs to interpret, classify, or write, but execution stays controlled.
- **Agentic tool calling** (Path A): the agent calls tools directly with inline gating. Use it when the agent needs real-time feedback on tool results to decide the next steps.
- **Content-only inbox** (Path C): the agent generates structured content that goes straight to a human inbox. Use it when there is no automatable action, only information for review.

#### Golden rule: minimize what the LLM orchestrates
- **Data fetching is code, not prompt**. If you know which data the agent needs, fetch it beforehand and hand it over assembled.
- The LLM should be used for: analysis, classification, writing, decisions under ambiguity.
- The LLM should **not** be used for: sequencing predictable API calls, paginating results, filtering lists, transforming data.
- In fan-outs (processing N entities), precompute each entity's context in code and pass it as compact input to the LLM. Do not let the LLM call 11 tools per entity.

#### Tier1 checks (fast path without the LLM)
Good candidates for tier1:
- Checking that the event has the minimum required data (loanId exists, payload not empty)
- Checking whether the workflow already ran recently for this entity (dedup)
- Validating business preconditions (loan is not in a terminal status, processor is active)
- Checking whether there is new data since the last execution

Bad candidate for tier1:
- Anything that requires semantic interpretation
- Checks that depend on external data that is expensive to fetch

#### Confidence gate tuning

> The numbers below (0.90/0.70, 90%/10%) are the calibrated defaults of our agent-service, house starting points rather than universal constants. Adjust them by impact, reversibility, compliance, and the asymmetric cost of an error; and read approval/rejection rates with sample selection and reviewer behavior in mind. Approval rate alone is an incomplete indicator: combine it with sampling of auto-executed cases, the edit-before-approve rate, and the downstream outcome, segmented by task type.

- Thresholds are per **action type**, not per workflow. Actions with external side effects (sending email, publishing) need a high threshold (0.90+); internal actions (creating a draft, creating a task) can be lower (0.70+)
- **Compliance-blocked actions** always force inbox review, regardless of confidence
- **Passive mode**: when the entity is in transition or in a sensitive state, force everything to the inbox
- Calibrate thresholds with real data. Monitor the approval/rejection rate in the inbox and adjust
- If more than 90% of inbox items are approved without edits, the threshold is too conservative
- If more than 10% are rejected, the threshold is too permissive

#### Fan-out patterns
- Use **concurrency limiting** (slots) to avoid OOM and rate limiting
- **Pre-filter** before the fan-out: drop entities that do not need processing
- **Compact briefing**: instead of the LLM calling N tools per entity, precompute a JSON summary and pass it as context
- **Token budget per iteration**: the soul prompt and the tool schemas are identical across fan-out iterations. Consider whether the redundancy can be reduced
- **Timeout per entity**: do not let one slow entity stall the entire fan-out

#### Dedup and idempotency
- Always check the action log before proposing actions (to avoid duplicate emails and duplicate tasks)
- Use a query of recent actions as an implicit gate: if a similar action ran in the last N hours, skip it or lower the confidence
- For mutations, prefer a **pre-check** (verify state before executing) over a **post-check**, while being aware that read-before-write is not atomic (TOCTOU): the pre-check is an optimization, and the real guarantee of invariants comes from unique constraints, transactions, compare-and-set, or atomic idempotency keys
- Payload dedup via a hash of a **canonical representation** (explicit, ordered identity fields, never a raw `JSON.stringify`: key order and volatile fields change the hash, and sensitive payloads should not become a persisted identifier)
- **Human approval has a shelf life**: between approving and executing, state and permissions can change. Revalidate both at execution time, bind the approval to the approved payload (hash or version, so an altered payload invalidates the approval), and expire old approvals

#### Token budget management per execution
- Monitor tokens consumed per workflow execution (input plus output)
- Workflows with fan-out are the biggest consumers. Identify them and optimize them first
- Reduce the tool schemas sent to the LLM: filter and send only the tools each workflow needs
- Long prompts with instructions the agent already "knows" (from the system prompt) are waste. Avoid repetition between the system prompt and the workflow prompt
- Log token usage per execution to detect drift (gradual growth in consumption)
- Cost, step, and duration limits are enforced **in code** (hard caps that abort the execution). Monitoring alone observes the overrun, it does not prevent it

### Review checklist for agentic systems

When reviewing workflow or agentic handler code, check:

**Unnecessary round-trips:**
- [ ] Does the handler delegate data-fetching sequences to the LLM that could be deterministic code?
- [ ] Is the LLM paginating results, filtering lists, or transforming data?
- [ ] Does the fan-out create N agents that repeat the same queries? Precompute the context.

**Token waste:**
- [ ] Are identical tool schemas re-sent on every fan-out iteration?
- [ ] Does the system prompt repeat information already in the workflow prompt?
- [ ] Does the prompt include instructions the tool descriptions already cover?

**Tool design:**
- [ ] Does any tool accept `Record<string, unknown>` or a generic dictionary?
- [ ] Do error messages guide the agent's recovery, or are they generic (400 Bad Request)?
- [ ] Do mutation tools have the correct annotations (destructiveHint, idempotentHint)?
- [ ] Do constrained choices use enums/literals instead of free strings?

**Confidence and gating:**
- [ ] Are thresholds calibrated with real approval/rejection data?
- [ ] Do actions with external side effects have a gate calibrated to the risk (in our policy, a threshold of 0.90 or higher)?
- [ ] Do compliance-blocked actions force inbox review?
- [ ] Is there a passive mode for entities in transition?

**Dedup:**
- [ ] Does the handler check recent actions before proposing new ones?
- [ ] Is there protection against duplicate inbox items on retries?
- [ ] Do mutations pre-check state before executing?

**Prompt quality:**
- [ ] Does the prompt guide intentions, or dictate specific tool calls (fragile coupling)?
- [ ] Do the examples in the prompts vary, or do they replicate implicit patterns?
- [ ] Are the confidence anchors clearly defined?

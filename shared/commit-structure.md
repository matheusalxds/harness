# Commit Structure — Canonical Convention

Single source of truth for commit splitting rules used across skills (`/create-plan`, `/generate-commit-msg`, `/tdd`, `/address-pr-comments`, etc.).

## General rule

**Never mix file types in the same commit.** Every commit represents **a single, clear, isolated intention**, with a single SEMVER prefix.

The separation exists for three concrete reasons:
1. **History tells the TDD story** — `test:` (RED) followed by `feat:` / `fix:` (GREEN) keeps the intention traceable in `git log`.
2. **Review becomes surgical** — the reviewer doesn't have to untangle changes of a different nature.
3. **Reverts stay isolated** — fixing one commit doesn't drag along unrelated changes.

Commits mixing types are forbidden even when the change-set looks "logically atomic".

## SEMVER prefixes by file type

| Prefix | Scope |
|---|---|
| `test:` | Test and eval files — `*.spec.ts`, `*.test.ts`, `*.eval.spec.ts`, test fixtures, snapshots |
| `feat:` | Production code that adds new behavior |
| `fix:` | Production code that fixes a bug |
| `refactor:` | Production code that changes structure without changing behavior |
| `perf:` | Production code focused on performance |
| `docs:` | `*.md`, documented schemas, examples, **LLM/agent prompts** (files under `prompts/` or similar) |
| `chore:` | Dependencies (`package.json`, lockfile) **OR** config/build (`tsconfig`, `biome.jsonc`, CI, Dockerfile, scripts) — in separate commits from each other |
| `build:` | Build system and external dependencies (alternative to `chore:` when the repo uses this granularity) |
| `ci:` | CI/CD pipeline (workflows, CircleCI, GitHub Actions) |

## Canonical order for TDD

1. **`test(<pkg>): <description>`** — commit with **only** the test/eval files that make up the RED
2. **`feat|fix|refactor|docs(<pkg>): <description>`** — commit with **only** the production code (or prompt/docs) that makes the GREEN pass
3. **Separate additional commits** for each type touched by the same change:
   - `docs:` for `*.md`, README, prompts
   - `chore:` for deps (`package.json` + lockfile together, nothing else)
   - separate `chore:` for config/build (or `build:` / `ci:` if the repo distinguishes them)

The **same base description** is reused across the paired commits — only the prefix changes. This makes the pairing visible in `git log`.

### Example

Change: add a rule to an agent prompt + a new assertion in the eval.

❌ **Wrong** — single commit:
```
feat(agent-service): refine R9 borrower email — reactive large deposits, question-format LOE
  apps/agent-service/src/domain/prompts/workflows/r9.md
  apps/agent-service/src/workflows/handlers/r9.agents.eval.spec.ts
```

✅ **Correct** — two commits:
```
test(agent-service): add R9 borrower LOE and large-deposit scorer fields
  apps/agent-service/src/workflows/handlers/r9.agents.eval.spec.ts

docs(agent-service): refine R9 borrower prompt — reactive large deposits, question-format LOE
  apps/agent-service/src/domain/prompts/workflows/r9.md
```

## Special cases

### LLM / agent prompts
`*.md` files under `prompts/` (or equivalents) are `docs:`, **not** `feat:`. They are text that guides the model, not production code that implements logic. Remember: the behavior change comes from the test (eval) + the prompt together, but each one goes in its own commit.

### Snapshot tests
Snapshot updates go with the `test:` commit corresponding to the change that produced the new snapshot — not in their own commit.

### Rename + edit
A pure rename is a separate commit (`refactor:` or `chore:`). Rename + substantive edit may be a single commit if the rename is a direct consequence of the edit.

### Lockfile-only
If only the lockfile changed (e.g., after `pnpm install` with no `package.json` change), skip it — don't commit. Only commit the lockfile when it comes with a `package.json` change.

## Anti-patterns

- Commit mixing test + production code ("atomic change-set")
- Commit mixing production code + docs
- Commit mixing `package.json` + production code
- Generic message like "update" or "wip"
- Message describing the file change instead of the intention ("add field X to schema Y" vs. "allow users to set X preference")
- Wrong prefix (e.g., `feat:` for a prompt-only change — it must be `docs:`)

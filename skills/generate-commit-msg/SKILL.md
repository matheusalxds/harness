---
name: generate-commit-msg
description: Full pre-commit flow — verifies test coverage via the feature-test-architect agent, runs lint/format and the test suite, then splits the working tree into typed commits (test/feat/fix/docs/chore) following the shared commit-structure conventions. Use when the user asks to commit the current work.
disable-model-invocation: true
---

# Verify and Commit

Steps to verify your work before committing

0. Verify test coverage (MANDATORY — run before anything else)
  • Launch the `feature-test-architect` agent to analyze all changed production files
  • The agent will identify untested code paths and report gaps
  • If gaps are found, write the missing tests BEFORE proceeding to step 1
  • Only proceed to step 1 after the agent confirms all production code has test coverage

1. Check code quality
  • Run lint, format, and any other quality checks.
  • Make sure there are no relevant errors or warnings.
2. Run the test suite
  • Run all tests before creating any commit.
  • If following TDD, implement changes in small increments.
3. Prepare the commit message
  • Write a commit message with up to 100 characters.
  • Always write the commit message in English.
  • Be clear and direct, describing exactly what the change does (the intention, not the files touched).
  • The same base description is reused across paired commits (e.g., `test:` + `feat:`) — only the prefix changes.

4. Split into separate commits per file type
  **→ Before staging the first commit, read `~/.claude/shared/commit-structure.md` with the Read tool.** It is the canonical source for:
  • The prefix → file-type table (`test:`, `feat:`, `fix:`, `refactor:`, `perf:`, `docs:`, `chore:`, `build:`, `ci:`)
  • The required TDD ordering (test → production → docs → chore)
  • Special cases (LLM prompts are `docs:` not `feat:`; snapshot updates go with their test commit; lockfile-only changes are skipped)
  • Anti-patterns (never mix test + production, never mix production + docs, never mix `package.json` + code)

  Execution template for each commit (repeat per file-type group until the working tree is clean):
  ```
  git add <scoped paths>
  git co "<prefix>(<scope>): <description>"
  ```

  Never use `git add .` or `git add -A` — always scope the add to the specific files belonging to this commit's type.

5. Run the test suite again
  • Make sure everything passes after all commits are completed.

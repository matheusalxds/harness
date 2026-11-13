---
name: git-cb
description: Creates a new branch named after a ClickUp card (type/<clickup-id>-<short-description>) and moves the card to "in progress". Use when the user asks to create a branch for a card or starts work on a ClickUp task.
argument-hint: <clickup-card-id-or-url>
disable-model-invocation: true
---

# Create Branch from ClickUp Card

ClickUp access (CLI invocation, auth check, command list): read `~/.claude/shared/clickup-conventions.md` first and follow it.

Create a new branch based on ClickUp card:

- Use the $ARGUMENTS as ClickUp task identifier
- Read the card to get context (title, description):
  ```bash
  node .agents/skills/clickup/query.mjs get $ARGUMENTS
  ```
- Follow conventional-commit type prefixes for branch naming:
  - feat/ for new features
  - fix/ for bug fixes
  - chore/ for maintenance tasks
  - refactor/ for code refactoring
- Use a very short, clear branch name
- Branch format: <type>/<clickup-id>-<short-description>
  - Example: feat/868g584nb-date-table
- Create the branch with:
git cb <branch-name>
- After the branch is created, move the card to "in progress":
  ```bash
  node .agents/skills/clickup/query.mjs status <clickup-id> "in progress"
  ```
  The match is case insensitive and partial. If the command fails (e.g. the list has no "in progress" status), run `status <clickup-id>` with no argument to list the valid ones, report the error to the user, and do not block the branch creation.
- Inform the user:
  - The branch name created
  - That the ClickUp ticket was moved to "in progress" (or that the status update failed, with the reason)
  - Next steps to start development

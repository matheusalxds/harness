---
name: git-cb
description: Creates a new branch named after a ClickUp card (type/<clickup-id>-<short-description>) and moves the card to "in progress". Use when the user asks to create a branch for a card or starts work on a ClickUp task.
argument-hint: <clickup-card-id-or-url>
disable-model-invocation: true
---

# Create Branch from ClickUp Card

Create a new branch based on ClickUp card:

- Use the $ARGUMENTS as ClickUp task identifier
- Access ClickUp to get context about the card (title, description)
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
- After the branch is created, update the ClickUp ticket status to "in progress" using the ClickUp MCP update-task tool with the task ID and `status: "in progress"`. If the status update fails (e.g., the list does not have an "in progress" status), report the error to the user but do not block the branch creation.
- Inform the user:
  - The branch name created
  - That the ClickUp ticket was moved to "in progress" (or that the status update failed, with the reason)
  - Next steps to start development

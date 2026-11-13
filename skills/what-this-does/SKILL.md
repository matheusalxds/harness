---
name: what-this-does
description: Reviews all files changed in the current branch (final result, not per-commit) and produces a clear English message explaining what the change does and why the PR exists. Use when the user asks what a branch does or when another skill needs a PR summary.
---

# What This Does

Review all files changed in this branch:
- Check only the final result, not each commit;
- Review every file that was modified in this branch;
- Write a clear and direct message explaining what this change does and why this PR exists;
- Make sure the message is easy to understand and communicates the purpose of the work;
- Write the message in English;
- Return the message text to the caller (the terminal, or a delegating skill such as `/update-pr`) — do not post it anywhere yourself.

---
name: address-pr-comments
description: Finds the GitHub PR for the current branch and works through unresolved review comments — implementing accepted suggestions, replying in-thread, and explaining rejected ones. Use when the user asks to address, respond to, or resolve PR review comments.
disable-model-invocation: true
---

# Address PR Comments

Find the GitHub PR associated with the current branch.

## Step 0: Ownership check (mandatory)

```bash
gh api user --jq .login
gh pr view --json author,state --jq '{author: .author.login, state: .state}'
```

- If the PR is `CLOSED` or `MERGED`, stop and tell the user.
- If the PR author is NOT the current user: do not edit code or push. You may only draft reply suggestions and show them to the user — post nothing without explicit confirmation.

## Workflow

Fetch unresolved review threads (thread state and in-thread replies require the GraphQL API, not REST):

```bash
gh api graphql -f query='query($owner:String!,$repo:String!,$pr:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$pr){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:20){nodes{id databaseId body author{login} path line}}}}}}}' -f owner=<owner> -f repo=<repo> -F pr=<number>
```

For each unresolved review comment or thread:

1. Read the full thread and inspect the related code.
2. Determine whether the comment is still relevant to the current version of the PR.
3. Assess whether the suggested change is correct and within the scope of the PR.
4. If the suggestion makes sense:
    * Implement the smallest necessary change.
    * Run the relevant tests, linting, or type checks.
    * Draft a reply in the same thread summarizing what was changed.
5. If the suggestion does not make sense:
    * Do not change the code.
    * Draft a reply with a concise technical explanation.
6. If the comment is outdated, already addressed, or no longer applicable:
    * Draft a reply explaining why.

## Confirmation gate (mandatory)

Before posting ANY reply to GitHub, show the user a summary table: thread → action taken (code change / explanation / outdated) → draft reply text. Only post after the user approves (all at once or per-thread). Replies to a thread use the comment's `databaseId`:

```bash
gh api repos/<owner>/<repo>/pulls/<number>/comments -f body='<reply>' -F in_reply_to=<databaseId>
```

## Rules

* Always reply directly in the existing review thread.
* Never create a new top-level PR comment for a review comment.
* Do not make unrelated refactors or changes outside the comment's scope.
* Do not resolve a thread unless the comment has been addressed or explicitly answered.
* Do not reply to already resolved threads unless new action is required.
* Never close or merge the PR under any circumstances.

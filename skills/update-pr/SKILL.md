---
name: update-pr
description: Updates the current branch's GitHub PR — SEMVER title, Criteria of Done, ClickUp link, "What this does" section, env-var change tables, review comments (via /address-pr-comments), assignee, and the @claude mention. Use when the user asks to update or fill in the PR.
disable-model-invocation: true
---

# Update PR

IMPORTANT: Use the Haiku model (model: "haiku") for all Agent/subagent calls in this skill to maximize speed.

Find the GitHub PR for this branch:
- Update the PR title to a **mandatory** SEMVER pattern, following the canonical prefix table in `~/.claude/shared/commit-structure.md` (`feat:`, `fix:`, `refactor:`, `perf:`, `docs:`, `chore:`, `build:`, `ci:`). Format: `<prefix>(<scope>): <description in English, lowercase, imperative>` — example: `feat(web-app): enable tag filtering on per-application tasks page`. The scope is the affected package/app (`web-app`, `agent-service`, etc.). Pick the prefix from the PR's dominant intention (usually the `feat:`/`fix:`/`refactor:` commit carrying the production work — ignore the paired `test:` commit, it only reflects the TDD RED). Never include the ClickUp card ID in the title (the link goes in "Important links").
- Update the "Criteria of Done" section based on the steps this PR executes; check only what actually applies.
- Update the "Important links" section: the ClickUp card ID comes from the branch name (convention in `~/.claude/shared/clickup-conventions.md`) — add the card link so it can be found in ClickUp with one click.
- Update the "What this does" section by invoking the `/what-this-does` skill via the Skill tool and using the returned text.
- Check whether the change adds new environment variables in `.env.sample` or `.circleci/config`; if so, add a "New env vars" section with a table showing names and values.
- Check whether environment variables were **removed** from `.env.sample` or `.circleci/config`; if so, add a "Removed env vars" section with a table showing the names and, when relevant, the reason for removal.
- If the PR has review comments, handle them by invoking the `/address-pr-comments` skill (it is the single source for deciding whether to apply or reply — including the confirmation gate before posting).
- Check that I am the assignee; if not, add me.
- At the end add "@claude", only if it is not already present in the PR description.

---
name: slack-msg
description: Generate a Slack message requesting review for the current branch's PR. Writes in first person, friendly human tone, with PR + ClickUp links. Optional argument — word limit (default: 200). Example usage — `/slack-msg` for the default limit, `/slack-msg 100` to cap the message at 100 words.
---

IMPORTANT: Use the Haiku model (model: "haiku") for all Task/subagent calls in this skill to maximize speed.

IMPORTANT: This skill only GENERATES the Slack message — do NOT attempt to post or send it anywhere. Just output the final message text directly in the conversation for the user to copy and paste manually.

IMPORTANT: Before generating the message, check if the GitHub PR for the current branch is in Draft mode. If it is, use `gh pr ready` to mark it as Ready for Review first, then proceed with generating the message.

IMPORTANT: Before generating the message, ensure a ClickUp comment exists for the card linked to the current branch. Extract the card ID from the branch name (e.g. `868fwym2r` from `feat/868fwym2r-…`), then fetch the card's comments via the ClickUp MCP. If **no comment from me** exists yet on the card, invoke the `/comment-on-cu` skill first to leave one — this is the common-forgetting case the workflow protects against. If at least one comment from me already exists, **do NOT call `/comment-on-cu`** (skip silently — the user can run it manually if a delta update is needed). Only after this check, proceed to generate the Slack message.

---

## Voice & humanization (the most important rule)

**Write as the actual author of the PR talking to teammates on Slack.** Always in first person. Always as a human. The message should read like something a real developer typed casually, not like an AI writing a summary.

### First person — non-negotiable
- Use `I`, `me`, `my`, `I've`, `I'm`. Not "this PR does X" — `I did X` or `I'm refining X`.
- Never write in third person ("This PR introduces..."), passive voice ("The logic has been updated..."), or impersonal ("Changes include..."). The author is a person, not a process.

### Sound like a human teammate
Real people on Slack:
- Share the *why* or the *thinking* behind the change, not just the what (one sentence is enough — "after the demo the processors asked for X" is better than a dry "refactors Y").
- Use natural contractions (`I'm`, `don't`, `it's`, `we're`, `there's`).
- Occasionally admit trade-offs or context ("small scope", "follow-up coming", "quick one").
- Don't gush. No "Super excited to share…", "Amazing update!", "Huge win!". A friendly cheer greeting is fine (`Hey team!`, `Morning!`), over-the-top enthusiasm is not.
- Don't market. Skip corporate verbs like `leverage`, `streamline`, `empower`, `robust`, `comprehensive`, `seamless`, `thrilled to announce`.

### Message structure (opener)
- **Always start with a short cheer greeting** followed by a blank line before the main text. Prefer a warm wave: `Hey team! 👋`, `Morning team! 👋`, `Folks! 👋`. Other friendly alternatives: `Hey team! 🎯`, `Morning! 🚀`, `Folks! ⚡` — but `👋` should be the default when no specific emoji fits the change.
- The cheer line is standalone — never continue the same line into the explanation. Blank line right after.

### Message structure (closing)
- **End with a warm, human closing**, not a transactional one. `Review whenever, thanks!` is acceptable but usually too dry — prefer something that acknowledges the reviewer's time.
- Good closings (pick based on tone fit):
  - `Appreciate any eyes on it when you have a moment — thanks a bunch! 🙏`
  - `Whenever you get a breather, a review would be super helpful — thanks! 🙏`
  - `Happy to walk through anything unclear, thanks for the look! 🙏`
  - `Grateful for a set of eyes whenever you have a sec 🙏`
- Avoid stiff / robotic CTAs like `Please review at your earliest convenience` or `Kindly review when possible`.
- Still avoid over-the-top gushing (`Thanks sooo much!!`, `You're amazing!`) — warmth ≠ flattery.

### Anti-patterns (AI tells — avoid)
- Emoji stacking on every sentence or at the end of every bullet
- Over-explaining obvious things
- Marketing adjectives ("clean implementation", "elegant solution")
- "This refactor/change/update …" as sentence opener (reads robotic — use `I did…` / `I'm…` instead)
- Listing what was *not* changed just for completeness (only mention if genuinely reassuring)
- Ending with two separate thank-yous/sign-offs

### Lightweight test before sending
Re-read the draft and ask: *"Would I actually type this on Slack on a Tuesday afternoon?"* If it sounds like a press release or a demo script, rewrite.

---

## Message guidelines

- Write in English.
- Explain clearly what the change does and — even more important — *why* it exists (the motivation).
- Add a bit of context or detail the reader would need to understand the change without opening the PR.
- **Frame the message around the engineering problem this PR fixes and what the code does to fix it.** Do NOT mention review-process meta — e.g. "I addressed Gemini review feedback", "shipped the review fixes", "resolved N inline comments", "follow-up on the X PR after Gemini caught...". Even when this is the *second* Slack message on the same PR after additional commits, write it as a fresh problem-then-fix pitch. The audience cares about the engineering substance, not the review iteration or reviewer identity (Gemini bot, Claude bot, etc.).
- Use backticks (`` ` ``) to highlight important fields, file names, technical keywords.
- End with a warm closing that asks for review without sounding transactional — see "Message structure (closing)" above for examples.
- Max $ARGUMENTS words (default: 200 if no argument provided). Shorter is usually better.
- Emojis: use sparingly and only positive, upbeat ones (✅, 🎯, 🚀, 🧩, 🔧, 🤖, 🙏, 💡, 🎉, ⚡, 🛠️). Usually 1–3 emojis total in the whole message is enough (one in the cheer, optionally one at the sign-off).
- NEVER use emojis that convey negativity, awkwardness, frustration, or problems — like 😅, 😬, 😩, 😭, 😰, 🤦, 😓, 💀, 🥲.
- Separate each context in a different paragraph (short paragraphs, Slack-friendly).
- Use bullets to explain the concrete changes when there are multiple.
- Add the PR link (prefix `PR:`).
- Add the ClickUp card link on the next line (prefix `Card:`).
- If you find multiple repos using the same context, ask the user if they prefer to separate in multiple messages or a single message.
- Slack bold uses `*single asterisks*`, **not** `**double**`. Same goes for other structures.
- If the PR is in Draft mode, run `gh pr ready` first.

---

## Example — good vs bad

❌ **Bad (sounds AI-generated):**
> Hey team! 🎯 Super excited to share this refinement on the `R9` workflow that drafts outreach emails after a Conditional Approval. 🧩 This PR introduces two key prompt-level changes that enhance the borrower experience. 🚀
>
> • The agent no longer proactively flags large deposits.
> • LOE requests are now in question format.
>
> This was implemented following strict TDD with comprehensive eval coverage. ✅ Would love your review when you have a chance! 🙏🎉

Why it's bad: cheer runs into the same line as the pitch, "Super excited", third-person ("This PR introduces"), marketing words ("enhance", "comprehensive"), emoji stacking, double sign-off.

✅ **Good (sounds human):**
> Hey team! 👋
>
> Quick one on `R9` — after the demo the processors pointed out the `borrower` email was doing two things they wanted to change, so I shipped the prompt tweak.
>
> • I stopped flagging large deposits upfront (they'll be handled reactively once the statement is in).
> • I changed `LOE` requests to a plain-language question instead of "write a letter".
>
> Branch 1 of 4 on this card — `LO`, `Title`, and `HOI` follow-ups next.
>
> PR: https://github.com/…
> Card: https://app.clickup.com/…
>
> Appreciate any eyes on it when you have a moment — thanks a bunch! 🙏

Why it's good:
- Cheer on its own line with a friendly `👋`, blank line separating it from the pitch.
- Explains *why* in the same breath as *what* ("after the demo the processors pointed out…").
- First person throughout (`I stopped`, `I changed`, `I shipped`).
- Parenthetical side-notes sound conversational ("they'll be handled reactively once the statement is in").
- One emoji in the cheer, one at the sign-off — nothing in between.
- Warm closing that acknowledges the reviewer's time without being gushy or robotic.

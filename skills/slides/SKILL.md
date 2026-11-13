---
name: slides
description: "Generate a polished, self-contained HTML slide deck in the HouseNumbers visual identity (dark petrol + HN green accent). Two modes: (1) Git mode — presents the current branch's changes vs the base branch using git diff/log; (2) Plan mode — builds slides from a plan, outline, or topic given in the conversation. Trigger on 'slides', 'presentation', 'slide deck', 'present changes', 'apresentação'. Output is always a single self-contained HTML file with no external dependencies."
argument-hint: "[topic or leave empty for git mode]"
---

# Slides — HouseNumbers HTML Deck

Generate a self-contained HTML slide deck styled with the HouseNumbers identity.

## Determine the mode

| Signal | Mode |
|--------|------|
| User mentions branch, PR, diff, changes, commits | **Git mode** |
| User provides a plan, outline, topic, or bullet points | **Plan mode** |
| Ambiguous | Ask the user which mode they want |

**Git mode**: gather `git merge-base HEAD main`, `git diff --stat`, `git diff`, `git log --oneline` for the branch; group the diff into **logical changes** (not per-file) and build one slide per change (what changed, why it matters, key snippets, non-obvious decisions).

**Plan mode**: map each major point of the plan/topic to one or more slides. Ask one clarifying question if the plan is vague.

## Slide structure

1. **Title slide** — eyebrow label, serif headline with one italic accent phrase, 1–2 sentence lead.
2. **Overview slide** — agenda or file-change summary; use the `flowlist` pattern for sequential content.
3. **Content slides** — one concept per slide: eyebrow (`STAGE 01 · NAME` style when sequential), serif `h2` with italic accent, list or code block. Max ~15 lines of code per snippet (truncate with `// ...`).
4. **Summary slide** — key takeaways.

If the content is a **sequential flow** (stages, steps, timeline), add the **pipeline rail**: a fixed footer with one node per stage; the current slide's stage lights up in green (`here`), earlier stages are marked `done`. Tag each `<section>` with `data-stage="N"` (0 = no stage highlighted). For non-sequential content, keep only the `N / total` counter.

## Visual identity (mandatory — do not restyle)

Single self-contained HTML file. Inline CSS/JS only, no external dependencies, no webfont links.

### Design tokens

```css
:root {
  /* HouseNumbers tokens on dark petrol — green accent (accent-500 family) */
  --bg: hsl(191 100% 9%);           /* deep petrol, darker step of primary #003844 */
  --surface: hsl(191 70% 13%);
  --petrol: #003844;                /* primary / n900 */
  --border: hsl(192 28% 25%);       /* n800 */
  --fg: hsl(26 23% 92%);            /* warm cream */
  --muted: hsl(187 12% 61%);        /* n500 */
  --faint: hsl(187 15% 42%);
  --accent: hsl(158 58% 50%);       /* HN green — accent-500 (#36c993) */
  --accent-dim: hsl(160 45% 28%);
  --accent-soft: hsl(148 82% 79%);  /* accent-300 */
  --teal: hsl(177 100% 27%);        /* Accent900 #006c67 */
  --green: hsl(148 82% 79%);        /* diff add — accent-300 */
  --red: hsl(11 87% 62%);           /* at-risk */
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  --sans: "Avenir Next", "Segoe UI", system-ui, sans-serif;
  --mono: "SF Mono", "Fira Code", "JetBrains Mono", "Cascadia Code", Menlo, monospace;
}
```

**Never introduce orange, purple, or blue accents.** The only accent family is the HN green; semantic red is reserved for removals/errors.

### Typography roles

- **Display** (`h1`/`h2`): `--serif`, weight 500, `text-wrap: balance`, tight line-height; one key phrase per heading wrapped in `<em>` colored `var(--accent)`.
- **Eyebrows / stage labels / counters**: `--mono`, uppercase, `letter-spacing: .14em–.22em`, colored `var(--accent)` (dim parts in `var(--faint)`).
- **Body / lists**: `--sans`, `line-height ~1.6`, `max-width` ~62–66ch, color `var(--muted)` with `strong` in `var(--fg)`.

### Component patterns

- **Background texture**: faint dotted grid — `radial-gradient(rgba(239,233,226,.05) 1px, transparent 1px)`, `background-size: 26px 26px`.
- **Lists**: no bullets; `—` marker in `var(--accent-dim)`; hairline separators `rgba(239,233,226,.08)` between items.
- **Code blocks** (`pre`): `var(--surface)` background, `var(--border)` border, radius 8px, soft shadow; additions in `var(--green)`, removals in `var(--red)` with line-through, comments in `var(--faint)`.
- **Checkpoint/callout cards**: border `var(--accent-dim)`, background `rgba(54,201,147,.07)`, mono `GATE ✓`-style mark in `var(--accent)`.
- **Pipeline rail** (sequential decks): fixed footer, nodes 10px round; active node filled `var(--accent)` with glow `0 0 0 4px rgba(54,201,147,.18), 0 0 14px rgba(54,201,147,.5)`; done nodes `var(--accent-dim)`.

### Behavior

- Keyboard navigation: `←` / `→` (and Space / click advance).
- Progress indicator `N / total` in mono, bottom-right.
- Slide transitions: fade; content children enter with a staggered rise animation (`translateY(14px)`, delays of ~70ms per child).
- Respect `prefers-reduced-motion: reduce` — disable all animation.
- Responsive: `clamp()` on headings, grid columns collapse under 950px, `overflow-x: auto` on wide code blocks.

## Output

1. Save as `slides.html` in a temp directory (`mktemp -d` or the session scratchpad).
2. Send the file to the user (render inline when supported) with a brief summary: slide count and key topics.
3. Remind the user to open it in a browser for keyboard navigation.

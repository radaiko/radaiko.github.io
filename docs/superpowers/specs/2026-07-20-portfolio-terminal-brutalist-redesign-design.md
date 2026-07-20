# Portfolio v2 — "Terminal Brutalist" redesign

Date: 2026-07-20
Repo: `radaiko.github.io` (single self-contained `index.html`, deployed by GitHub Pages)

## Goal

Bold restatement of the personal portfolio's visual identity while preserving the
existing content and the live GitHub-activity data pipeline. New identity:
**technical / brutalist-precision** — Swiss grid, mono-forward labels, high contrast,
sharp edges, one loud accent — shipped in **both light and dark themes**. The hero
gains an **interactive mini-terminal** as its centerpiece.

## Locked decisions

| Axis | Decision |
|------|----------|
| Ambition | Bold restatement (new signature color + type system) |
| Mood | Technical / brutalist-precision (Linear-docs × terminal × Swiss grid) |
| Color | Dual light + dark with toggle, single **electric-blue** accent |
| Hero | Functional command-palette / mini-terminal |
| Terminal scope | Full interactive: real typing input + command history + clickable chips |
| Display font | **Space Grotesk** (display/headings) + **JetBrains Mono** (all UI/mono) |
| Status section | Keep as its own live-telemetry section; wire the terminal `status` command to it |

## Non-negotiable constraints

- **Self-contained**: everything inline in `index.html` — no build step, no bundler.
  Google Fonts is the only external request (already used today).
- **Keep the data pipeline**: `data/activity.json` (+ `scripts/fetch-activity.py` and the
  update workflow) stay as-is. The page still loads static data first, then falls back to
  the public GitHub API.
- **Preserve prior fixes**: active-projects list sorts by **date** (not commits); the
  Projects section shows exactly **SnackPilot** and **Fleetarr**.
- **Accessibility & resilience**: works with keyboard, honours `prefers-reduced-motion`,
  and degrades gracefully when JS is unavailable.

## Color tokens

Applied via `:root` + `:root[data-theme="dark"]`. Default theme follows
`prefers-color-scheme`; the nav toggle writes an explicit choice to `localStorage`.

**Dark**
```
--bg        #0b0c0e   --surface   #111316   --elevated  #16181c
--text      #f4f5f6   --muted     #8a9099   --rule      #22252a
--accent    #2b6fff   --accent-weak #2b6fff26
```
**Light**
```
--bg        #ffffff   --surface   #f6f7f8   --elevated  #ffffff
--text      #0a0b0d   --muted     #5a6169   --rule      #e4e6e9
--accent    #1f5fe6   --accent-weak #1f5fe614
```

Retired: floating glow orb, SVG noise overlay, gradient avatar border, rounded 16px cards.
Kept + crisper: the hairline grid background (subtle, theme-aware).

## Typography

- Display / headings / body: **Space Grotesk** (300–700).
- Labels / nav / section markers / meta / terminal: **JetBrains Mono**.
- Big, tight display sizes with negative letter-spacing; monospace UPPERCASE micro-labels
  with positive tracking. High contrast between the two roles is the core brutalist move.

## Layout

- Max content width ~1140px, generous but structured vertical rhythm.
- Section headers render as a mono marker + full-width hairline rule, e.g.
  `01 // WORK ───────────────────────────`.
- Cards and panels are bordered rectangles (1px `--rule`, ~4–6px radius), hover =
  accent border + faint `--accent-weak` fill.

## Sections

1. **Nav** — mono logo `radaiko ~/dev`, section links, GitHub link, **theme toggle** (sun/moon).
2. **Hero** — left: mono kicker + oversized headline + one-line intro + primary actions
   (View GitHub / Contact). Right: the interactive terminal panel.
3. **`01 // WORK`** — SnackPilot + Fleetarr as bold brutalist cards (big index number `01`/`02`,
   language tag, description, footer meta, whole card links to the repo). Icons reused from the
   repos.
4. **`02 // STATUS`** — live telemetry: "Active projects (last 12 weeks)" **sorted by date** +
   commit-activity bars, restyled brutalist. Fed by `data/activity.json`.
5. **`03 // STACK`** — tech tags grouped under mono category labels:
   - **Languages**: Rust · Swift · Kotlin · C# · TypeScript · Python · Dart
   - **Frameworks / UI**: SwiftUI · Jetpack Compose · .NET · Tauri · React Native · Flutter · WPF · ASP.NET
   - **Tooling**: UniFFI · Docker · Git · CI/CD · gRPC
6. **`04 // DOCS`** — auto-discovered GitHub Pages sites (unchanged data, restyled).
7. **Footer** — copyright + links.

## Hero terminal — behaviour spec

A real `<input>` prompt inside a hairline-framed panel with a live output log.

**Boot**: on load, type-animate `whoami`, print the identity line, then a hint:
`type \`help\` or click a command below`. Under `prefers-reduced-motion`, print instantly.

**Input**: Enter runs the line; ↑/↓ walk command history; blinking cursor; the panel body
auto-scrolls to the newest output. A row of clickable command **chips** sits below the input
for discovery and mobile use.

**Commands**
| Command | Behaviour |
|---------|-----------|
| `help` | List available commands |
| `whoami` | Identity line (name · role · location) |
| `projects` / `projects --active` | List SnackPilot + Fleetarr (tag, one-liner, `open` hint) |
| `stack` | Print the grouped tech stack |
| `status` | Print live totals from activity data + scroll to / flash the Status section |
| `open <name>` | Open a repo in a new tab. Names: `snackpilot`, `fleetarr`, `graft`, `github`, `docs`. Bare `open` → GitHub profile |
| `contact` | Print + trigger the `mailto:` |
| `theme [light\|dark]` | Toggle, or set explicitly |
| `clear` | Clear the terminal log |
| unknown / `sudo` | Playful `command not found` / `permission denied` → suggest `help` |

**Accessibility / resilience**: input has an associated label; the output log is an
`aria-live="polite"` region; visible focus ring; full keyboard operation. The panel ships
with meaningful static default content so a no-JS visitor still sees the identity + key links.

## Content refresh

- **`<title>`**: `radaiko — Software Developer`
- **`<meta name="description">`**: "radaiko — software developer building native iOS & Android
  apps and cross-platform developer tools with Rust, Swift, and .NET."
- **Hero kicker**: `// software developer · Upper Austria`
- **Hero headline** (default): "Native apps &\ndeveloper tools." (accent on the second line)
- **Hero intro**: "I build native iOS & Android apps and cross-platform developer tools —
  mostly in Rust, Swift, and the .NET ecosystem."
- Hero meta chips: location + a repositories count (kept).

Copy is a starting point; exact wording is easy to tweak after seeing it rendered.

## Motion

Restrained and precise: terminal typing, cursor blink, hairline/section draw-in on scroll
(short, snappy transforms + opacity), ~120ms hover transitions. All motion gated behind
`prefers-reduced-motion: reduce`.

## Acceptance criteria

- [ ] Renders correctly in **both** light and dark; toggle persists across reloads; defaults to OS.
- [ ] Terminal: typing, Enter, history, chips, and every command above work; boot animation runs
      (and is skipped under reduced-motion); no-JS fallback shows identity + links.
- [ ] Active-projects list is **date-sorted**; Projects/Work shows only SnackPilot + Fleetarr.
- [ ] Activity data still loads from `data/activity.json` with public-API fallback.
- [ ] Responsive: clean single-column layout on mobile; terminal usable on touch via chips.
- [ ] No dead CSS carried over; page remains a single self-contained `index.html`.
- [ ] No console errors (favicon 404 excepted).

## Out of scope

- Changing the data pipeline / `fetch-activity.py` logic (beyond the already-applied date sort).
- Adding a real backend, analytics, or new external dependencies.
- Multi-page structure.

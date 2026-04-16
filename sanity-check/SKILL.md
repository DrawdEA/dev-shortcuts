---
name: sanity-check
description: Checks whether an npm package, library, or code pattern is current, maintained, and recommended. Use this skill whenever the user mentions a specific npm package, library, framework, or pattern (e.g. "should I use X", "is X still good", "using X for Y", "/sanity-check X"). Also auto-trigger when the user pastes code that imports or requires a library you're unfamiliar with, or when discussing tech stack choices. Also triggers on "/sanity-check --scan" or "scan my dependencies" to audit an entire package.json. Don't wait to be asked — if a package or pattern comes up and its currency is relevant, run this check proactively.
---

# /sanity-check

Two modes:
1. **Single package** — `/sanity-check <package>` — live check on one package
2. **Full scan** — `/sanity-check --scan` — audit entire package.json for vibe/agentic compatibility

---

## Mode 1: Single package check

### Trigger conditions

- Explicit: user types `/sanity-check <package>`
- Auto: user mentions a package/library/pattern where its health matters
- Auto: user pastes code with unfamiliar imports
- Auto: user asks "should I use X for Y" or "is X still good"

### Data sources (in order)

1. **npm registry** — `https://registry.npmjs.org/<package-name>` (latest version, publish date, deprecated field)
2. **GitHub repo** — releases/tags page and README for maintenance signals
3. **Bundlephobia** — `https://bundlephobia.com/package/<n>` if bundle size is relevant
4. **Training knowledge** — known dead/deprecated patterns, ecosystem shifts
5. **Startup/builder community vibe** — X/Twitter, Reddit (r/reactjs, r/expo, r/javascript, r/startups), Hacker News. Search `"<package> site:reddit.com OR site:news.ycombinator.com"` and `"<package> 2026 opinion"`.

Use `web_search` and `web_fetch`. Search pattern: `"<package> deprecated OR alternative OR 2026"`.

### Single package output format

```
## Sanity check: <package-name>

**Verdict: ✅ Current** | **⚠️ Caution** | **❌ Dead/Avoid**

One-line reason.

---

### Details
- **Latest version**: x.x.x (released N months ago)
- **npm weekly downloads**: ~Xm
- **Actively maintained**: Yes / No / Unclear (last commit: ...)
- **Deprecated flag**: None / "Use X instead"
- **Known issues**: [any breaking changes, migration notes]

### Ecosystem signal
[1-2 sentences on community sentiment, trends, alternatives if relevant]

### Vibe check 🌡️
**Builder/startup community opinion**: [Bullish / Neutral / Bearish / Divided]
[2-3 sentences: what are devs/founders saying on X, Reddit, HN? Hot takes, trends, is it the "cool" pick or "boring enterprise" pick?]

### Recommendation
[Concrete: keep using it / migrate to X / fine for Y but not Z]
```

---

## Mode 2: Full dependency scan (`/sanity-check --scan`)

Audits every package in the nearest `package.json` through the lens of **vibe coding / agentic engineering compatibility** — i.e. how well each package works when Claude (or another LLM) is writing the code.

### What "vibe/agentic compatible" means

A package is LLM-friendly if:
- **Well-typed** — bundled TypeScript types mean Claude can infer correct API shape
- **Actively maintained** — recent publishes mean Claude's training data is less likely stale
- **Well-documented** — rich README/docs give LLMs better context to generate correct usage
- **Stable API** — not multiple majors ahead of what's installed (Claude may generate newer API syntax)
- **Not deprecated** — obvious

### How to run

Find the nearest `package.json` in the current project, then run:

```bash
python {SKILL_DIR}/scripts/scan_deps.py path/to/package.json
```

The script fetches live npm registry data for every dep and returns structured JSON. Parse the JSON and generate a terminal summary.

### Scan output format

Print a terminal summary — one line per package, grouped by risk level:

```
🔍 Dependency scan: <project-name> (<N> packages)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ HIGH RISK (fix these)
  moment          v2.29  →  stale 36mo, deprecated, no types
  node-sass       v4.x   →  deprecated, use sass

⚠️  CAUTION
  axios           v1.x   →  2 major versions behind latest
  redux           v4.x   →  active but often overkill for vibe coding

✅ VIBE-FRIENDLY
  zod             v3.x   →  typed, active, LLM-friendly API
  react-query     v5.x   →  current, excellent docs
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary: X healthy · Y caution · Z high risk
🤖 Agentic compatibility score: N/10

Top recommendations:
1. [most impactful fix]
2. [second fix]
3. [third fix]
```

### Scoring rubric (per package)

| Signal | Weight |
|---|---|
| Deprecated flag | ❌ immediate high risk |
| No TypeScript types (bundled or @types) | ⚠️ caution |
| Last publish > 12 months | ⚠️ caution |
| Last publish > 24 months | ❌ high risk |
| Major version 2+ behind latest | ⚠️ caution |
| Sparse README (<500 chars) | ⚠️ caution |
| Active + typed + rich docs | ✅ vibe-friendly |

---

## Dead patterns reference (verify if old)

| Pattern | Status | Replacement |
|---|---|---|
| `moment` | ❌ Dead (self-deprecated) | `date-fns`, `dayjs`, `Temporal API` |
| `enzyme` | ❌ Dead (React 17+ broken) | `@testing-library/react` |
| `request` (npm) | ❌ Dead (deprecated 2020) | `axios`, `ky`, `fetch` |
| `node-sass` | ❌ Dead | `sass` (Dart Sass) |
| `tslint` | ❌ Dead | `eslint` + `typescript-eslint` |
| `react-scripts` (CRA) | ⚠️ Zombie | `vite`, `Next.js` |
| `redux` alone | ⚠️ Often overkill | `zustand`, `jotai`, RTK if needed |
| `styled-components` v5 | ⚠️ Check v6 compat | `v6` or `tailwind` |
| `expo-av` | ⚠️ Splitting | `expo-audio`, `expo-video` |
| `@react-navigation/native` v5 | ⚠️ Old | v6/v7 |

## Edge cases

- **Monorepo packages** (`@tanstack/react-query`): check root package on npm
- **Expo-specific packages**: check `https://docs.expo.dev` — npm data alone isn't enough for SDK version gating
- **Native modules in RN**: check New Architecture compatibility list
- **Unknown package**: if npm 404s, say so and search — might be a typo or GitHub-only
- **Multiple packages**: `/sanity-check axios zod react-query` → stacked verdict blocks
- **Patterns not packages**: skip npm steps, go straight to web_search + training knowledge

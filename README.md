# dev-shortcuts

A collection of Claude Code skills for agentic engineers. Install once, use on every project.

Built for developers who vibe code with Claude and need guardrails before they ship.

---

## Skills

### `/sanity-check`
Checks if an npm package or pattern is still worth using. Takes into account the opinions of the community. A smarter linter, essentially.

- Hits the npm registry and GitHub live — not training data
- Checks version, maintenance status, deprecation flags, weekly downloads
- Searches Reddit, X, and HN for community sentiment (vibe check)
- Full dep scan mode: scores your entire `package.json` for AI coding compatibility

```
/sanity-check axios                               ← is this package still worth using?
/sanity-check moment                              ← deprecated? better alternatives?
/sanity-check "next.js current implementation"   ← patterns and approaches, not just packages
/sanity-check --scan                              ← audit entire package.json
/sanity-check axios zod react-query               ← multiple at once
```

---

### `/stack-check`
Reviews architectural decisions for soundness. Useful when in doubt if what you're using is the best right now, depending on your use case. Very useful when you're learning as you go.

Evaluates on four axes:
- **Fit** — right tool for the job?
- **Coherence** — do the pieces work together?
- **Longevity** — still a good bet in 12-18 months?
- **Vibe/AI coding compatibility** — how well does Claude generate correct code for this tool?

Covers RN/Expo mobile, Next.js/web, AI/LLM tooling, and backend/infra. Always makes a concrete call.

```
/stack-check
/stack-check should I use Supabase or Convex for a real-time app?
```

---

### `/ship-check`
Pre-release codebase audit. Use when you're lazy to check after "generally" finishing your app. Runs in this order:

1. **📋 CLAUDE.md** — reads your project's CLAUDE.md for known blockers and unresolved TODOs
2. **🔍 Static analysis** — scans for secrets, console.logs, hardcoded values, localhost refs, ts-ignore abuse
3. **🏗️ Build check** — runs tsc, lint, expo export or next build, and tests (only if steps 1-2 are clean)

`--fix` mode loops until clean:
- Removes console.logs and debugger statements
- Generates `.env.example` with values redacted
- Applies known RN/Next.js pattern fixes with your confirmation

```
/ship-check             ← full audit
/ship-check --quick     ← critical issues only, skips build
/ship-check --fix       ← audit + auto-fix loop
```

---

## Install

**Prerequisites:** [Claude Code](https://code.claude.com) (Pro, Max, Team, or Enterprise), Node.js, Python 3.x

### Option 1 — npx (recommended)

```bash
npx github:DrawdEA/dev-shortcuts
```

Works on Mac, Linux, and Windows. No git clone needed.

### Option 2 — git clone

```bash
git clone https://github.com/DrawdEA/dev-shortcuts.git
cd dev-shortcuts
node bin/install.js
```

Good if you want to inspect or modify the skills before installing.

### Verify

Open Claude Code in any project and run `/context`. You should see all three skills listed under Skills.

---

## File structure

```
dev-shortcuts/
├── README.md
├── sanity-check/
│   ├── SKILL.md
│   └── scripts/
│       └── scan_deps.py       ← hits npm registry, scores deps for AI compatibility
├── stack-check/
│   └── SKILL.md
└── ship-check/
    ├── SKILL.md
    └── scripts/
        ├── audit.py           ← static analysis, returns structured JSON
        ├── fixer.py           ← auto-fixes safe issues
        └── build_check.py     ← runs tsc, lint, build, tests
```

---

## Contributing

PRs welcome. If you're adding a skill:
- Follow the `SKILL.md` format (YAML frontmatter + markdown body)
- Make the description specific — vague descriptions undertrigger
- Test on at least one real project before submitting
- Add install instructions to this README

---

## License

MIT

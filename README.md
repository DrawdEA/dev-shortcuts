# dev-shortcuts

A collection of Claude Code skills for JS/TS developers. Install once, use on every project.

Built for developers who vibe code with Claude and need guardrails before they ship.

---

## Skills

### `/sanity-check`
Checks if an npm package or pattern is still worth using.

- Hits the npm registry and GitHub live — not training data
- Checks version, maintenance status, deprecation flags, weekly downloads
- Searches Reddit, X, and HN for community sentiment (vibe check)
- Full dep scan mode: scores your entire `package.json` for AI coding compatibility

```
/sanity-check axios
/sanity-check moment
/sanity-check --scan                      ← audit entire package.json
/sanity-check axios zod react-query       ← multiple at once
```

---

### `/stack-check`
Reviews architectural decisions for soundness.

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
Pre-release codebase audit. Runs in this order:

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

### Prerequisites
- [Claude Code](https://code.claude.com) — Pro, Max, Team, or Enterprise
- Python 3.x
- Node.js + npm

### Mac/Linux
```bash
git clone https://github.com/DrawdEA/dev-shortcuts.git

mkdir -p ~/.claude/skills/sanity-check/scripts
mkdir -p ~/.claude/skills/stack-check
mkdir -p ~/.claude/skills/ship-check/scripts

cp dev-shortcuts/sanity-check/SKILL.md ~/.claude/skills/sanity-check/SKILL.md
cp dev-shortcuts/sanity-check/scripts/scan_deps.py ~/.claude/skills/sanity-check/scripts/scan_deps.py

cp dev-shortcuts/stack-check/SKILL.md ~/.claude/skills/stack-check/SKILL.md

cp dev-shortcuts/ship-check/SKILL.md ~/.claude/skills/ship-check/SKILL.md
cp dev-shortcuts/ship-check/scripts/audit.py ~/.claude/skills/ship-check/scripts/audit.py
cp dev-shortcuts/ship-check/scripts/fixer.py ~/.claude/skills/ship-check/scripts/fixer.py
cp dev-shortcuts/ship-check/scripts/build_check.py ~/.claude/skills/ship-check/scripts/build_check.py
```

### Windows (PowerShell)
```powershell
git clone https://github.com/DrawdEA/dev-shortcuts.git

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills\sanity-check\scripts"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills\stack-check"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills\ship-check\scripts"

Copy-Item "dev-shortcuts\sanity-check\SKILL.md" "$env:USERPROFILE\.claude\skills\sanity-check\SKILL.md"
Copy-Item "dev-shortcuts\sanity-check\scripts\scan_deps.py" "$env:USERPROFILE\.claude\skills\sanity-check\scripts\scan_deps.py"

Copy-Item "dev-shortcuts\stack-check\SKILL.md" "$env:USERPROFILE\.claude\skills\stack-check\SKILL.md"

Copy-Item "dev-shortcuts\ship-check\SKILL.md" "$env:USERPROFILE\.claude\skills\ship-check\SKILL.md"
Copy-Item "dev-shortcuts\ship-check\scripts\audit.py" "$env:USERPROFILE\.claude\skills\ship-check\scripts\audit.py"
Copy-Item "dev-shortcuts\ship-check\scripts\fixer.py" "$env:USERPROFILE\.claude\skills\ship-check\scripts\fixer.py"
Copy-Item "dev-shortcuts\ship-check\scripts\build_check.py" "$env:USERPROFILE\.claude\skills\ship-check\scripts\build_check.py"
```

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

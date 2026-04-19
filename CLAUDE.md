# dev-shortcuts

Claude Code skills package. Installs via `npx github:DrawdEA/dev-shortcuts` or `node bin/install.js`.

## What this is

Three Claude Code skills for pre-ship guardrails:
- `/sanity-check` — npm package/pattern health check (hits live npm + GitHub + community sentiment)
- `/stack-check` — architecture review across fit, coherence, longevity, AI coding compat
- `/ship-check` — pre-release audit: secrets, console.logs, build check, auto-fix loop

Skills live in `~/.claude/skills/` after install. Claude Code picks them up automatically.

## Project structure

```
bin/install.js          ← copies skill files to ~/.claude/skills/
sanity-check/SKILL.md   ← skill definition + trigger instructions
sanity-check/scripts/   ← scan_deps.py
stack-check/SKILL.md
ship-check/SKILL.md
ship-check/scripts/     ← audit.py, fixer.py, build_check.py
```

## Install flow

`bin/install.js` checks for Python 3, then copies the files listed in `files[]` to `~/.claude/skills/`. No npm deps required at runtime.

## Adding a skill

1. Create `<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`, `triggers`)
2. Add any scripts under `<skill-name>/scripts/`
3. Add the files to the `files` array in `bin/install.js`
4. Add the dir to `files` in `package.json`
5. Document in README

## Requirements

- Node.js >=14
- Python 3.x (for sanity-check and ship-check scripts)
- Claude Code (Pro, Max, Team, or Enterprise)

---
name: ship-check
description: Pre-release codebase audit that checks if a project is safe to ship, and can auto-fix mechanical issues in a loop until clean. Use when the user says "ready to ship", "about to release", "submitting to App Store", "deploying to prod", "is this prod-ready", or "/ship-check". Auto-trigger when the user mentions submitting, releasing, or deploying anything. Covers JS/TS projects including Expo/RN mobile apps, Next.js web apps, and general Node.js projects. Runs real checks against actual files — not just advice.
---

# /ship-check

Pre-release audit for JS/TS projects. Checks CLAUDE.md and scans your files first, then runs the build pipeline last — no point waiting on a slow build if there are obvious issues to fix first.

Two modes:
- **`/ship-check`** — full audit of current project
- **`/ship-check --quick`** — critical issues only (secrets, crashes, broken builds)
- **`/ship-check --fix`** — audit + auto-fix safe issues in a loop until clean or max 3 iterations

---

## What it checks

### 🔴 Critical (block the release)
- Hardcoded secrets, API keys, tokens in source files
- `console.log` / `console.error` / `print` statements left in production code
- TODO/FIXME/HACK comments in code that ships
- Calls to localhost or `127.0.0.1` in non-test code
- Disabled TypeScript (`@ts-ignore`, `@ts-nocheck`, `as any` abuse)
- Missing `.env.example` when `.env` exists but is gitignored
- Exposed `.env` files committed to git

### 🟡 Warnings (fix before ship, not blockers)
- `debugger` statements
- Commented-out code blocks (>3 lines)
- Missing error handling on async/await (naked `await` without try/catch)
- Unhandled promise rejections (`.then()` without `.catch()`)
- `Math.random()` used for anything security-related
- Direct `eval()` usage
- Outdated deps with known issues (cross-ref with sanity-check if available)

### 🔵 Info (worth knowing)
- Bundle size estimate if detectable
- Test coverage signal (are there any tests at all?)
- README present and non-empty?
- License file present?
- CHANGELOG or release notes?

### Platform-specific checks

**Expo/RN:**
- `app.json` / `app.config.js` has valid `version` and `buildNumber`/`versionCode`
- No `__DEV__`-gated code that should be removed
- EAS config present if using EAS Build
- `expo-constants` not exposing secrets via `extra` field
- No `flipper` or dev-only packages in production dependencies
- Check `android/` and `ios/` for hardcoded debug flags if ejected

**Next.js:**
- `NEXT_PUBLIC_` env vars don't accidentally expose secrets
- No API routes missing auth checks (basic pattern match)
- `next.config.js` not disabling security headers
- No `console.log` in Server Components or API routes
- Build output: run `next build` check if possible

---

## Execution order

Run in this sequence — stop early if critical issues found at any step:

1. **📋 CLAUDE.md check** — read project CLAUDE.md, extract blockers and TODOs
2. **🔍 Static analysis** — run `audit.py`, scan for secrets, console.logs, etc.
3. **🏗️ Build check** — only runs if steps 1 and 2 have no critical issues. Slow, so save it for last.

If step 1 or 2 finds critical issues → report them, ask if user wants to fix before running build. Build takes time — no point running it against broken code.

---

## How to run

### Step 3: Build check (runs last, only if no critical issues)

```bash
python {SKILL_DIR}/scripts/build_check.py <project-root>
```

This runs in order:
1. `npx tsc --noEmit` — TypeScript errors
2. `npm run lint` — if lint script exists
3. `npx expo export` (Expo) or `npm run build` (Next.js) — bundler errors
4. `npm run test` — if test script exists and is not a placeholder

**If build check fails on a critical command (tsc, build), give a 🛑 DO NOT SHIP verdict.**

Build errors surface in the output as:
```
🏗️ BUILD CHECK
  ❌ TypeScript — 3 errors
     src/lib/api.ts:45 — Type string is not assignable to type number
  ✅ Lint — passed
  ❌ Expo export — failed
     Bundle failed to compile. See error above.
```


Find the project root (look for `package.json`), then:

```bash
python {SKILL_DIR}/scripts/audit.py <project-root>
```

The script scans files and returns structured JSON. Parse it and generate the terminal report.

If the script can't run (no Python, permission issue), fall back to running bash greps directly:

```bash
# Secrets pattern
grep -rn "sk-\|api_key\|apikey\|secret\|password\|token" --include="*.ts" --include="*.tsx" --include="*.js" --exclude-dir=node_modules --exclude-dir=.git <project-root>

# Console logs
grep -rn "console\.\(log\|error\|warn\|debug\)" --include="*.ts" --include="*.tsx" --include="*.js" --exclude-dir=node_modules --exclude-dir=.git <project-root>

# TODOs
grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.ts" --include="*.tsx" --include="*.js" --exclude-dir=node_modules --exclude-dir=.git <project-root>

# Localhost
grep -rn "localhost\|127\.0\.0\.1" --include="*.ts" --include="*.tsx" --include="*.js" --exclude-dir=node_modules --exclude-dir=.git <project-root>
```

---

## Output format

```
🚢 Ship check: <project-name>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 CLAUDE.md CHECK
  🔴 Unresolved: "TODO: add rate limiting before launch"
  🟡 Manual check: "auth flow has known edge case on logout"

🔴 CRITICAL — fix before shipping
  ...

🟡 WARNINGS
  ...

🏗️ BUILD CHECK (ran last)
  ✅ TypeScript — no errors
  ✅ Expo export — success
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏗️ BUILD CHECK
  ✅ TypeScript — no errors
  ✅ Lint — passed
  ✅ Expo export — success
  ✅ Tests — 42 passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 CRITICAL — fix before shipping
  [file:line] hardcoded API key found: "sk-proj-..."
  [file:line] localhost reference in production code
  [file:line] .env file committed to git

🟡 WARNINGS — should fix
  [file:line] console.log (23 instances across 8 files)
  [file:line] naked await without error handling
  [file:line] TODO: finish auth logic

🔵 INFO
  Tests: ✅ present / ❌ none found
  README: ✅ present / ❌ missing
  .env.example: ✅ present / ❌ missing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
verdict: ✅ READY TO SHIP | ⚠️ SHIP WITH CAUTION | 🛑 DO NOT SHIP

X critical · Y warnings · Z info
```

If critical issues found: **do not give a ready-to-ship verdict**. Be direct.

---

## Platform detection

Auto-detect project type from `package.json`:
- Has `expo` dep → run Expo checks
- Has `next` dep → run Next.js checks
- Has both → run both
- Neither → generic JS/TS checks only

---

## False positive guidance

Some patterns look like secrets but aren't:
- `apiKey` in Firebase config (public by design, but note it anyway)
- `publishableKey` in Stripe (public, but flag and explain)
- Test fixtures with dummy values

When flagging potential secrets, show the matched line so the user can judge. Don't just say "secret found" — show them `const API_KEY = "sk-proj-abc123"` so they can confirm.

---

## After the audit

If critical issues found, offer to:
1. Fix `console.log` instances automatically (safe, mechanical)
2. Generate a `.env.example` from the existing `.env` structure with values redacted

Do not auto-fix anything involving auth, secrets handling, or logic changes — those need human review.

---

## Fix mode (`/ship-check --fix`)

Runs the audit, auto-fixes everything safe to fix mechanically, then re-runs until clean or until max 3 iterations.

### What gets auto-fixed
| Issue | Fix |
|---|---|
| `console.log/warn/debug` statements | Removed from file |
| `debugger` statements | Removed from file |
| Missing `.env.example` | Generated with values redacted, keys preserved |

### What never gets auto-fixed (needs you)
| Issue | Why |
|---|---|
| Hardcoded secrets | Moving a secret is not the same as removing it — needs human decision |
| Localhost references | Might be intentional (dev config, feature flags) |
| TODOs/FIXMEs | Need context to know if blocking or not |
| `@ts-ignore` / `as any` | Needs proper typing, not just deletion |
| Missing version/buildNumber | Needs intentional version bump |
| Auth issues | Never touch auth automatically |

### Execution order

Run in this sequence — stop early if critical issues found at any step:

1. **📋 CLAUDE.md check** — read project CLAUDE.md, extract blockers and TODOs
2. **🔍 Static analysis** — run `audit.py`, scan for secrets, console.logs, etc.
3. **🏗️ Build check** — only runs if steps 1 and 2 have no critical issues. Slow, so save it for last.

If step 1 or 2 finds critical issues → report them, ask if user wants to fix before running build. Build takes time — no point running it against broken code.

---

## How to run

### Step 3: Build check (runs last, only if no critical issues)

```bash
python {SKILL_DIR}/scripts/build_check.py <project-root>
```

This runs in order:
1. `npx tsc --noEmit` — TypeScript errors
2. `npm run lint` — if lint script exists
3. `npx expo export` (Expo) or `npm run build` (Next.js) — bundler errors
4. `npm run test` — if test script exists and is not a placeholder

**If build check fails on a critical command (tsc, build), give a 🛑 DO NOT SHIP verdict.**

Build errors surface in the output as:
```
🏗️ BUILD CHECK
  ❌ TypeScript — 3 errors
     src/lib/api.ts:45 — Type string is not assignable to type number
  ✅ Lint — passed
  ❌ Expo export — failed
     Bundle failed to compile. See error above.
```
 fix mode

```bash
# Step 1: run audit, save output
python {SKILL_DIR}/scripts/audit.py <project-root> > /tmp/audit.json

# Step 2: run fixer
python {SKILL_DIR}/scripts/fixer.py /tmp/audit.json <project-root>

# Step 3: re-run audit to verify
python {SKILL_DIR}/scripts/audit.py <project-root>
```

Repeat steps 1-3 up to **3 times**. Stop when:
- No critical issues remain → ✅ ready to ship
- Only unfixable issues remain → report them clearly, stop looping
- 3 iterations hit → stop, show what's left, don't keep going

### Fix mode output format

```
🔧 Ship check --fix: <project-name>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Iteration 1/3
  ✅ Removed 23 console.log statements across 8 files
  ✅ Removed 2 debugger statements
  ✅ Generated .env.example
  Re-running audit...

Iteration 2/3
  ✅ No new auto-fixable issues found

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Auto-fixed: 3 issue types
🚨 Still needs you:
  [src/lib/api.ts:12] hardcoded API key — move to .env
  [src/app/page.tsx:45] TODO: add rate limiting before launch
  [app.json] missing ios.buildNumber

verdict: ⚠️ ALMOST THERE — 3 issues need manual fix
```

### Safety rules for fix mode
- Always show a diff summary of what was changed before writing
- Never modify files in `node_modules`, `.git`, `dist`, `build`
- Never delete entire files — only remove specific lines
- If a file write fails, skip it and report it — don't crash the loop
- Keep a change log so the user can undo if something looks wrong

---

## Tier 2 fixes: Claude-applied fixes for known patterns

After `fixer.py` runs (Tier 1), Claude applies Tier 2 fixes for issues with a known correct replacement. These require reading the file, understanding context, and writing the correct code — not just deleting lines.

**Always confirm with the user before applying Tier 2 fixes.** Show what you're about to change and ask "fix these?" before writing.

### Known patterns and their fixes

#### RN/Expo

**`Alert.prompt` — iOS only, crashes on Android**
```tsx
// BEFORE
Alert.prompt('Enter name', '', (text) => setName(text))

// AFTER — cross-platform modal replacement
const [modalVisible, setModalVisible] = useState(false)
const [inputValue, setInputValue] = useState('')
// ... Modal component with TextInput
```
Show the user the full modal component, confirm, then write it.

**`tracksViewChanges={true}` on map markers**
```tsx
// BEFORE
<Marker tracksViewChanges={true} />

// AFTER
<Marker tracksViewChanges={false} />
// Note: set to true only during initial render if marker content is dynamic,
// then flip to false — keeping it true tanks map performance
```
Safe to apply directly after confirming.

**`ActivityIndicator` inside a `FlatList` without `keyExtractor`**
```tsx
// Flag missing keyExtractor — causes React key warnings in prod
// Add: keyExtractor={(item, index) => item.id ?? index.toString()}
```

**`image` without explicit `width`/`height` in RN**
```tsx
// BEFORE
<Image source={require('./img.png')} />

// AFTER
<Image source={require('./img.png')} style={{ width: 100, height: 100 }} />
// Or use resizeMode + flex if dynamic
```
Don't auto-apply — ask for intended dimensions first.

#### Next.js

**`useEffect` with missing dependency array**
```tsx
// BEFORE
useEffect(() => { fetchData() })

// AFTER
useEffect(() => { fetchData() }, []) // or [dep] if dependency exists
```
Safe to apply, but show the change first.

**API route without try/catch**
```tsx
// BEFORE
export async function GET(req) {
  const data = await db.query()
  return Response.json(data)
}

// AFTER
export async function GET(req) {
  try {
    const data = await db.query()
    return Response.json(data)
  } catch (error) {
    return Response.json({ error: 'Internal server error' }, { status: 500 })
  }
}
```
Always confirm before applying — user may have custom error handling.

**`next/image` missing `alt` prop**
```tsx
// BEFORE
<Image src="/hero.png" width={800} height={400} />

// AFTER
<Image src="/hero.png" width={800} height={400} alt="" />
// Empty alt for decorative images, descriptive for content images
// Ask which before applying
```

#### General TS/JS

**Empty catch blocks**
```tsx
// BEFORE
try { await something() } catch (e) {}

// AFTER
try { await something() } catch (error) {
  console.error('Failed:', error) // at minimum — or proper error handling
}
```
Flag and suggest, don't auto-apply.

---

## Tier 2 fix flow in `--fix` mode

```
After Tier 1 (fixer.py) completes:

1. Collect all remaining issues
2. Match each against Tier 2 known patterns
3. Group by "safe to apply" vs "needs dimensions/context"
4. Show the user a summary:

   🔧 Tier 2 fixes available (Claude-applied):
     ✅ tracksViewChanges={true} → false  (MapScreen.tsx:311, :341)
     ✅ Alert.prompt → cross-platform modal  (MapScreen.tsx:239)

   Apply these? (y/n)

5. On confirmation: read each file, apply fix, write back
6. Re-run audit.py to verify
7. Report final state
```

The goal: user types `/ship-check --fix` once and walks away. Everything that can be fixed gets fixed. What's left is a short list of genuine judgment calls.

---

## CLAUDE.md awareness

Every `/ship-check` run reads the project's `CLAUDE.md` (and any nested ones) as part of the audit. This gives the check project-specific context that static analysis can't infer.

### How to read it

```bash
# Find all CLAUDE.md files in the project
find <project-root> -name "CLAUDE.md" -not -path "*/node_modules/*" -not -path "*/.git/*"
```

Read each one and extract two things:

1. **Known issues / manual checks** — anything the developer has flagged as needing attention before shipping
2. **TODOs / pre-launch items** — explicit tasks that haven't been done yet

### What to look for in CLAUDE.md

Scan for these patterns:

```
# Ship-check relevant signals in CLAUDE.md:

- Lines containing: TODO, FIXME, before launch, before ship, before release, before deploy
- Lines containing: known issue, edge case, manual test, do not ship
- Lines containing: warning, caution, important, note
- Any section titled: "Known issues", "Before shipping", "Pre-release checklist", "TODO"
```

### Cross-referencing with code

For each item found in CLAUDE.md, check if the code actually reflects it:

| CLAUDE.md says | Check |
|---|---|
| "TODO: add rate limiting to /api/auth" | grep for rate limit implementation in that file |
| "known edge case on logout" | flag as manual test required |
| "do not ship without X" | treat as a critical blocker |
| "auth flow needs review" | surface as warning |

If the code doesn't address a documented TODO — treat it as a 🔴 critical issue if it mentions shipping/release, 🟡 warning otherwise.

### CLAUDE.md section in output

Add to the report:

```
📋 CLAUDE.md CHECK
  🔴 Unresolved pre-launch item: "TODO: add rate limiting before launch" (CLAUDE.md:12)
  🟡 Manual check required: "auth flow has known edge case on logout" (CLAUDE.md:8)
  🔵 Note: "MapScreen performance degrades with >50 markers" (CLAUDE.md:24)
```

### If no CLAUDE.md exists

Note it in the info section and suggest creating one:

```
🔵 No CLAUDE.md found — consider adding one with known issues and pre-launch checklist
   This helps /ship-check catch project-specific concerns automatically
```

### CLAUDE.md is also a signal for the verdict

If CLAUDE.md contains any explicit "do not ship", "not ready", or "blocked" statements — that is an automatic 🛑 DO NOT SHIP regardless of what static analysis says. The developer put it there for a reason.

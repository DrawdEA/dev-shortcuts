---
name: stack-check
description: Reviews architectural decisions, tech stack choices, and system design for soundness. Use this skill whenever the user asks "is this architecture good", "does this make sense", "should I use X or Y", "review my stack", "is this the right approach", or describes how they've structured a project. Auto-trigger when the user shares a system design, tech stack, or architecture decision and seems to want validation or critique. Covers RN/Expo mobile, Next.js/web, AI/LLM tooling, and backend/infra. Don't wait to be asked — if an architectural decision comes up that seems worth examining, run this proactively.
---

# /stack-check

Reviews architecture and tech stack decisions for soundness. Not just "is this the popular choice" — is it the *right* choice for what you're building and where you're going.

## Trigger conditions

- Explicit: `/stack-check` followed by a description, stack list, or diagram
- Auto: user describes how they've structured a project
- Auto: user asks "should I use X or Y for Z"
- Auto: user shares a tech stack and seems to want feedback
- Auto: user says "does this make sense" about an architectural decision

## What "sound architecture" means here

Evaluate on five axes:

1. **Fit** — does this tool/pattern actually solve the problem, or is it overkill/underkill?
2. **Coherence** — do the pieces work well together, or are there impedance mismatches?
4. **Longevity** — will this still be a reasonable choice in 12-18 months?
5. **Vibe/AI coding compatibility** — how well does this tool work when Claude (or another LLM) is writing the code?

## How to run a stack-check

1. Ask clarifying questions if the stack/decision isn't fully described — what is being built, who uses it, what's the team size, what's the timeline
2. Research any unfamiliar tools or recent ecosystem shifts via web_search before forming opinions
3. Evaluate each axis above
4. Give a verdict with concrete reasoning

## Output format

```
## Stack check: <what's being reviewed>

**Overall verdict: ✅ Sound** | **⚠️ Some concerns** | **❌ Reconsider**

One-line summary.

---

### Fit
[Is this the right tool for this specific problem? What does it do well here, what does it miss?]

### Coherence
[Do the pieces work together? Any friction points, impedance mismatches, or "this will bite you later" combos?]


### Longevity
[Is this still a reasonable bet in 12-18 months? Any ecosystem risk, deprecation risk, or momentum concerns?]

### Alternatives worth knowing
| Option | When to prefer it |
|---|---|---|
| X | [scenario] |
| Y | [scenario] |

### Verdict
[Concrete recommendation. Not "it depends" — make a call. If it's context-dependent, say which context leads to which answer.]
```

## Domain-specific heuristics

### RN/Expo mobile
- Expo managed workflow is almost always correct unless you have a specific native module need — don't prebuild early
- New Architecture is now default in SDK 55 — flag any Old Arch-only native deps
- State: zustand for most things, don't reach for Redux unless you genuinely need devtools + time travel
- Navigation: React Navigation v7 — anything older is a red flag
- If they're considering bare RN over Expo without a strong reason, push back

### Next.js/web
- App Router is the current path — Pages Router is legacy, flag it
- Don't overcomplicate data fetching — Server Components + fetch is often enough before reaching for React Query
- Supabase is a solid choice for indie/small team; flag if they're trying to use it at scale without understanding the tradeoffs
- Vercel for hosting is fine but flag vendor lock-in if it matters to them

### AI/LLM tooling
- Evaluate: is this actually agentic or just a prompted workflow? (matters for framing, not necessarily correctness)
- RAG vs structured extraction — most "knowledge base" use cases are better served by structured extraction than naive RAG
- MCP is worth learning — it's becoming the standard tool interface
- Flag if they're using LangChain for something Claude/Anthropic SDK handles natively — often unnecessary abstraction
- Vector DB: only reach for Pinecone/Weaviate if you actually need scale; pgvector handles most indie use cases

### Backend/infra
- Supabase covers 80% of indie/small team backend needs — validate before they build custom
- Don't build a microservices architecture for a product with <10k users
- Edge functions are often overkill — regular serverless is fine for most cases
- Flag premature optimization patterns (caching layers, queues, etc. before there's actual load)


## Edge cases

- **"Is my whole app architecture sound"** — ask for a brief description or diagram, then evaluate holistically
- **"X vs Y"** — always make a call, don't hedge. State your reasoning clearly
- **Unfamiliar tool** — web_search it before opining, don't hallucinate capabilities
- **Solo dev vs team** — adjust recommendations; what's right for a team of 5 is often wrong for a solo builder
- **MVP vs production** — flag explicitly when a choice is fine for MVP but needs rethinking at scale

## Vibe/AI coding compatibility heuristics

When evaluating a tool for a solo dev or small team using Claude heavily, apply these signals:

### What makes a tool AI-coding friendly
- **TypeScript-native API** — Claude generates typed code more reliably than SQL strings or stringly-typed configs
- **Colocated schema + logic** — Claude can read the whole data layer in one place; hunting across migration files increases hallucination risk
- **Small, stable API surface** — fewer ways to do the same thing = more consistent codegen
- **Rich docs + high training data coverage** — tools with extensive docs and GitHub presence generate better completions
- **No raw SQL required** — SQL is the #1 surface where LLMs generate plausible-but-wrong code (especially RLS policies)

### Known AI coding traps by tool
| Tool | AI coding risk |
|---|---|
| Supabase RLS | Claude frequently generates RLS policies that look right but have logic errors — always review manually |
| Supabase SSR (Next.js) | Client vs server client distinction is a common Claude mistake — `@supabase/ssr` vs `@supabase/supabase-js` |
| Prisma | Schema is separate from queries — Claude loses context across files in long sessions |
| Raw SQL | Highest hallucination risk — prefer query builders or TypeScript-native ORMs |
| LangChain | API surface changes frequently — Claude's training data is often stale on exact method names |

### AI-friendly alternatives
| Instead of | Consider | Why |
|---|---|---|
| Supabase (complex RLS) | Convex | TypeScript queries, no SQL, colocated schema |
| Raw SQL | Drizzle ORM | TypeScript-native, schema-first, excellent Claude compatibility |
| LangChain | Anthropic SDK directly | Smaller surface, stable API, Claude knows it well |
| Prisma | Drizzle | Faster, TypeScript-first, less migration complexity |

### The Convex signal specifically
Convex is notably AI-coding friendly:
- Queries/mutations are TypeScript functions with full type inference — no SQL strings
- Schema is defined in `convex/schema.ts`, colocated with functions — Claude reads the whole data layer at once
- Reactive queries mean less glue code for Claude to get wrong
- Official Anthropic + Convex integration exists — well-covered in training data

For solo devs vibe-coding a new project in 2026, Convex is now a legitimate default over Supabase unless you specifically need SQL control or have existing Supabase infrastructure.

## Output format (updated)

Add this section to every stack-check output:

```
### Vibe/AI coding compatibility
**Score: 🤖 High / ⚠️ Medium / 🚨 Low**
[1-2 sentences: how well does Claude generate correct code for this tool? Any known traps?]
```

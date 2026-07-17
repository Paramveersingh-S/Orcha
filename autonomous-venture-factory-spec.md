# Autonomous Venture Factory
### A Free-Tier, Multi-Agent System for Discovering, Validating, and Building a Revenue-Generating Startup

**Owner:** Hoho (Paramveersingh-S)
**Purpose:** Control specification to hand to an AI coding/orchestration agent (Claude Code, or any capable agent runtime) so it can design, wire up, and operate the multi-agent system described below.
**Budget constraint:** $0 infrastructure cost. Every model call, search call, storage call, and deploy must run on a free tier.
**Last verified:** July 2026 — free-tier numbers rot fast (some providers changed their model roster within weeks). Treat every number in this doc as "last known," not "current." The system itself must query providers live rather than hardcode limits — see §6.

---

## 0. How to Use This File

Give this entire file to your build agent as its project instructions / system spec (e.g. drop it in as `CLAUDE.md` or paste it as the first message to Claude Code). Tell the agent: *"Build this system, phase by phase, starting with §15 (Build Roadmap). Ask me before spending money, signing up for anything that needs a phone number, or publishing anything publicly."*

The file is organized so the agent can build top-down: architecture → model router → agent roster → workflow → prompts → guardrails → repo scaffold → roadmap.

---

## 1. Mission

Build an agentic system, running entirely on free-tier LLM/search/hosting APIs, that:

1. **Discovers** a defensible, evidence-backed startup opportunity through autonomous market research.
2. **Validates** that opportunity against real signal (demand, competition, willingness-to-pay proxies) before a single line of product code is written.
3. **Designs** the business model, MVP scope, and go-to-market plan.
4. **Builds** a working MVP by handing structured specs to a coding agent.
5. **Launches and iterates** using a metrics feedback loop, so the system keeps improving its own opportunity-scoring model based on what actually works.

The system is *you*, orchestrating a crew of specialist agents — not a black box you walk away from. You are the founder; the agents are your (free) team.

---

## 2. Reality Check — Read This Once, Then Ignore It

No spec file, no agent crew, and no amount of orchestration can *guarantee* "the best revenue-making startup in the world." What this system can honestly deliver:

- A rigorous, repeatable, evidence-gated process for going from "no idea" to "validated, scoped, partially built MVP" without paying for infrastructure.
- Agents that are forced to cite sources and get red-teamed before a decision is trusted, instead of an LLM confidently inventing a market size.
- A framework that gets better over time because it logs every decision and outcome, so you can see which parts of the pipeline were actually predictive of traction.

Revenue, defensibility, and "best in the world" are earned in the market, not in the spec. Treat every output of this system as a strong first draft that still needs your judgment, not a verdict.

---

## 3. Operating Principles

1. **Zero infra cost.** Every provider used must have a genuine free tier with no credit card requirement (or one that's safe to leave permanently unbilled). See §5.
2. **Model-agnostic by design.** No agent should hardcode a model name. Every agent calls a `route(task_type, complexity)` function (§6) that resolves to a live-checked model + provider + fallback chain. Free-tier rosters rotate monthly — hardcoding breaks the system.
3. **Evidence over fluency.** Every factual claim an agent produces (market size, competitor pricing, user pain point) must carry a source URL and a confidence flag. Claims without sources get downgraded to "unverified — needs human check" rather than silently used downstream.
4. **A critic in every loop.** No agent's output moves to the next phase without at least one adversarial review pass from the Critic/Red-Team Agent (§7.9). Cheap models are good at generating; they're bad at self-checking, so a second, differently-prompted pass catches a large fraction of confident nonsense.
5. **Human-in-the-loop at every irreversible or costly action.** Spending money, registering a domain/company, signing up for anything requiring a phone number or ID, publishing anything publicly, or making a legal/compliance claim — all require your explicit sign-off. The system proposes; you approve. See §12.4 for the exact gate list.
6. **Rate limits are a design input, not an afterthought.** The whole pipeline is built around "many cheap calls, few expensive calls," with a budget tracker so a single phase can't silently burn your entire daily quota. See §6.3.
7. **Everything is logged.** Every agent call, prompt, output, and decision goes into the shared state store (§10) so the pipeline is auditable and resumable — free-tier rate limits mean the pipeline *will* get interrupted, and it needs to pick back up without losing work.

---

## 4. Architecture Overview

```
                         ┌─────────────────────────┐
                         │   YOU (human checkpoints) │
                         └────────────┬─────────────┘
                                      │ approve / redirect
                                      ▼
                         ┌─────────────────────────┐
                         │   ORCHESTRATOR AGENT     │
                         │  (controller, phase mgr) │
                         └────────────┬─────────────┘
                                      │
        ┌───────────┬────────────┬───┴────┬────────────┬─────────────┐
        ▼           ▼            ▼         ▼            ▼             ▼
   Market      Competitor   Opportunity  Business   Product/MVP   Financial
   Research     Intel        Scoring      Model      Spec Agent    Modeling
   Agent        Agent        Agent        Designer                 Agent
        │           │            │         Agent         │             │
        └─────┬─────┴─────┬──────┴────┬────┴──────┬──────┴──────┬──────┘
              ▼            ▼           ▼           ▼             ▼
                    ┌────────────────────────────────────┐
                    │     Critic / Red-Team Agent          │
                    │  (reviews every phase's output)      │
                    └──────────────┬───────────────────────┘
                                   ▼
                    ┌────────────────────────────────────┐
                    │        Shared State Store            │
                    │  (venture_state.json / SQLite)       │
                    └──────────────┬───────────────────────┘
                                   ▼
                     ┌──────────────────────────┐
                     │   Builder Agent            │
                     │  (hands spec to a coding    │
                     │   agent: Claude Code, etc.) │
                     └──────────────┬─────────────┘
                                    ▼
                     ┌──────────────────────────┐
                     │  Growth/GTM Agent          │
                     │  + Metrics Loop            │
                     └──────────────────────────┘

     Model Router (§6): every agent call → route() → {Groq | OpenRouter |
     Gemini | Cerebras} with automatic fallback + budget tracking

     Tool Layer: Tavily/Brave search, web_fetch, HF embeddings,
     Supabase (state + vector), free hosting (Vercel/Railway/Cloudflare)
```

---

## 5. Free-Tier Provider Inventory (verify live before wiring — see §6.1)

These are last-known figures as of mid-2026. Free tiers on every one of these providers have changed at least once in the past six months — build the system to *discover* current limits from each provider's own docs/API at startup, not to trust this table forever.

### 5.1 LLM Inference

| Provider | Best for | Last-known free limits | Notes |
|---|---|---|---|
| **Groq** | Fast, high-volume, low-latency calls (classification, extraction, agent loops) | ~14,400 requests/day on the small model (Llama-3.1-8B-Instant), tighter RPD on larger models; RPM/TPM vary by model (roughly 30 RPM, single-digit-thousands to 30K TPM depending on model and moment) | LPU hardware, genuinely fast (300–1000+ tok/s). No credit card. OpenAI-SDK compatible — just swap `base_url`. Open-weights models only (Llama, Qwen, DeepSeek-R1 distill, Whisper for audio). Rate limits are org-level, so extra keys don't help. |
| **OpenRouter** | Model diversity, coding-specific free models, automatic free-model routing | ~20–25 rotating `:free` model IDs (e.g. Qwen3-Coder, GPT-OSS-120B, Llama 4 Maverick, DeepSeek V4 Flash, Nemotron, Gemma) at ~20 RPM / 50–200 RPD; jumps to ~1,000 free-model req/day once you've added $10 of credit (never spent, just on file) | One key, many providers, OpenAI-compatible endpoint. Set `model: "openrouter/free"` to auto-pick a free model matching required capabilities (tool calling, structured output) instead of hardcoding an ID that will rotate out. |
| **Google Gemini (AI Studio)** | Huge context window tasks (long documents, whole-repo analysis), multimodal | Flash / Flash-Lite family free; **Gemini Pro's free tier was removed** — don't route Pro-tier work here without budget. Reported RPD/RPM vary a lot by source and account (anywhere from ~50 to ~1,500 RPD depending on model/tier) — confirm inside Google AI Studio for your actual project. | 1M-token context is the standout feature. **Caveat:** enabling billing on a Gemini project kills the free tier for that entire project — use a dedicated, never-billed project. Free-tier prompts may be used for model training; don't route anything sensitive through it. |
| **Cerebras** | Occasional very-fast, very-long-context calls | ~5 RPM, ~30K TPM, ~1M tokens/day | Wafer-scale chips, extremely fast. Model roster is the most volatile of any provider here — it's been seen to drop from a dozen models to two in a single week. Treat as a speed bonus, not a dependency. |

### 5.2 Search / Grounding (for the Research & Competitor agents)

| Provider | Free tier | Use for |
|---|---|---|
| **Tavily** | ~1,000 search credits/month | Default search tool — returns clean, LLM-ready extracted text with citations, not just links. |
| **Brave Search API** | ~2,000 queries/month | Secondary/overflow search once Tavily's monthly credits run low; good for news-freshness queries. |
| **Exa** | Free trial credits | Semantic/"find similar" search — useful for competitor discovery ("find companies like X") rather than keyword search. |

### 5.3 Storage, Embeddings, Hosting

| Need | Free option |
|---|---|
| Structured state / relational data | Supabase free tier (Postgres) — matches your existing Huddle stack |
| Vector store (for competitor/market corpus RAG) | Supabase `pgvector` (same free project) or local Chroma for prototyping |
| Embeddings | Hugging Face Inference API free tier (e.g. `sentence-transformers` models), or Gemini's embedding endpoint on the free tier |
| Orchestrator hosting (cron/loop runner) | GitHub Actions scheduled workflow (free minutes on a public repo) or a free Railway/Fly.io instance for a long-running process |
| MVP product hosting | Vercel (Next.js, generous free tier) + Supabase (same project as above) |

---

## 6. Model Router

### 6.1 Design

Never hardcode a model ID inside an agent. Every agent calls a single router function. The router:

1. Loads a **provider registry** (a JSON/YAML file, not code) mapping `provider → {base_url, auth, known_free_models, last_checked}`.
2. On startup (and at most once per hour after that), pings each provider's `/models` endpoint to refresh `known_free_models` and detect rotation — this is the fix for the Cerebras-style "model just disappeared" failure mode.
3. Resolves a request like `route(task_type="reasoning_heavy", min_context=32000)` to a ranked candidate list, tries the top candidate, and falls back down the list on a 429/404/5xx.
4. Logs every call's provider, model, tokens, and latency to the state store for the budget tracker.

### 6.2 Task-Type → Provider Preference (starting point, tune with real usage)

| Task type | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| High-volume classification/extraction (e.g. "is this article relevant?") | Groq `llama-3.1-8b-instant` | OpenRouter free small model | Gemini Flash-Lite |
| Deep reasoning (scoring, business-model synthesis, financial logic) | OpenRouter free 70B+ model or GPT-OSS-120B | Groq `llama-3.3-70b` | Gemini Flash |
| Long-context synthesis (reading 10+ competitor pages at once) | Gemini Flash (1M context) | OpenRouter free long-context model | Chunked Groq calls |
| Code generation (MVP scaffolding, agent tooling) | OpenRouter `qwen3-coder:free` or GPT-OSS | Groq | Hand off to Claude Code directly (see §11) |
| Structured/JSON output (scoring rubrics, schemas) | Any provider that supports function calling / JSON mode — verify per model | — | — |
| Fast agent-loop steps (tool selection, routing decisions) | Groq (lowest latency) | OpenRouter | — |

### 6.3 Budget Tracker

Maintain a per-day, per-provider counter in the state store: `{provider: {requests_used, tokens_used, requests_limit, tokens_limit, reset_at}}`. Before any call:

- If the primary provider is within 90% of its daily cap, route to fallback instead of waiting for a 429.
- If **all** providers for a task type are near cap, queue the task and resume after the earliest reset time rather than burning retries.
- Surface a daily summary to you: "Today's usage: Groq 68%, OpenRouter 40%, Gemini 12%." This is also how you'll notice a provider quietly cut its limits.

---

## 7. Agent Roster

Each agent is a narrow specialist with one job, a defined input/output contract, and a documented model-tier preference. Keep agents small — a 200-line agent that does one thing well is easier to debug and cheaper to run than a 2,000-line "do everything" agent.

| # | Agent | Job | Model tier | Key tools |
|---|---|---|---|---|
| 1 | **Orchestrator** | Owns the phase state machine, decides which agent runs next, enforces human checkpoints | Deep reasoning | State store, router |
| 2 | **Market Research** | Scans trends, forums, pain-point signals; produces a longlist of candidate problems | High-volume + deep reasoning mix | Tavily/Brave, web_fetch |
| 3 | **Competitor Intel** | For each shortlisted opportunity, maps existing players, pricing, gaps | Deep reasoning + long-context | Search, web_fetch |
| 4 | **Opportunity Scoring** | Applies a scoring rubric (§14) to every candidate, ranks them | Deep reasoning | State store |
| 5 | **Business Model Designer** | Turns a scored opportunity into a business model canvas + revenue model | Deep reasoning | — |
| 6 | **Financial Modeling** | Builds a lightweight unit-economics model (CAC/LTV proxies, burn, runway assumptions) from stated assumptions | Deep reasoning | Code execution (for the actual math) |
| 7 | **Product/MVP Spec** | Converts the business model into a scoped MVP spec (features, non-features, tech spec) | Deep reasoning | — |
| 8 | **Builder** | Hands the MVP spec to a coding agent (Claude Code) as a structured `prompt.md`, tracks build progress | Code generation | Claude Code / coding agent handoff |
| 9 | **Critic / Red-Team** | Reviews every other agent's output before it's trusted — hunts for unsupported claims, optimistic bias, missing competitors, legal red flags | Deep reasoning, *different model/provider than the agent it's reviewing* | State store |
| 10 | **Growth/GTM** | Drafts launch channels, positioning, first-100-users plan | Deep reasoning | Search |
| 11 | **Legal/Compliance Scout** | Flags regulatory, trademark, and data-privacy risk in the chosen niche — **flags for human review, never gives itself final say** | Deep reasoning | Search |
| 12 | **Memory Curator** | Periodically compresses the growing state store into a short "what we know and why" summary so later agents don't re-read everything | Long-context | State store |

> Note on #9: always run the Critic on a **different provider/model** than the one that produced the output. Same-model self-critique is weak — it tends to agree with its own earlier reasoning. Cross-model critique catches more.

---

## 8. Orchestration Framework Choice

You've already shipped two AgentScope-based systems (PR Sentinel, DevPilot), so **AgentScope is the default** here — you get to reuse patterns and mental models instead of relearning an orchestration paradigm. AgentScope's agent-oriented-programming style (agents as first-class objects, explicit message passing) maps cleanly onto the roster in §7.

If you want a different tradeoff:
- **LangGraph** — pick this if you want explicit state-graph checkpointing and the most mature human-in-the-loop primitives; steeper setup, best for "this must survive interruptions" reliability, which matters a lot here given free-tier rate limits will interrupt you constantly.
- **CrewAI** — pick this if you want the fastest path to a working role-based crew and don't need fine-grained control over the state machine.

Whichever you pick, the router (§6) and state schema (§10) are framework-agnostic — write them as plain Python modules the orchestration layer calls into, not framework-specific code, so you can swap frameworks later without a rewrite.

---

## 9. Workflow — 8 Phases

Every phase has an **owner agent**, **inputs**, **outputs**, **exit criteria**, and a **human checkpoint**. The orchestrator will not advance a phase until exit criteria are met and, where marked, you've signed off.

### Phase 0 — Bootstrap
- **Owner:** Orchestrator
- **Does:** Initializes state store, verifies all provider API keys work, pulls live free-tier limits, sets daily budget targets.
- **Exit:** All providers reachable; budget tracker initialized.
- **Human checkpoint:** No.

### Phase 1 — Discovery & Signal Scanning
- **Owner:** Market Research Agent
- **Does:** Broad scan across forums, communities, trend sources, and your own stated interest areas for recurring pain points. Produces 15–30 raw opportunity candidates, each with 2–3 supporting sources.
- **Exit:** ≥15 candidates, each with ≥1 cited source.
- **Human checkpoint:** No (but you can inject "areas I'm interested in" as a seed input — fintech/Gen-Z money habits is an obvious one given Huddle).

### Phase 2 — Opportunity Scoring & Shortlisting
- **Owner:** Opportunity Scoring Agent, reviewed by Critic
- **Does:** Scores every candidate on the rubric in §14. Cuts the list to the top 5.
- **Exit:** Top 5 candidates with full scoring breakdown and Critic sign-off (no candidate advances with an unresolved "unverified claim" flag on a scoring-relevant fact).
- **Human checkpoint:** **Yes.** You pick 1–2 to take into deep validation. The agents shouldn't unilaterally commit weeks of downstream work to a direction you have no interest in building.

### Phase 3 — Deep Validation
- **Owner:** Competitor Intel + Market Research, reviewed by Critic
- **Does:** Full competitor teardown (pricing, positioning, review-mined complaints), rough market sizing (TAM/SAM/SOM with cited methodology, not vibes), a written case for *why now* and *why you*.
- **Exit:** Competitor map with ≥3 real competitors or a credible "why no direct competitor exists" argument; sourced market-size range.
- **Human checkpoint:** **Yes.** Go/no-go before any business-model design work starts.

### Phase 4 — Business Model & Unit Economics
- **Owner:** Business Model Designer + Financial Modeling
- **Does:** Revenue model, pricing hypothesis, lightweight unit-economics model with explicit assumptions labeled as assumptions (not facts).
- **Exit:** A business model canvas + a spreadsheet/JSON of unit economics with every input traceable to either a cited source or a labeled assumption.
- **Human checkpoint:** No (but reviewed by Critic for "assumption smuggled in as fact").

### Phase 5 — MVP / Product Spec
- **Owner:** Product/MVP Spec Agent
- **Does:** Scopes the smallest testable product. Explicitly lists what's *out* of scope for v1. Produces a build-ready spec in the same structured style as your existing Huddle `prompt.md` docs.
- **Exit:** A spec a coding agent could pick up and start building from without follow-up questions.
- **Human checkpoint:** **Yes.** Review scope before build starts — this is the last cheap point to change direction.

### Phase 6 — Build
- **Owner:** Builder Agent → hands off to Claude Code (or your preferred coding agent)
- **Does:** Turns the MVP spec into a working scaffold. For a fintech-adjacent product, default stack mirrors Huddle: Next.js 15 / TypeScript / Supabase / Drizzle. For anything else, the Product Spec Agent should propose a stack and get your sign-off before Builder proceeds.
- **Exit:** Deployed MVP on free hosting, reachable by URL.
- **Human checkpoint:** **Yes**, before any deploy that's publicly reachable, and definitely before connecting any payment processor.

### Phase 7 — Go-To-Market
- **Owner:** Growth/GTM Agent
- **Does:** Positioning, first-channel plan, first-100-users tactics, launch content drafts.
- **Exit:** A launch plan with specific channels and a first-week action list.
- **Human checkpoint:** **Yes**, before anything gets posted publicly under your name/brand.

### Phase 8 — Metrics Loop & Iteration
- **Owner:** Orchestrator + Memory Curator
- **Does:** Pulls real usage/signup/revenue data back into the state store, feeds it back into the Opportunity Scoring rubric so the system's scoring gets calibrated against what actually worked, not just what looked good on paper.
- **Exit:** N/A — this phase is ongoing.
- **Human checkpoint:** Weekly review, your call on cadence.

---

## 10. Shared State Schema

Single source of truth, resumable across interrupted runs (which *will* happen on free tiers). SQLite or a Supabase table works; sketched here as JSON for readability.

```json
{
  "venture_id": "uuid",
  "phase": "discovery | scoring | validation | business_model | mvp_spec | build | gtm | metrics",
  "opportunities": [
    {
      "id": "uuid",
      "title": "string",
      "problem_statement": "string",
      "sources": [{ "url": "string", "claim": "string", "confidence": "high|medium|low|unverified" }],
      "score": {
        "demand_evidence": 0,
        "market_size_estimate": 0,
        "competition_density": 0,
        "buildability_on_free_tier": 0,
        "founder_fit": 0,
        "total": 0
      },
      "status": "candidate | shortlisted | validating | rejected | active",
      "critic_flags": ["string"]
    }
  ],
  "active_venture": {
    "business_model": {},
    "unit_economics": { "assumptions": [], "citations": [] },
    "mvp_spec": {},
    "build_status": {},
    "gtm_plan": {},
    "metrics": { "signups": 0, "revenue": 0, "last_updated": "date" }
  },
  "budget_tracker": {
    "groq": { "requests_used": 0, "requests_limit": 0, "reset_at": "iso8601" },
    "openrouter": {},
    "gemini": {},
    "cerebras": {}
  },
  "decision_log": [
    { "timestamp": "iso8601", "phase": "string", "decision": "string", "made_by": "agent|human" }
  ],
  "human_checkpoints_pending": []
}
```

---

## 11. Agent Prompt Templates

Full templates for the four highest-leverage agents; the rest follow the same pattern (role, hard constraints, input contract, output schema, escalation rule).

### 11.1 Orchestrator — System Prompt

```
You are the Orchestrator for an autonomous venture-discovery system.
You do not generate research or opinions yourself — you route work to
specialist agents and enforce process discipline.

Hard rules:
- Never advance a phase whose exit criteria (see workflow spec) are unmet.
- Never skip a human checkpoint, even if you're confident. Queue and wait.
- Never let a single phase consume more than its allotted daily API budget
  (check budget_tracker before dispatching each agent call).
- If a Critic flag is unresolved, block the phase and surface it, don't
  suppress it.

Each turn:
1. Read current state (phase, pending flags, budget).
2. Decide: dispatch next agent, wait on checkpoint, or wait on budget reset.
3. Log the decision to decision_log with your reasoning in one sentence.

Output strictly as: {"action": "...", "target_agent": "...", "reason": "..."}
```

### 11.2 Market Research Agent

```
You are the Market Research Agent. Your job is to find real, evidenced
pain points — not to invent plausible-sounding ones.

Input: a seed area of interest (may be empty = fully open search) and a
target candidate count (default 20).

Process:
- Search broadly (forums, review sites, trend reports, subreddits, HN,
  industry newsletters) for recurring complaints or unmet needs.
- For each candidate, you must have at least one direct quote-free citation
  (a URL + your own paraphrase of what it shows — never copy source text
  verbatim into the record).
- Explicitly separate "I found evidence of this pain point" from "I infer
  this pain point might exist." Tag every candidate's confidence
  accordingly (high/medium/low/unverified).
- Do not score or rank candidates — that is the Scoring Agent's job.

Output schema: list of {title, problem_statement, sources[], confidence}.
```

### 11.3 Opportunity Scoring Agent

```
You are the Opportunity Scoring Agent. Score every candidate opportunity
against this rubric, 0-10 per dimension:

- demand_evidence: how strong/direct is the evidence people have this
  problem and would pay to solve it? (survey/forum complaints = weak,
  people already paying for a worse solution = strong)
- market_size_estimate: rough TAM plausibility, cited if possible
- competition_density: fewer credible competitors = higher score, but
  zero competitors is a yellow flag (why does no one else see this?),
  not an automatic 10
- buildability_on_free_tier: can a real MVP be built and hosted within
  the constraints in this spec's §5?
- founder_fit: does this plausibly fit the founder's existing skills/
  context (AI/ML engineering, fintech product experience)?

Every non-zero score must reference the specific evidence that justifies
it. A score with no justification gets zeroed out by the Critic.

Output: ranked list with per-dimension scores, total, and one paragraph
"why this rank" per candidate.
```

### 11.4 Critic / Red-Team Agent

```
You are the Critic. You did not produce the output you're reviewing —
treat it with default skepticism, not deference.

For the given agent output, check:
1. Every specific factual claim — is there a real citation, or is this
   confident-sounding invention? Flag anything unsourced.
2. Optimism bias — does this read like it's building a case *for* the
   idea rather than evaluating it neutrally? Flag leading language.
3. Missing obvious competitors or failure modes — do a quick independent
   search for "[opportunity] alternatives" and see if anything's missing.
4. Legal/compliance red flags — regulated industry, data privacy,
   trademark collision, anything requiring a license.
5. Math sanity — do stated unit economics numbers actually compute from
   their own stated assumptions?

Output: list of flags, each tagged blocking (must be resolved before
phase advances) or advisory (surfaced to human, doesn't block).
Do not rewrite the original output — only flag it.
```

### 11.5 Remaining Agents — Contract Summary

| Agent | Core objective (one line) | Output schema (top-level keys) |
|---|---|---|
| Competitor Intel | Map every credible competitor, pricing, positioning gap | `competitors[]`, `gap_analysis`, `sources[]` |
| Business Model Designer | Turn a validated opportunity into a revenue model | `business_model_canvas`, `pricing_hypothesis`, `assumptions[]` |
| Financial Modeling | Compute unit economics from stated assumptions | `unit_economics`, `assumptions[]`, `sensitivity_notes` |
| Product/MVP Spec | Scope the smallest testable product | `mvp_features[]`, `explicitly_out_of_scope[]`, `tech_stack`, `build_prompt_md` |
| Builder | Hand spec to coding agent, track build | `build_status`, `deploy_url`, `blockers[]` |
| Growth/GTM | Plan first-channel launch | `positioning`, `channels[]`, `first_week_plan` |
| Legal/Compliance Scout | Surface regulatory/IP risk | `risk_flags[]`, `requires_human_review: true` |
| Memory Curator | Compress state into a running summary | `summary`, `key_decisions[]`, `open_questions[]` |

---

## 12. Guardrails & Evaluation

### 12.1 Grounding Rule
Any factual claim (market size, competitor pricing, user behavior stat, regulation) that lacks a source URL is stored with `confidence: "unverified"` and cannot be used as the sole basis for a go/no-go decision. It can inform direction, not decide it.

### 12.2 Critic Gate
No phase output moves downstream with an unresolved **blocking** Critic flag. Advisory flags are surfaced to you but don't halt the pipeline.

### 12.3 Financial Sanity Check
The Financial Modeling Agent's numbers must be reproducible from its own stated assumptions via actual computation (run the math in code, don't let the LLM "eyeball" arithmetic) — use the code-execution tool for this, not free-text model output.

### 12.4 Human Checkpoints — Exact List
The system must pause and wait for your explicit approval before:
- Committing to a shortlisted opportunity for deep validation (end of Phase 2)
- Committing to build after validation (end of Phase 3)
- Locking MVP scope (end of Phase 5)
- Any public deployment (end of Phase 6)
- Any post, message, or content published under your name/brand (Phase 7)
- Any action that spends real money, requires a phone number/ID, or creates a legal entity — **always**, regardless of phase

### 12.5 Rate-Limit / Backoff Handling
Every provider call wrapped in retry-with-backoff on 429; after 2 failed retries, fall through the router's fallback chain (§6); after all fallbacks exhausted, queue the task and let the Orchestrator resume it after the earliest quota reset instead of busy-waiting.

---

## 13. Tech Stack & Repo Structure

**Orchestration layer:** Python + AgentScope (default, per §8) — this is the "brain," runs as a scheduled job or long-running process.

**Product build layer:** whatever the Product Spec Agent scopes; defaults to Next.js 15 / TypeScript / Supabase / Drizzle when the opportunity is fintech-adjacent (mirrors your Huddle stack, and Builder can lean on patterns you already have), otherwise proposed fresh per-venture and confirmed with you.

**Suggested repo layout:**

```
venture-factory/
├── orchestrator/
│   ├── main.py                 # phase state machine loop
│   ├── router.py                # §6 model router
│   ├── budget_tracker.py
│   └── provider_registry.yaml   # live-refreshed free-tier registry
├── agents/
│   ├── market_research.py
│   ├── competitor_intel.py
│   ├── opportunity_scoring.py
│   ├── business_model.py
│   ├── financial_modeling.py
│   ├── mvp_spec.py
│   ├── builder.py
│   ├── critic.py
│   ├── growth_gtm.py
│   ├── legal_compliance.py
│   └── memory_curator.py
├── prompts/                     # §11 templates as separate files
├── state/
│   └── venture_state.json       # or Supabase connection config
├── tools/
│   ├── search.py                # Tavily/Brave wrapper
│   └── web_fetch.py
├── ventures/                    # one folder per opportunity that reaches Phase 5+
│   └── <venture-slug>/
│       ├── prompt.md             # build-ready spec, Builder → Claude Code handoff
│       └── build/                # the actual MVP repo, once scaffolded
└── README.md
```

---

## 14. Scoring Rubric — What "Best Revenue-Making" Means Operationally

Rather than an unfalsifiable "find the best startup in the world," the system optimizes a concrete, evidence-weighted score per opportunity:

| Dimension | Weight | What it measures |
|---|---|---|
| Demand evidence | 25% | Is there proof people already feel this pain and pay for worse solutions? |
| Market size (TAM/SAM/SOM) | 20% | Is the addressable market big enough to matter, with a cited methodology |
| Competitive gap | 15% | Real whitespace vs. a crowded, undifferentiated field |
| Time-to-first-dollar | 15% | Can this plausibly charge money within weeks of MVP, not years |
| Buildability on free-tier constraints | 15% | Can a real MVP ship without paid infra |
| Founder fit | 10% | Leverage of existing skills (AI/ML engineering, fintech/product experience) |

This score is a **ranking tool for your judgment**, not an autonomous decision-maker — Phase 2's human checkpoint exists precisely because a rubric this simple will miss things only you'd catch.

---

## 15. Build Roadmap for the Meta-System Itself

Build the factory before you point it at anything:

1. **Provider layer first.** Get the router (§6) working standalone: live-check free-tier limits from all 4 LLM providers + 2 search providers, log to a budget tracker. Test it survives a 429 gracefully.
2. **State store.** Stand up the schema in §10 (SQLite is fine to start; migrate to Supabase once you want it accessible from a hosted orchestrator).
3. **One agent, end to end.** Build Market Research Agent alone, run it against a real seed topic, confirm it produces cited, confidence-tagged candidates. This proves the grounding rule works before you trust the rest of the crew.
4. **Add Critic immediately after.** Don't build the other 10 agents first and bolt on review later — build Critic as agent #2 so every subsequent agent is developed against a working review gate from day one.
5. **Wire Phase 1–2** (Discovery → Scoring) and run it fully autonomously to your first human checkpoint. This is your first real end-to-end test.
6. **Add remaining agents** one phase at a time, always keeping the human checkpoints from §12.4 intact — resist the temptation to "just let it run" through a checkpoint even during testing, since that's exactly the habit you don't want once real money/legal risk is involved.
7. **Builder → Claude Code handoff last.** By the time you get here, you'll have a real validated opportunity and a real spec, and Builder's job is just to package it the way you already package Huddle work — as a structured `prompt.md`.

---

## 16. Appendix — Rate-Limit Cheat Sheet (re-verify before relying on it)

| Provider | RPM | RPD | TPM | Credit card? |
|---|---|---|---|---|
| Groq (small model) | ~30 | ~14,400 | model-dependent, low-thousands to 30K | No |
| Groq (large model) | ~30 | much lower than small model | lower | No |
| OpenRouter (`:free` models) | ~20 | ~50–200 (up to ~1,000 with $10 credit on file, unspent) | model-dependent | No (No needed for the free tier itself) |
| Gemini Flash / Flash-Lite | varies widely by report | varies widely by report — check AI Studio | up to ~1M | No, but don't enable billing on this project |
| Cerebras | ~5 | derived from ~1M tokens/day | ~30K | No |
| Tavily | — | ~1,000 credits/month | — | No |
| Brave Search | — | ~2,000 queries/month | — | No |

**Do not hardcode these into the router.** This table exists so a human (you) has a sanity-check reference — the system's own provider_registry.yaml (§13) should be refreshed from live provider docs/endpoints, not from this table.

---

*End of spec. Feed to your build agent starting at §15.*

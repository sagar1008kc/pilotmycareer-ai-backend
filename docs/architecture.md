# Architecture

## Goal

Add a separate Python FastAPI backend that serves as the AI runtime for Pilot My Career.
The existing Next.js app keeps full ownership of Supabase Auth, Database, and Storage. This
backend never duplicates auth, never exposes the service role key to the browser, and never
puts AI orchestration inside Next.js API routes.

## Request flow

```
Browser (Next.js)            FastAPI AI backend                Supabase
-----------------            ------------------                --------
Supabase session    ──────▶  get_current_user
(access_token)               - JWKS verify (primary)   ──────▶ /auth/v1/.well-known/jwks.json
                             - HS256 verify (fallback)
                             - extract user_id/email/role
                                       │
                                       ▼
                             LangGraph supervisor
                             - classify intent
                             - route to agent node
                                       │
                                       ▼
                             LLM provider abstraction
                             (OpenAI or mock)
                                       │
                                       ▼
                             report_service / usage log ──────▶ ai_reports / ai_usage_logs
                                       │                         (service role, when enabled)
                                       ▼
Render result       ◀──────  structured JSON
```

## Modules

- `app/core/config.py` — environment-driven settings (`pydantic-settings`).
- `app/core/security.py` — `get_current_user` dependency. Dev bypass + dual Supabase JWT
  verification (JWKS then HS256). Optional plan/entitlement enrichment.
- `app/core/logging.py` / `app/core/errors.py` — JSON logging and typed error handlers.
- `app/agents/` — LangGraph `AgentState`, supervisor, and one node per agent.
- `app/services/llm_service.py` — provider abstraction (OpenAI + mock; Grok/Gemini/Claude
  placeholders).
- `app/services/scoring_service.py` — deterministic keyword/skill extraction + match score.
- `app/services/document_parser.py` — PDF/DOCX/TXT extraction.
- `app/services/supabase_service.py` — lazy, optional service-role client.
- `app/services/report_service.py` — report + usage-log persistence (config gated).
- `app/services/safety_service.py` — wellness guardrails / crisis detection.

## LangGraph design

A single supervisor graph operates over a shared `AgentState`. The supervisor sets `intent`
(rules first using `page_context`, LLM classification as fallback), then conditional edges route
to exactly one agent node. Feature endpoints set `intent` directly to skip classification; the
`/chat` endpoint uses full classification.

```
input -> supervisor -> {resume_match | resume_optimize | linkedin |
                        wellness | rag | interview_prep} -> END
```

The resume matcher calls the deterministic `scoring_service` for the numeric score, and only
uses the LLM for explanation, recommended edits, and interview questions.

## Supabase persistence (frontend repo migration)

These tables belong to the shared Supabase project and should be added as a migration in the
**frontend** repo (`pilotmy-career/supabase/migrations/`), mirroring the existing RLS patterns
in `20260502120000_career_platform_tables.sql`:

```sql
create table if not exists public.ai_reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  agent text not null,
  title text,
  content jsonb not null default '{}'::jsonb,
  model text,
  provider text,
  created_at timestamptz not null default now()
);

create table if not exists public.ai_usage_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  request_id text,
  agent text not null,
  model text,
  provider text,
  prompt_tokens integer not null default 0,
  completion_tokens integer not null default 0,
  total_tokens integer not null default 0,
  latency_ms integer not null default 0,
  status text not null default 'ok',
  created_at timestamptz not null default now()
);

alter table public.ai_reports enable row level security;
alter table public.ai_usage_logs enable row level security;

create policy ai_reports_select_own on public.ai_reports
  for select using (auth.uid() = user_id);
create policy ai_usage_logs_select_own on public.ai_usage_logs
  for select using (auth.uid() = user_id);
```

The backend inserts via the service role (which bypasses RLS), while user-facing reads
(`GET /reports/history`) run with the user's own token so RLS applies.

## Security notes

- Service role key is backend-only; never returned in responses or logged.
- CORS is restricted to `FRONTEND_ORIGIN`.
- Usage logs store token counts and metadata, not raw resume/JD text.
- Wellness output is supportive/educational only and surfaces crisis resources when needed.

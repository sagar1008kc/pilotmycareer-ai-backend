# Pilot My Career AI Backend

Production-ready Python **FastAPI + LangGraph** backend that powers the AI workflows for the
Pilot My Career platform. It is a standalone **AI runtime only** — it does not own auth UI or
sessions. The existing Next.js app keeps its Supabase Auth/Database/Storage integration
untouched; this service simply validates the Supabase access token the frontend already holds,
runs multi-agent AI workflows, and returns structured JSON.

## Architecture

```
User
  -> Next.js Dashboard (existing Supabase Auth)
  -> Next.js sends Supabase access_token (Authorization: Bearer)
  -> FastAPI validates token (JWKS first, HS256 fallback)
  -> FastAPI runs LangGraph workflow
  -> FastAPI optionally reads/writes the same Supabase project (service role, backend-only)
  -> FastAPI returns structured JSON
  -> Next.js renders the result
```

The service role key lives only in this backend's environment and is never exposed to the
browser. It is used only for backend operations such as report writes, usage logs, and storage
reads.

## AI Agents

1. Resume + JD Matcher
2. Resume Optimizer
3. LinkedIn Optimizer
4. Mental Fitness Support (supportive/educational only, never diagnosis)
5. AI Resource / RAG
6. Interview Prep

A LangGraph supervisor classifies intent and routes each request to the correct agent.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in keys; set AUTH_MODE=dev for local testing
uvicorn app.main:app --reload --port 8000
```

Then visit:

- Health: http://localhost:8000/api/v1/health
- Docs:   http://localhost:8000/docs

Run tests:

```bash
pytest -q
```

Run with Docker:

```bash
docker compose up --build
```

## Auth modes

- `AUTH_MODE=dev` — returns a fixed mock user; no token required. Use for local development.
- `AUTH_MODE=supabase` — validates the `Authorization: Bearer <token>` header against the
  Supabase project. Tries asymmetric JWKS verification first, then falls back to the legacy
  HS256 shared secret (`SUPABASE_JWT_SECRET`).

## LLM provider

`LLM_PROVIDER=openai` uses OpenAI. If `OPENAI_API_KEY` is empty, the backend automatically
falls back to a deterministic **mock provider** so the API works end-to-end with no key and no
cost. Placeholders exist for Grok / Gemini / Claude.

## API

See [docs/api-examples.md](docs/api-examples.md) for request/response examples and
[docs/architecture.md](docs/architecture.md) for design details.

| Method | Path                       | Purpose                                  |
| ------ | -------------------------- | ---------------------------------------- |
| GET    | `/api/v1/health`           | Liveness / config probe                  |
| POST   | `/api/v1/chat`             | General chat; routes to the right agent  |
| POST   | `/api/v1/resume/match`     | Resume + JD matcher                       |
| POST   | `/api/v1/resume/optimize`  | Resume optimizer                          |
| POST   | `/api/v1/linkedin/optimize`| LinkedIn optimizer                        |
| POST   | `/api/v1/wellness/checkin` | Mental fitness support                    |
| POST   | `/api/v1/rag/query`        | Resource / interview prep RAG             |
| GET    | `/api/v1/reports/history`  | User AI report history (Supabase)         |
| POST   | `/api/v1/reports/generate` | Generate a downloadable report           |

## Persistence

AI reports and usage logs are persisted to the shared Supabase project only when
`SUPABASE_PERSIST=true` and the service role is configured. The required tables
(`ai_reports`, `ai_usage_logs`) are defined as a migration in the frontend repo's
`supabase/migrations/` (see [docs/architecture.md](docs/architecture.md)).

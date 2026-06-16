# API examples

All authed endpoints require `Authorization: Bearer <supabase_access_token>`.
With `AUTH_MODE=dev` the header is optional and a mock user is used.

Base URL: `http://localhost:8000/api/v1`

## Health

```bash
curl http://localhost:8000/api/v1/health
```

```json
{ "status": "ok", "app": "Pilot My Career AI Backend", "env": "local", "version": "0.1.0" }
```

## Resume match

```bash
curl -X POST http://localhost:8000/api/v1/resume/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resume_text": "...", "job_description": "..."}'
```

```json
{
  "score": 72,
  "matched_skills": ["python", "fastapi", "redis"],
  "missing_skills": ["kafka", "terraform", "graphql"],
  "recommended_edits": ["Add measurable impact for caching work", "..."],
  "interview_questions": ["Describe a time you scaled an async service.", "..."],
  "explanation": "Strong backend alignment; gaps in streaming and IaC.",
  "request_id": "...",
  "provider": "mock",
  "model": "mock-1",
  "latency_ms": 12,
  "usage": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 }
}
```

## Resume optimize

```bash
curl -X POST http://localhost:8000/api/v1/resume/optimize \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"resume_text": "...", "job_title": "Staff Backend Engineer"}'
```

## LinkedIn optimize

```bash
curl -X POST http://localhost:8000/api/v1/linkedin/optimize \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"profile_text": "...", "target_role": "Staff Backend Engineer"}'
```

## Wellness checkin

```bash
curl -X POST http://localhost:8000/api/v1/wellness/checkin \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "I feel stressed about a possible layoff."}'
```

## RAG query

```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query": "How do I answer behavioral questions?", "mode": "interview_prep"}'
```

## Chat (auto-routed)

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "Match my resume to this job", "page_context": "resume_match"}'
```

## Reports

```bash
curl http://localhost:8000/api/v1/reports/history \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"agent": "resume_match", "title": "My match report", "content": {}}'
```

## Next.js integration snippet

```ts
// In a Next.js route handler or server action
import { createSupabaseServerClient } from "@/lib/supabase/server";

const supabase = await createSupabaseServerClient();
const { data: { session } } = await supabase.auth.getSession();

const res = await fetch(`${process.env.AI_BACKEND_URL}/api/v1/resume/match`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session?.access_token}`,
  },
  body: JSON.stringify({ resume_text, job_description }),
});
const result = await res.json();
```

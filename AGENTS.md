# BankMate — Project Context for AI Agent

> **IMPORTANT:** Read this entire file before executing any task. This is the single source of truth for the project. Always follow these conventions.

---

## 1. What we are building

**BankMate** is an internal, private, on-premise AI assistant for bank branch staff. It works like Google NotebookLM but fully self-hosted — staff ask questions in Uzbek or Russian and get accurate answers with citations, based ONLY on internal bank documents (credit guidelines, AML/KYC procedures, product manuals, Central Bank regulations).

**Core principle:** This is a closed RAG (Retrieval-Augmented Generation) system. The AI must NEVER invent answers. If the answer is not in the documents, it must say so.

**Target:** Branch specialists at a bank with 52 branches, ~2,600 users. But for now we build the MVP locally.

---

## 2. Development phase & environment

- **Current phase:** MVP (local development only)
- **Environment:** Local machine with Docker Compose (NO cloud, NO Kubernetes yet)
- **Data:** Synthetic/test documents only (NO real bank data during MVP)
- **Languages of the app UI & answers:** Uzbek (primary) + Russian
- **Code, comments, variable names:** English

---

## 3. Technology stack (DO NOT substitute without asking)

### Frontend
- Next.js 14+ (App Router, NOT Pages Router)
- TypeScript (strict mode)
- TailwindCSS + shadcn/ui
- Zustand (state management)
- TanStack Query (React Query) for server state

### Backend
- Python 3.11+
- FastAPI (async)
- SQLAlchemy 2.0 (async syntax, NOT legacy)
- Alembic (migrations)
- Pydantic v2 (validation)
- Celery + Redis (background jobs)

### AI / RAG
- Multi-LLM failover (Anthropic, OpenAI, Qwen) with `claude-sonnet-4-5` as primary
- OpenAI text-embedding-3-large (3072 dimensions) — embeddings
- LangChain 0.3+ — RAG orchestration
- LlamaParse — PDF parsing (with PyPDF2 fallback)

### Data layer
- PostgreSQL 15+ — relational data
- Qdrant — vector database
- Redis 7+ — cache & job queue
- MinIO — S3-compatible file storage

### DevOps (MVP)
- Docker + Docker Compose ONLY
- No Kubernetes, no cloud services during MVP

---

## 4. Repository structure

This is a monorepo with two main apps:

```
bankmate/
├── AGENTS.md                  # this file
├── docker-compose.yml         # all services
├── docker-compose.dev.yml     # dev overrides
├── .env.example               # template (NEVER commit real .env)
├── .gitignore
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/v1/             # endpoints: auth, chat, documents, admin
│   │   ├── core/              # config, security, database
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # business logic (rag/, auth/, documents/)
│   │   ├── utils/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── frontend/
    ├── app/                   # Next.js App Router
    ├── components/            # ui/, chat/, auth/, layout/
    ├── lib/                   # api.ts, auth.ts, utils.ts
    ├── hooks/
    ├── store/                 # Zustand
    ├── types/
    ├── package.json
    └── Dockerfile
```

---

## 5. Database schema (7 core tables)

| Table | Key columns |
|-------|-------------|
| `users` | id, username, email, password_hash, full_name, role, branch_id, is_active, created_at |
| `branches` | id, name, code, region, created_at |
| `documents` | id, title, category, file_path, status, version, uploaded_by, created_at, indexed_at |
| `conversations` | id, user_id, title, created_at, updated_at |
| `messages` | id, conversation_id, role, content, sources_json, feedback, created_at |
| `audit_logs` | id, user_id, action, resource_type, resource_id, ip_address, user_agent, metadata, created_at |
| `document_chunks` | id, document_id, chunk_index, content, metadata, page_number, vector_id |

**Roles enum:** USER, BRANCH_MANAGER, CONTENT_MANAGER, AUDITOR, ADMIN

---

## 6. RAG pipeline (the heart of the system)

**Ingestion flow:**
1. Upload document → MinIO
2. Parse (LlamaParse / PyPDF2) → extract text + tables
3. Chunk (800-1200 tokens, 200 overlap, recursive splitter)
4. Embed each chunk (OpenAI text-embedding-3-large)
5. Index to Qdrant (collection: `bankmate_documents`, COSINE distance, 3072 dim)
6. Save chunk metadata to PostgreSQL

**Query flow:**
1. Embed user question
2. Hybrid search: vector (Qdrant) + keyword (PostgreSQL full-text)
3. Retrieve top-20
4. Re-rank → top-5
5. Build context (max 8000 tokens)
6. Send to Claude with system prompt (Uzbek)
7. Stream response with citations

**System prompt rule:** AI answers ONLY from provided documents. Temperature 0.1. Always cite sources (document + page).

---

## 7. Coding conventions

- **Async everywhere** in backend (FastAPI async routes, async SQLAlchemy, async HTTP clients)
- **Type hints** mandatory in Python; **strict TypeScript** in frontend
- **No hardcoded secrets** — everything from environment variables
- **Error handling** — never let exceptions crash silently; log them
- **Pydantic schemas** for every API request/response
- **One responsibility per file** — keep files focused and small
- Write **docstrings** for services and complex functions
- Frontend: **functional components + hooks only**, no class components

---

## 8. Security rules (CRITICAL — even in MVP)

- `.env` files MUST be in `.gitignore` — NEVER commit API keys
- Passwords hashed with bcrypt (rounds=12)
- JWT for auth (access 30min, refresh 7 days)
- All SQL via parameterized queries / ORM (no string concatenation)
- Input validation on every endpoint
- Audit log for all important actions

---

## 9. How the agent should work

1. **Read this file first**, every session.
2. **Work one task at a time.** Complete it fully before moving on.
3. **After completing a step, STOP and report** what was done, how to test it, and wait for my confirmation before the next step.
4. **If something is ambiguous, ASK** — do not guess on architecture decisions.
5. **Test as you go** — provide the exact command to verify each step works.
6. **Explain trade-offs** when you make a non-obvious choice.
7. Never install a different library/framework than specified above without asking.
8. Keep secrets out of code. Always use `.env`.

---

## 10. Definition of "done" for any task

- Code runs without errors
- I can verify it with a clear command you provide
- No secrets committed
- Follows the conventions above
- You told me what to check and what the next step is

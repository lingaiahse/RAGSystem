
# Enterprise HR Policy RAG — Implemented Skeleton

This repository provides a complete, production-oriented skeleton for an Enterprise HR Policy Retrieval-Augmented Generation (RAG) system. The implementation focuses on strict separation of concerns, production hardening, RBAC-aware retrieval, deterministic citation handling, and streaming responses for real-time UX.

Summary of what is implemented
- Backend (FastAPI, Python): ingestion, vector-store abstraction, RAG orchestration, and a streaming SSE endpoint that emits citation metadata followed by answer chunks.
	- Core files: [backend/app/main.py](backend/app/main.py), [backend/app/config.py](backend/app/config.py), [backend/app/auth.py](backend/app/auth.py), [backend/app/ingest.py](backend/app/ingest.py), [backend/app/services/rag_service.py](backend/app/services/rag_service.py), [backend/app/services/vector_store.py](backend/app/services/vector_store.py), [backend/app/api/routers/stream.py](backend/app/api/routers/stream.py)
	- Docker: [backend/Dockerfile](backend/Dockerfile)
	- Dependency manifest: [backend/requirements.txt](backend/requirements.txt)

- Frontend (Next.js + TypeScript): streaming client hook and chat message UI with clickable citation chips.
	- Core files: [frontend/app/page.tsx](frontend/app/page.tsx), [frontend/hooks/useRagStream.tsx](frontend/hooks/useRagStream.tsx), [frontend/components/ChatMessage.tsx](frontend/components/ChatMessage.tsx)
	- Docker: [frontend/Dockerfile](frontend/Dockerfile)
	- Manifest: [frontend/package.json](frontend/package.json)

- Dev & orchestration
	- Compose: [docker-compose.yml](docker-compose.yml)

Design highlights
- Separation of concerns: config, auth, ingestion, vector storage, RAG orchestration, and presentation are separated into dedicated modules.
- Metadata-filtered retrieval: every retrieval is filtered by user context (department, location, role_level) before generation.
- Deterministic citations: the system prompt instructs Gemini-generated answers to include citations in a deterministic format; the backend also returns citation metadata as the first SSE event.
- Streaming: backend streams citation metadata first, then token/segment-level answer chunks via SSE; frontend consumes the stream incrementally.
- Security & hardening included: Pydantic settings validation, structured logging, CORS, JWT gate on API endpoint, and a vector-store abstraction that can be replaced with pgvector or Pinecone.

How to configure
1. Backend: copy `backend/.env.example` to `backend/.env` and set:
	 - `GEMINI_API_KEY` (required)
	 - `JWT_PUBLIC_KEY` and `JWT_ALGORITHM` (for JWT auth)
	 - `DATABASE_URL` if you plan to use a persistent vector store (pgvector)
2. Frontend: copy `frontend/.env.example` to `frontend/.env` if overriding the API URL.

Run locally with Docker Compose
1. Build & run:

```powershell
docker-compose up --build
```

2. Or run services individually for development:

Backend (venv):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend (dev):
```powershell
cd frontend
npm install
npm run dev
```

Using the system
- The frontend posts to the streaming endpoint at `POST /api/rag/stream` (the frontend hook uses `NEXT_PUBLIC_API_URL`).
- API requires a `Authorization: Bearer <token>` header where the JWT contains `department`, `employment_status`, `location`, and `role_level` claims. The backend uses these claims to filter retrieved chunks.
- The SSE stream emits three event types:
	- `citation`: initial JSON array of retrieved chunk metadata
	- `message`: one or more incremental answer chunks (JSON payload `{text: string}`)
	- `done`: stream completion

Security, compliance, and production notes
- Do not commit secrets. Use Azure Key Vault or your preferred secret manager for `GEMINI_API_KEY` and JWT keys.
- Replace or extend `backend/app/services/vector_store.py` with a production-backed provider (pgvector or Pinecone). The repository includes a factory (`VectorStoreFactory.create`) to add providers.
- Validate JWT `iss` and `aud` according to your identity provider and enforce scopes/claims for fine-grained RBAC.
- Enable network-level protections, monitoring and alerting when deploying to Azure. Use managed DBs (Azure Database for PostgreSQL) with the `pgvector` extension for persistence.

Recommended next steps (I can implement any of these):
- Add a `PgVectorStore` implementation using async SQLAlchemy + `pgvector` and migration scripts.
- Implement true streaming calls to Gemini (token-level or chunked streaming) and wire SSE to proxy those streams.
- Add unit/integration tests around ingestion, retrieval filtering, and SSE parsing.
- Add server-side role-based checks (e.g., deny queries for contractors or terminated employees) and audit logging.

If you want me to proceed with any of the recommended next steps, tell me which one and I will implement it.


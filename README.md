# ResolveAI — AI Customer Support Copilot

**Tagline:** Turn Customer Support Tickets into Resolved Problems with AI.

ResolveAI is an AI-powered customer support automation platform that helps businesses classify tickets, retrieve knowledge with hybrid RAG, generate grounded responses, and keep humans in control via approval workflows.

Built with:
- **Backend:** Python 3.12 · FastAPI · SQLAlchemy · LangGraph · LangChain · Qdrant
- **Frontend:** React + Vite + Tailwind CSS
- **Database:** PostgreSQL
- **Vector DB:** Qdrant

## Project Status
- **Owner:** Taha Farooq
- **Start Date:** 4 November 2026
- **Current Phase:** Foundation and core ticket operations

## Quick Start (Local Development)

```bash
# 1. Clone / enter project
cd resolveai

# 2. Backend setup
cd backend
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Environment
cp .env.example .env
# Edit .env with your keys

# 4. Start infrastructure
docker compose up -d               # Postgres + Qdrant

# 5. Run migrations (after models are ready)
alembic upgrade head

# 6. Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
resolveai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # Auth, Documents, Tickets, AI, Approvals, Analytics
│   │   ├── core/                 # Config, Security, Database, Dependencies
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic
│   │   ├── ai/                   # LangGraph workflow, nodes, prompts
│   │   └── main.py
│   ├── alembic/
│   └── tests/
├── frontend/                     # React + Vite + Tailwind
├── docs/                         # Architecture, Evaluation Report, API docs
└── docker-compose.yml
```

## Implemented foundation capabilities

- Tenant-scoped authentication and organization membership
- Ticket creation, detail views, lifecycle updates, assignment, bulk updates, internal messages, filtering, searching, sorting, and pagination
- Multi-format knowledge ingestion including PDF, DOCX, TXT, CSV, Markdown, and HTML
- Configurable RAG chunking and Qdrant/keyword retrieval fallback
- Structured Pydantic validation for AI classification and quality-assurance outputs
- React production build and responsive ticket search/filter UI

## Development Roadmap

1. **Phase 1 — Foundation** ← You are here
2. Phase 2 — Knowledge Base + RAG
3. Phase 3 — AI Engine (Classification + LangGraph)
4. Phase 4 — Human-in-the-Loop Approval
5. Phase 5 — Analytics + Evaluation
6. Phase 6 — Deployment
7. Phase 7 — Public Launch

## License
Private / Proprietary (for now)

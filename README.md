# Recursive Fractal Wealth Engine

> A 100% autonomous, multi-agent AI "Forest" of high-growth trading seeds and a stable tokenized-asset Vault. Built for infinite vertical growth, user-authorized horizontal expansion, adversarial security, institutional-grade risk architecture, and generational wealth transfer.

## Phase 1: Shared Root & Waterfall Logic

### What's Implemented
- **15/20/50/15 Profit Waterfall** — Atomic distribution across Reservoir, Nursery, Vault, and Reinvestment
- **Tiered Vault (Liquidity Ladder)** — Tier 2 ETFs fill before Tier 3 Real Estate
- **Heartbeat System** — 90/150/180-day inactivity escalation with Legacy Protocol trigger
- **PostgreSQL + JSONB** — Full schema with NUMERIC(20,8) for all monetary columns
- **Alembic Migrations** — Version-controlled database schema
- **Comprehensive Test Suite** — 24 tests covering waterfall, vault, and heartbeat logic

### Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend API | Python FastAPI |
| Database | PostgreSQL 16 + JSONB |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Testing | pytest + pytest-asyncio |
| Frontend | Next.js (scaffold) |

### Quick Start

```bash
# Start PostgreSQL
docker-compose up db -d

# Set up Python environment
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload

# Run tests (no PostgreSQL needed — uses SQLite in-memory)
pytest tests/ -v
```

### Project Structure
```
fractal-wealth-engine/
├── backend/
│   ├── alembic/                  # Migration infrastructure
│   │   ├── versions/
│   │   │   └── 001_initial_schema.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── api/v1/               # REST endpoints
│   │   ├── models/               # SQLAlchemy ORM
│   │   ├── schemas/              # Pydantic validation
│   │   ├── services/             # Core business logic
│   │   ├── config.py             # Settings management
│   │   ├── database.py           # Async engine + session
│   │   └── main.py               # FastAPI entry point
│   ├── tests/                    # Full test suite
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                     # Next.js (Phase 4)
├── docker-compose.yml
└── .env.example
```

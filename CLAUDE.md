# CLAUDE.md — Development Guide

## Project Overview

**ThreadGraph** — AI-powered fashion garment classification and inspiration web app.
Designers upload garment photos → Claude Vision classifies them → searchable, filterable image library with designer annotations.

**Stack**: React + TypeScript + Tailwind | FastAPI + Python | PostgreSQL | Claude 3.5 Sonnet (vision) | Docker Compose

---

## Repository Structure

```
threadgraph/
├── app/
│   ├── backend/                 # FastAPI application
│   │   ├── api/                 # Route handlers (routers)
│   │   │   ├── images.py        # Upload, list, filter, search
│   │   │   ├── annotations.py   # CRUD annotations
│   │   │   ├── filters.py       # Dynamic filter values
│   │   │   └── health.py        # Health check
│   │   ├── models/              # Data models
│   │   │   ├── database.py      # SQLAlchemy models + engine
│   │   │   └── schemas.py       # Pydantic request/response schemas
│   │   ├── services/            # Business logic
│   │   │   ├── classifier.py    # Claude Vision integration
│   │   │   └── search.py        # FTS query builder
│   │   ├── core/                # Config, dependencies
│   │   │   ├── config.py        # Settings via pydantic-settings
│   │   │   └── dependencies.py  # DB session, shared deps
│   │   ├── main.py              # FastAPI app entry
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/                # React application
│       ├── src/
│       │   ├── api/             # API client (fetch wrapper)
│       │   ├── components/      # Reusable UI components
│       │   ├── hooks/           # React Query hooks
│       │   ├── pages/           # Route-level page components
│       │   ├── types/           # TypeScript interfaces
│       │   ├── App.tsx
│       │   └── main.tsx
│       ├── package.json
│       ├── tsconfig.json
│       ├── tailwind.config.js
│       ├── vite.config.ts
│       └── Dockerfile
├── eval/                        # Model evaluation
│   ├── run_eval.py              # CLI eval script
│   ├── ground_truth.csv         # Manual labels (50 images)
│   ├── test_images/             # Test image files
│   └── results/                 # Generated reports (gitignored except summary)
├── tests/                       # Test suite
│   ├── unit/                    # Parser, schema tests
│   ├── integration/             # API + DB filter tests
│   ├── e2e/                     # Full workflow tests
│   └── conftest.py              # Shared fixtures
├── docker-compose.yml
├── .env.example
├── CLAUDE.md                    # This file
└── README.md
```

**Rules**:
- Application code → `app/`
- Evaluation code/data → `eval/`
- All tests → `tests/` (not alongside source)
- No business logic in route handlers — delegate to `services/`
- No raw SQL in route handlers — use SQLAlchemy in `models/` or `services/`

---

## Python / FastAPI

### Environment
- **Python 3.12**
- **Formatter**: `ruff format` (Black-compatible)
- **Linter**: `ruff check` with `select = ["E", "F", "I", "UP"]`
- **Type checker**: `pyright` basic mode (if time permits; not blocking)

### Imports
```python
# stdlib
import os
from pathlib import Path
from uuid import uuid4

# third-party
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
import anthropic

# local
from app.backend.models.database import Image
from app.backend.models.schemas import ImageResponse
from app.backend.services.classifier import classify_image
```
Order: stdlib → third-party → local. One blank line between groups. `ruff` enforces via `isort`.

### Type Hints
- **All function signatures must have type hints** — parameters and return types
- Use `str | None` not `Optional[str]` (Python 3.12)
- Use `list[str]` not `List[str]`

### Pydantic Models
```python
# Response schemas in models/schemas.py
class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    garment_type: str
    # ...

# AI output schema in services/classifier.py
class GarmentClassification(BaseModel):
    """Schema sent to Claude as tool_use definition."""
    garment_type: str = Field(..., description="...")
```
- Use `model_config = ConfigDict(from_attributes=True)` for ORM compat
- All Fields that Claude fills get descriptive `description=` (they're part of the prompt)
- Separate API schemas from AI schemas — different concerns

### FastAPI Routers
```python
# api/images.py
router = APIRouter(prefix="/api/images", tags=["images"])

@router.post("/upload", response_model=ImageResponse, status_code=201)
async def upload_image(file: UploadFile, db: Session = Depends(get_db)):
    ...
```
- One router per resource file
- Mount all routers in `main.py`
- Use `response_model` on every endpoint
- Use `status_code` explicitly (don't rely on 200 default for POST)

### Async vs Sync
- **Route handlers**: `async def` (FastAPI native)
- **Claude API calls**: `anthropic.AsyncAnthropic` — the main async operation
- **Database**: synchronous SQLAlchemy (simpler; use `run_in_executor` if blocking becomes an issue)
- **File I/O**: synchronous (negligible for single-user)

### Error Handling
```python
# services/classifier.py
class ClassificationError(Exception):
    """Raised when Claude API fails after retries."""
    pass

# api/images.py
@router.post("/upload")
async def upload_image(...):
    try:
        classification = await classify_image(file_path)
    except ClassificationError as e:
        raise HTTPException(status_code=502, detail=f"Classification failed: {e}")
```
- Custom exceptions in services — never raise `HTTPException` from services
- Convert to `HTTPException` at the API layer
- Always log errors with context before raising

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Classifying image", extra={"filename": filename})
logger.warning("Claude returned unexpected format", extra={"attempt": attempt})
logger.error("Classification failed", extra={"error": str(e)})
```
- Use `__name__` loggers
- Structured context via `extra={}` — not f-string interpolation in the message
- Levels: `info` for flow, `warning` for recoverable issues, `error` for failures

---

## React / TypeScript

### Environment
- **Node 20 LTS**
- **Package manager**: `npm`
- **Framework**: Vite + React 18
- **CSS**: Tailwind CSS v3

### Components
```tsx
// components/Gallery/ImageCard.tsx
interface ImageCardProps {
  image: ImageResponse;
  onClick: (id: string) => void;
}

export function ImageCard({ image, onClick }: ImageCardProps) {
  return ( ... );
}
```
- **Functional components only** — no class components
- **Named exports** — no `export default`
- **Props interface above component** in same file
- **One component per file** (exception: tiny helper sub-components)

### TypeScript
- `"strict": true` in tsconfig
- Interfaces for API shapes in `types/index.ts` — must match backend Pydantic schemas
- No `any` — use `unknown` + type guards if needed
- Prefer `interface` over `type` for object shapes

### File Naming
```
components/Gallery/ImageCard.tsx    # PascalCase for components
hooks/useImages.ts                 # camelCase with "use" prefix
api/client.ts                      # camelCase for utilities
types/index.ts                     # index for barrel exports
pages/GalleryPage.tsx              # PascalCase with Page suffix
```

### Tailwind
- Use utility classes directly — no `@apply` in CSS files
- Extract repeated patterns into components, not CSS classes
- Dark mode: not required for MVP
- Responsive: use `sm:`, `md:`, `lg:` breakpoints for grid layout

### State Management
- **React Query (TanStack Query v5)** for all server state
- `useQuery` for reads (GET /images, GET /filters)
- `useMutation` for writes (POST upload, POST annotation)
- Invalidate queries on mutation success
- **No Redux/Zustand** — not needed for this app
- Local component state (`useState`) only for UI state (modal open, search input)

### API Client
```typescript
// api/client.ts
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchImages(params: ImageFilters): Promise<PaginatedResponse<ImageResponse>> {
  const query = new URLSearchParams(/* ... */);
  const res = await fetch(`${API_BASE}/api/images?${query}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```
- Plain `fetch` — no axios needed for this scope
- All API functions in `api/client.ts`
- Throw on non-2xx — let React Query handle error state
- Base URL from env var

---

## PostgreSQL

### Migrations
- **Raw SQL migration files** in `app/backend/migrations/`
- Numbered: `001_initial_schema.sql`, `002_add_search_vector.sql`
- Run on container startup via init script
- No Alembic — overkill for a single migration POC

### Naming Conventions
- Tables: `snake_case`, plural (`images`, `annotations`)
- Columns: `snake_case` (`garment_type`, `created_at`)
- Indexes: `idx_{table}_{column}` (`idx_images_garment_type`)
- Primary keys: `id` (UUID)
- Foreign keys: `{referenced_table_singular}_id` (`image_id`)

### Query Patterns
- **SQLAlchemy ORM** for CRUD operations
- **SQLAlchemy Core / text()** acceptable for complex filter queries
- No raw psycopg2 — always go through SQLAlchemy
- Use `Session.execute()` not `Session.query()` (2.0 style)

### Connection
```python
# models/database.py
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Docker

### Local Dev Workflow
```bash
docker compose up --build          # Start all services
docker compose up --build backend  # Rebuild single service
docker compose exec backend bash   # Shell into backend
docker compose down -v             # Stop + remove volumes (clean slate)
```

### docker-compose.yml Structure
```yaml
services:
  frontend:    # Vite dev server, port 5173, hot reload via volume mount
  backend:     # FastAPI + uvicorn, port 8000, hot reload via volume mount
  db:          # PostgreSQL 16, port 5432, persistent volume
```

### Environment Variables
- `.env.example` committed — template with placeholder values
- `.env` gitignored — real secrets (API key)
- Backend reads via `pydantic-settings` (`Settings` class)
- Frontend reads via Vite's `import.meta.env.VITE_*` pattern

### Hot Reload
- **Backend**: mount `./app/backend` into container + `uvicorn --reload`
- **Frontend**: mount `./app/frontend/src` into container + Vite HMR
- **DB**: persistent named volume (data survives restarts)

---

## Testing

### File Naming & Location
```
tests/
├── conftest.py                # Shared fixtures (test DB, mock Claude, sample images)
├── unit/
│   ├── test_classifier_parsing.py   # Pydantic parsing of Claude output
│   └── test_schemas.py              # Schema validation edge cases
├── integration/
│   ├── test_image_filters.py        # Filter queries against test DB
│   └── test_search.py               # FTS query behavior
└── e2e/
    └── test_upload_classify_filter.py  # Full workflow
```

### Unit Tests
- **Purpose**: test parsing logic in isolation, no API calls, no DB
- **Mock Claude responses**: use fixture JSON files in `tests/fixtures/`
- **Test cases for parser**:
  - Valid complete JSON
  - Missing optional fields (designer_brand, location)
  - Malformed JSON (fallback behavior)
  - Unexpected field values

### Integration Tests
- **Purpose**: test filter queries against a real PostgreSQL (test DB in Docker)
- **Setup**: seed DB with known records in `conftest.py`
- **Test cases**:
  - Single filter (garment_type=Dress)
  - Combined filters (garment_type=Dress AND material=Silk)
  - Location filters (continent, country, city)
  - Time filters (year, month)
  - Dynamic filter endpoint returns correct distinct values
  - Full-text search returns expected matches

### E2E Tests
- **Purpose**: upload image → verify classification stored → verify it appears in filtered results
- **Mock Claude API** — deterministic, no API cost
- **Use `httpx.AsyncClient`** with FastAPI's `TestClient`

### Mocking
```python
# conftest.py
@pytest.fixture
def mock_claude_response():
    return GarmentClassification(
        description="A flowing silk midi dress...",
        garment_type="Dress",
        style="Bohemian",
        # ...
    )

@pytest.fixture
def mock_classifier(mock_claude_response, monkeypatch):
    async def _mock_classify(image_path: str):
        return mock_claude_response
    monkeypatch.setattr("app.backend.services.classifier.classify_image", _mock_classify)
```
- Mock at the service boundary, not the HTTP client level
- Use `monkeypatch` (pytest native), not `unittest.mock` unless necessary
- Fixture JSON files for complex mock responses: `tests/fixtures/claude_response_valid.json`

### Running Tests
```bash
# All tests
docker compose exec backend pytest tests/ -v

# Specific suite
docker compose exec backend pytest tests/unit/ -v
docker compose exec backend pytest tests/integration/ -v
docker compose exec backend pytest tests/e2e/ -v

# With coverage
docker compose exec backend pytest tests/ --cov=app.backend --cov-report=term-missing
```

---

## Git Conventions

### Commit Messages
```
<type>: <short description>

Types:
  feat:     New feature
  fix:      Bug fix
  refactor: Code change that neither fixes nor adds
  test:     Adding/updating tests
  docs:     Documentation only
  chore:    Build, config, tooling
  eval:     Evaluation-related changes
```

Examples:
```
feat: add image upload endpoint with Claude classification
feat: implement dynamic filter sidebar
test: add unit tests for Claude output parsing
eval: add ground truth labels for 50 test images
docs: write architecture notes and eval summary in README
chore: configure Docker Compose with hot reload
```

### Logical Commits (Minimum ~10-15)
A commit should represent one coherent unit of work. Target sequence:
1. `chore: scaffold project structure and Docker Compose`
2. `feat: add database schema and SQLAlchemy models`
3. `feat: implement Claude Vision classification service`
4. `test: add unit tests for classification output parsing`
5. `feat: add image upload API endpoint`
6. `feat: add image listing with filter and search endpoints`
7. `test: add integration tests for filter behavior`
8. `feat: implement React gallery grid and upload UI`
9. `feat: add filter sidebar and search functionality`
10. `feat: add designer annotations (create, display, search)`
11. `eval: add test set, ground truth labels, and eval script`
12. `eval: run evaluation and add results`
13. `test: add e2e test for upload-classify-filter workflow`
14. `docs: write README with setup, architecture, and eval summary`
15. `fix: polish edge cases and error handling`

---

## AI Integration Patterns

### Prompt Structure
```python
# System prompt: role + behavior constraints
# User message: image (base64) + instruction
# Tool definition: Pydantic schema → Claude tool_use
# tool_choice: force specific tool ({"type": "tool", "name": "classify_garment"})
```

### Parsing Flow
```
Claude API response
  → find content block with type="tool_use"
  → extract .input dict
  → GarmentClassification.model_validate(input_dict)
  → on ValidationError: log, retry (up to 3x), then fallback defaults
```

### Error Handling
- **Retry**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **Rate limits**: Anthropic returns 429 — respect `retry-after` header
- **Timeout**: 30s per request — Claude vision typically responds in 3-8s
- **Fallback**: return `GarmentClassification` with "Unclassified" defaults — never block upload

### Cost Awareness
- Sonnet vision: ~$0.01-0.03 per image
- 50 eval images: ~$1-2 total
- Log token usage per call for monitoring
- Don't call Claude in tests — always mock

---

## Common Commands

```bash
# Start everything
docker compose up --build

# Stop everything
docker compose down

# Clean slate (removes DB data)
docker compose down -v

# Backend shell
docker compose exec backend bash

# Run tests
docker compose exec backend pytest tests/ -v

# Run linter
docker compose exec backend ruff check app/backend/

# Run formatter
docker compose exec backend ruff format app/backend/

# Run eval (costs ~$1-2)
docker compose exec backend python eval/run_eval.py

# Re-score without API calls
docker compose exec backend python eval/run_eval.py --skip-classify

# Frontend shell
docker compose exec frontend sh

# View API docs
open http://localhost:8000/docs

# View app
open http://localhost:5173
```
## Frontend Design Principles
/Users/sameerauf/Documents/GarmentIQ/design-principles.md


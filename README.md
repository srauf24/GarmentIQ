# GarmentIQ

AI-powered fashion garment classification and inspiration library. Designers upload garment photos, which are automatically classified using vision AI, then browsable through a searchable, filterable gallery with designer annotations.

**Stack**: React 18 + TypeScript + Tailwind | FastAPI + Python 3.12 | PostgreSQL 16 | Claude Sonnet (vision) | Docker Compose

## Setup (3 steps)

```bash
cp .env.example .env          # Add your ANTHROPIC_API_KEY
docker compose up --build      # Starts frontend, backend, and DB
# Frontend → http://localhost:5173   Backend → http://localhost:8000/docs
```

Requires Docker and an Anthropic API key from [console.anthropic.com](https://console.anthropic.com).

## Requirements Mapping

### 1. Image Upload + AI Classification

| Requirement | Implementation |
|---|---|
| Upload garment photos | `POST /api/images/upload` — multipart file upload with optional `uploaded_by`, `location_country`, `location_city` |
| Rich natural-language description | Claude Vision returns a 2-3 sentence description covering construction, fabric, and styling context (`ai_description` field) |
| Structured attributes | `tool_use` with `tool_choice` forces Claude to return a `GarmentClassification` Pydantic schema: garment type, style, material, color palette, pattern, season, occasion, consumer profile, trend notes, designer/brand, and location context (environment, inferred geo, confidence) |
| Store both outputs | Both description and all structured fields persisted in PostgreSQL `images` table. Location stored as separate columns for filtering. |

**Key decision**: Using `tool_choice: {"type": "tool", "name": "classify_garment"}` eliminates JSON parsing failures — Claude is forced to return data matching the exact schema. Retry (3x, exponential backoff) with graceful fallback to "Unclassified" so uploads never fail.

### 2. Search + Filtering

| Requirement | Implementation |
|---|---|
| Visual image grid | Responsive gallery (1-4 columns) with garment type badges, metadata, and color palette chips |
| Garment attribute filters | `garment_type`, `style`, `material`, `pattern`, `season`, `occasion`, `consumer_profile`, `designer_brand` — all as query params on `GET /api/images` |
| Contextual filters | `location_continent`, `location_country`, `location_city`, `year`, `month`, `uploaded_by` |
| Dynamically generated filters | `GET /api/filters` returns distinct values from actual data, not hardcoded lists |
| Full-text search | PostgreSQL `tsvector` with weighted columns (description=A, trend_notes=B, attributes=C). Trigger auto-updates on insert/update. Query: `GET /api/images?q=embroidered+neckline` |

**Key decision**: Search spans both AI descriptions and designer annotations (notes + tags), so a query like "artisan market" finds images whether that phrase came from Claude or a designer's note.

### 3. Designer Annotations

| Requirement | Implementation |
|---|---|
| Add tags, notes, observations | `POST /api/images/{id}/annotations` with `note`, `tags[]`, `created_by` |
| Searchable | Annotation notes searched via `to_tsvector`, tags matched via array contains — both included in the `?q=` search |
| Distinct from AI output | Separate `annotations` table with foreign key to `images`. UI shows AI attributes in an indigo "AI Generated" panel and annotations in an emerald "Designer Notes" panel |

## Architecture

```
app/
├── backend/
│   ├── api/            # Route handlers (images, annotations, filters, health)
│   ├── models/         # SQLAlchemy models + Pydantic schemas
│   ├── services/       # classifier.py — Claude Vision integration
│   ├── core/           # config.py — pydantic-settings
│   └── migrations/     # SQL (schema + search vector trigger)
├── frontend/src/
│   ├── components/     # Gallery (ImageCard, ImageGrid), Filters (Sidebar, SearchBar, ActiveFilters), ImageDetail (AttributePanel, AnnotationPanel)
│   ├── hooks/          # React Query hooks (useImages, useFilterValues, useUploadImage, etc.)
│   ├── pages/          # GalleryPage, ImageDetailPage
│   └── api/client.ts   # Plain fetch wrapper
eval/                   # Evaluation script + 50 test images + ground truth
tests/                  # Unit (77), integration (12), e2e (1) — 90 total
```

No business logic in route handlers — classification lives in `services/classifier.py`. No raw SQL in routes — queries use SQLAlchemy ORM.

## Testing

```bash
docker compose exec backend pytest tests/ -v    # All 90 tests
```

| Suite | Count | What it covers |
|---|---|---|
| Unit | 77 | Classification parsing (valid/missing/malformed), fallback behavior, schema validation, all API endpoints, search logic. Mocked DB. |
| Integration | 12 | Attribute filters, contextual filters (continent, country, year, month), combined filters, FTS, annotation search, dynamic filter values. **Real PostgreSQL** with transactional rollback. |
| E2E | 1 | Upload → classify → filter → search → annotate → verify detail → verify filter values. **Real PostgreSQL**, real file I/O, only Claude mocked. |

## Evaluation

50 images from Pexels across 9 garment types (Dress, Jacket, Suit, Top, Skirt, Coat, Knitwear, Trousers, Accessories), manually labeled for 5 attributes.

```bash
docker compose exec backend python eval/run_eval.py                # Full run (~$1-2)
docker compose exec backend python eval/run_eval.py --skip-classify # Re-score from cache
```

### Results

| Attribute | Accuracy | Notes |
|---|---|---|
| garment_type | **70%** | Strong on primary silhouettes (dress vs jacket vs suit) |
| material | 50% | Knit/wool/cotton hard to distinguish visually |
| occasion | 54% | "Casual Daily" vs "Smart Casual" is genuinely ambiguous |
| style | 36% | High label overlap — "Casual" vs "Classic" vs "Minimalist" |
| location_country | **100%** | Correctly returns null for studio images with no geographic cues |

**Where it works well**: Garment type is the most actionable filter for designers and has the highest accuracy. Location inference shows strong restraint — the model doesn't hallucinate geography when visual cues are absent.

**Where it struggles**: Style and occasion have low exact-match accuracy, but this is largely a label taxonomy problem. Many "errors" are reasonable alternative interpretations (e.g., a structured blazer classified as "Classic" instead of "Formal"). Material identification is inherently limited without tactile information.

**With more time**:
- Reduce style/occasion vocabulary overlap — fewer, more distinct categories
- Add fuzzy/semantic matching to evaluation — "Casual"/"Classic" as partial match
- Few-shot examples in the prompt for underperforming categories
- Confidence calibration to flag low-certainty predictions for human review

Full confusion pair analysis: [eval/results/eval_summary.md](eval/results/eval_summary.md)

## Simplifying Assumptions

- **No auth**: Single-user proof of concept. `uploaded_by` is a free-text field, not tied to accounts.
- **Synchronous classification**: Upload blocks until Claude responds (~7-10s). At scale, this would be an async job queue.
- **No image optimization**: Original files stored as-is. Production would add resizing, thumbnails, and CDN.
- **SQLAlchemy sync driver**: Using synchronous DB sessions. Adequate for single-user; would switch to async for concurrent load.
- **No Alembic**: Single SQL migration file run on container startup. Sufficient for a POC with one schema version.

## What I'd Build Next

1. **Async upload pipeline** — Background worker (Celery/ARQ) for classification so uploads return immediately
2. **Similar image search** — CLIP embeddings + pgvector for "find garments like this one"
3. **Bulk upload** — Drag-and-drop multiple images with progress tracking
4. **Export/share** — Moodboard creation from filtered selections
5. **Multi-user with auth** — User accounts, team workspaces, permission-based annotations

---

## Appendix: Full Evaluation Findings

### Per-Attribute Accuracy

| Attribute | Correct | Total | Accuracy |
|-----------|---------|-------|----------|
| garment_type | 35 | 50 | 70.0% |
| style | 18 | 50 | 36.0% |
| material | 25 | 50 | 50.0% |
| occasion | 27 | 50 | 54.0% |
| location_country | 50 | 50 | 100.0% |

### Top Confusion Pairs

**garment_type**
- Top misclassified as Blouse (2x)
- Skirt misclassified as Top (2x)
- Trousers misclassified as Knitwear (2x)

**style**
- Casual misclassified as Classic (9x)
- Casual misclassified as Minimalist (5x)
- Formal misclassified as Classic (4x)

**material**
- Cotton misclassified as Knit (3x)
- Synthetic misclassified as Knit (3x)
- Knit misclassified as Wool (3x)

**occasion**
- Casual Daily misclassified as Smart Casual (10x)
- Casual Daily misclassified as Business (5x)
- Casual Daily misclassified as Evening/Formal (3x)

### Analysis

The confusion pairs reveal a consistent pattern: the model's "errors" are often reasonable alternative interpretations rather than outright mistakes. "Top" vs "Blouse" is a legitimate vocabulary difference. "Casual" vs "Classic" reflects genuine ambiguity in style categorization. The largest single confusion — Casual Daily → Smart Casual (10 cases) — suggests the model reads styled photography as implying a more elevated context than the garment alone would warrant.

Material identification is the most fundamentally limited attribute. Distinguishing cotton from synthetic, or knit from wool, requires tactile information that no vision model can access. The 50% accuracy here represents roughly the ceiling for visual-only material classification on diverse garment types.

Location country achieves 100% not because the model is exceptionally good at geography, but because all 50 test images are studio/Pexels photos with no visible geographic cues. The model correctly returns null in every case, demonstrating appropriate calibration — it doesn't guess when evidence is absent.

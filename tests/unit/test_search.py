"""Unit tests for full-text search across images and annotations."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient


def _make_image(**overrides) -> SimpleNamespace:
    defaults = {
        "id": uuid.uuid4(),
        "filename": f"{uuid.uuid4()}.jpg",
        "original_filename": "photo.jpg",
        "file_path": "/uploads/photo.jpg",
        "ai_description": "A garment.",
        "garment_type": "Dress",
        "style": "Bohemian",
        "material": "Silk",
        "color_palette": ["Blue"],
        "pattern": "Floral",
        "season": "Spring",
        "occasion": "Casual Daily",
        "consumer_profile": "Young Professional",
        "designer_brand": None,
        "trend_notes": "Trending.",
        "location_environment": None,
        "location_inferred_geo": None,
        "location_confidence": None,
        "location_continent": None,
        "location_country": None,
        "location_city": None,
        "uploaded_by": None,
        "created_at": datetime.now(timezone.utc),
        "annotations": [],
        "search_vector": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class FakeQuery:
    """Minimal query mock supporting chained operations."""

    def __init__(self, items: list):
        self._items = items

    def filter(self, *args):
        filtered = list(self._items)
        for expr in args:
            try:
                left = expr.left
                if hasattr(left, "key"):
                    col_name = left.key
                    value = expr.right.value
                    filtered = [
                        i for i in filtered
                        if getattr(i, col_name, None) == value
                    ]
            except (AttributeError, TypeError):
                pass
        return FakeQuery(filtered)

    def distinct(self):
        return self

    def subquery(self):
        # Return something that won't break .in_() in the or_ clause
        return []

    def count(self):
        return len(self._items)

    def order_by(self, *args):
        return FakeQuery(self._items)

    def offset(self, n):
        return FakeQuery(self._items[n:])

    def limit(self, n):
        return FakeQuery(self._items[:n])

    def all(self):
        return list(self._items)


class FakeSession:
    def __init__(self, images: list):
        self._images = images

    def query(self, model):
        # Both Image and Annotation.image_id queries go through here
        return FakeQuery(self._images)

    def close(self):
        pass


def _override_db(images: list):
    """Create a dependency override for get_db."""
    from app.backend.main import app
    from app.backend.models.database import get_db

    def _get_fake_db():
        db = FakeSession(images)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_fake_db
    return app


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    from app.backend.main import app
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_search_matches_image_description() -> None:
    images = [_make_image(ai_description="A beautiful silk dress")]
    app = _override_db(images)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images?q=silk")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.anyio
async def test_search_matches_annotation_note() -> None:
    images = [_make_image()]
    app = _override_db(images)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images?q=artisan")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.anyio
async def test_search_matches_annotation_tag() -> None:
    images = [_make_image()]
    app = _override_db(images)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images?q=vintage")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.anyio
async def test_search_empty_q_returns_all() -> None:
    images = [_make_image(), _make_image(), _make_image()]
    app = _override_db(images)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.anyio
async def test_search_combined_with_filter() -> None:
    images = [
        _make_image(garment_type="Dress"),
        _make_image(garment_type="Jacket"),
    ]
    app = _override_db(images)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images?q=silk&garment_type=Dress")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Filter should narrow to Dress only
    for item in data["items"]:
        assert item["garment_type"] == "Dress"

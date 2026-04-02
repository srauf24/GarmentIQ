"""Unit tests for the single image detail endpoint."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient


def _make_image(**overrides) -> SimpleNamespace:
    """Create a fake Image-like object with defaults."""
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
    def __init__(self, items: list):
        self._items = items
        self._filters = []

    def filter(self, *args):
        new_q = FakeQuery(self._items)
        new_q._filters = self._filters + list(args)
        return new_q

    def first(self):
        results = list(self._items)
        for expr in self._filters:
            try:
                left = expr.left
                if hasattr(left, "key"):
                    col_name = left.key
                    value = expr.right.value
                    results = [
                        i for i in results
                        if getattr(i, col_name, None) == value
                    ]
            except (AttributeError, TypeError):
                pass
        return results[0] if results else None


class FakeSession:
    def __init__(self, images: list):
        self._images = images

    def query(self, model):
        return FakeQuery(self._images)

    def close(self):
        pass


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    from app.backend.main import app
    app.dependency_overrides.clear()


def _override_db(images):
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


@pytest.mark.anyio
async def test_get_image_returns_200() -> None:
    image = _make_image()
    app = _override_db([image])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/images/{image.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(image.id)
    assert data["garment_type"] == "Dress"
    assert data["style"] == "Bohemian"
    assert "annotations" in data
    assert "location" in data
    assert "image_url" in data


@pytest.mark.anyio
async def test_get_image_not_found_returns_404() -> None:
    app = _override_db([])

    fake_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/images/{fake_id}")
    assert response.status_code == 404

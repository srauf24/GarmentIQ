"""Unit tests for the image listing endpoint with filters."""

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
    """Minimal query mock that supports chained filter/order/pagination."""

    def __init__(self, items: list):
        self._items = items

    def filter(self, *args):
        # For unit tests, we evaluate simple column == value comparisons
        # by inspecting the BinaryExpression. Complex expressions (extract,
        # FTS op) are skipped — they're tested via integration tests.
        filtered = list(self._items)
        for expr in args:
            try:
                left = expr.left
                # Only handle direct column comparisons (has .key attribute)
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
        return FakeQuery(self._images)

    def close(self):
        pass


@pytest.fixture
def _seed_images():
    """Return a list of fake images for testing."""
    return [
        _make_image(
            garment_type="Dress",
            material="Silk",
            style="Bohemian",
            created_at=datetime(2025, 3, 15, tzinfo=timezone.utc),
        ),
        _make_image(
            garment_type="Jacket",
            material="Leather",
            style="Streetwear",
            created_at=datetime(2025, 6, 10, tzinfo=timezone.utc),
        ),
        _make_image(
            garment_type="Dress",
            material="Cotton",
            style="Casual",
            created_at=datetime(2024, 11, 5, tzinfo=timezone.utc),
        ),
    ]


@pytest.fixture
def _mock_db(_seed_images):
    """Override get_db with FakeSession."""
    from app.backend.main import app
    from app.backend.models.database import get_db

    def _get_fake_db():
        db = FakeSession(_seed_images)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_fake_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_db")
async def test_list_images_returns_paginated_response() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_db")
async def test_list_images_single_filter() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images?garment_type=Dress")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["garment_type"] == "Dress"


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_db")
async def test_list_images_multiple_filters_and() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images?garment_type=Dress&material=Silk")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["garment_type"] == "Dress"
    assert data["items"][0]["material"] == "Silk"


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_db")
async def test_list_images_pagination() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images?page=2&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["total_pages"] == 2
    assert data["page"] == 2
    assert len(data["items"]) == 1


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_db")
async def test_list_images_empty_result() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images?garment_type=Nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["total_pages"] == 0


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_db")
async def test_list_images_includes_annotations() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/images")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert "annotations" in item
        assert isinstance(item["annotations"], list)


@pytest.mark.anyio
async def test_list_images_year_filter() -> None:
    """Year filter narrows results (FakeQuery skips extract, so we test the endpoint accepts it)."""
    from app.backend.main import app
    from app.backend.models.database import get_db

    images = [
        _make_image(created_at=datetime(2025, 3, 15, tzinfo=timezone.utc)),
    ]

    def _get_fake_db():
        db = FakeSession(images)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_fake_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/images?year=2025")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_images_month_filter() -> None:
    """Month filter is accepted by the endpoint."""
    from app.backend.main import app
    from app.backend.models.database import get_db

    images = [
        _make_image(created_at=datetime(2025, 6, 10, tzinfo=timezone.utc)),
    ]

    def _get_fake_db():
        db = FakeSession(images)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_fake_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/images?month=6")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_images_search_q() -> None:
    """Search param q is accepted by the endpoint."""
    from app.backend.main import app
    from app.backend.models.database import get_db

    images = [_make_image()]

    def _get_fake_db():
        db = FakeSession(images)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_fake_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/images?q=silk")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    finally:
        app.dependency_overrides.clear()

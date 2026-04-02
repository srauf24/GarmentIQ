"""Unit tests for annotation create and delete endpoints."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

EXISTING_IMAGE_ID = uuid.uuid4()
EXISTING_ANNOTATION_ID = uuid.uuid4()


def _make_image(image_id=None):
    return SimpleNamespace(
        id=image_id or EXISTING_IMAGE_ID,
    )


def _make_annotation(annotation_id=None, image_id=None):
    return SimpleNamespace(
        id=annotation_id or EXISTING_ANNOTATION_ID,
        image_id=image_id or EXISTING_IMAGE_ID,
        note="Great piece",
        tags=["vintage"],
        created_by="designer1",
        created_at=datetime.now(timezone.utc),
    )


class FakeQuery:
    def __init__(self, items):
        self._items = list(items)
        self._filters = []

    def filter(self, *args):
        new_query = FakeQuery(self._items)
        new_query._filters = self._filters + list(args)
        return new_query

    def first(self):
        # Evaluate filters against items
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
    def __init__(self, images, annotations):
        self._images = images
        self._annotations = annotations
        self._added = []
        self._deleted = []

    def query(self, model):
        from app.backend.models.database import Image, Annotation

        if model is Image:
            return FakeQuery(self._images)
        if model is Annotation:
            return FakeQuery(self._annotations)
        return FakeQuery([])

    def add(self, obj):
        # Simulate DB populating fields
        obj.id = uuid.uuid4()
        obj.created_at = datetime.now(timezone.utc)
        self._added.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def delete(self, obj):
        self._deleted.append(obj)

    def close(self):
        pass


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    from app.backend.main import app
    app.dependency_overrides.clear()


def _override_db(images, annotations=None):
    from app.backend.main import app
    from app.backend.models.database import get_db

    def _get_fake_db():
        db = FakeSession(images, annotations or [])
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_fake_db
    return app


@pytest.mark.anyio
async def test_create_annotation_returns_201() -> None:
    app = _override_db(images=[_make_image()])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/images/{EXISTING_IMAGE_ID}/annotations",
            json={"note": "Beautiful embroidery", "tags": ["artisan", "silk"], "created_by": "designer1"},
        )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["image_id"] == str(EXISTING_IMAGE_ID)
    assert data["note"] == "Beautiful embroidery"
    assert data["tags"] == ["artisan", "silk"]
    assert data["created_by"] == "designer1"
    assert "created_at" in data


@pytest.mark.anyio
async def test_create_annotation_image_not_found_returns_404() -> None:
    app = _override_db(images=[])

    fake_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/images/{fake_id}/annotations",
            json={"note": "Test"},
        )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_annotation_partial_body() -> None:
    app = _override_db(images=[_make_image()])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/api/images/{EXISTING_IMAGE_ID}/annotations",
            json={},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["note"] is None
    assert data["tags"] is None
    assert data["created_by"] is None


@pytest.mark.anyio
async def test_delete_annotation_returns_204() -> None:
    annotation = _make_annotation()
    app = _override_db(images=[], annotations=[annotation])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/images/{EXISTING_IMAGE_ID}/annotations/{EXISTING_ANNOTATION_ID}",
        )
    assert response.status_code == 204


@pytest.mark.anyio
async def test_delete_annotation_not_found_returns_404() -> None:
    app = _override_db(images=[], annotations=[])

    fake_annotation_id = uuid.uuid4()
    fake_image_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/images/{fake_image_id}/annotations/{fake_annotation_id}",
        )
    assert response.status_code == 404

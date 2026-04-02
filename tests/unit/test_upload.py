"""Unit tests for the image upload endpoint."""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from app.backend.models.schemas import GarmentClassification, LocationContext
from app.backend.services.classifier import ClassificationError


def _mock_classification() -> GarmentClassification:
    return GarmentClassification(
        description="A flowing silk midi dress with bohemian flair.",
        garment_type="Dress",
        style="Bohemian",
        material="Silk",
        color_palette=["Navy Blue", "Cream"],
        pattern="Floral",
        season="Spring",
        occasion="Casual Daily",
        consumer_profile="Young Professional",
        trend_notes="Part of the oversized silhouette trend.",
        location=LocationContext(
            environment="Urban Street",
            inferred_country="France",
            inferred_city="Paris",
            inferred_continent="Europe",
            confidence=0.8,
        ),
    )


@pytest.fixture(autouse=True)
def _use_tmp_upload_dir(monkeypatch, tmp_path):
    """Point uploads to a temp directory for all tests."""
    monkeypatch.setattr("app.backend.core.config.settings.upload_dir", str(tmp_path))


@pytest.fixture
def _mock_classify_success(monkeypatch):
    """Mock classify_image to return a valid classification."""
    async def _mock(file_path: str) -> GarmentClassification:
        return _mock_classification()

    monkeypatch.setattr(
        "app.backend.api.images.classify_image", _mock
    )


@pytest.fixture
def _mock_classify_failure(monkeypatch):
    """Mock classify_image to raise ClassificationError."""
    async def _mock(file_path: str) -> GarmentClassification:
        raise ClassificationError("Claude API unavailable")

    monkeypatch.setattr(
        "app.backend.api.images.classify_image", _mock
    )


@pytest.fixture
def _mock_db(monkeypatch):
    """Mock the DB session so no real database is needed."""
    from unittest.mock import MagicMock

    from app.backend.models.database import Image

    class FakeSession:
        def __init__(self):
            self._image = None

        def add(self, obj):
            self._image = obj
            # Simulate DB generating fields
            import uuid
            from datetime import datetime, timezone

            obj.id = uuid.uuid4()
            obj.created_at = datetime.now(timezone.utc)
            obj.annotations = []

        def commit(self):
            pass

        def refresh(self, obj):
            pass

        def close(self):
            pass

    def _get_fake_db():
        db = FakeSession()
        try:
            yield db
        finally:
            db.close()

    from app.backend.models.database import get_db
    from app.backend.main import app

    app.dependency_overrides[get_db] = _get_fake_db
    yield
    app.dependency_overrides.clear()


def _make_file(filename: str = "dress.jpg", content: bytes = b"fake image data"):
    return (filename, content, "image/jpeg")


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_classify_success", "_mock_db")
async def test_upload_valid_image_returns_201() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": _make_file()},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["garment_type"] == "Dress"
    assert data["style"] == "Bohemian"
    assert data["material"] == "Silk"
    assert data["ai_description"] is not None
    assert "id" in data


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_classify_success", "_mock_db")
async def test_upload_invalid_extension_returns_400() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": ("notes.txt", b"not an image", "text/plain")},
        )
    assert response.status_code == 400


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_classify_failure", "_mock_db")
async def test_upload_classifier_failure_returns_502() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": _make_file()},
        )
    assert response.status_code == 502


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_classify_success", "_mock_db")
async def test_upload_manual_location_overrides_ai() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": _make_file()},
            data={"location_country": "Italy", "location_city": "Milan"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["location"]["country"] == "Italy"
    assert data["location"]["city"] == "Milan"


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_classify_success", "_mock_db")
async def test_upload_ai_location_fallback() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": _make_file()},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["location"]["country"] == "France"
    assert data["location"]["city"] == "Paris"
    assert data["location"]["continent"] == "Europe"


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_classify_success", "_mock_db")
async def test_upload_file_saved_to_disk(tmp_path) -> None:
    from app.backend.main import app
    from app.backend.core.config import settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": _make_file()},
        )
    assert response.status_code == 201
    # Check a file was written to the upload dir
    files = os.listdir(settings.upload_dir)
    assert len(files) >= 1
    assert any(f.endswith(".jpg") for f in files)


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_classify_success", "_mock_db")
async def test_upload_response_has_image_url() -> None:
    from app.backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": _make_file()},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["image_url"].startswith("/uploads/")
    assert data["image_url"].endswith(".jpg")

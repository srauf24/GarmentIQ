"""E2E test: Upload → Classify → Filter → Search → Annotate → Detail.

Runs against real PostgreSQL with transactional rollback.
Only Claude Vision is mocked (for cost and determinism).
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.backend.models.schemas import GarmentClassification, LocationContext

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def mock_classifier(monkeypatch):
    """Mock classify_image to return a deterministic classification."""
    classification = GarmentClassification(
        description="A lightweight cotton sundress with delicate floral print, "
        "perfect for warm-weather outings",
        garment_type="Dress",
        style="Casual",
        material="Cotton",
        color_palette=["White", "Pink"],
        pattern="Floral",
        season="Summer",
        occasion="Casual Daily",
        consumer_profile="Young Professional",
        designer_brand=None,
        trend_notes="Part of the relaxed summer silhouette trend in 2025-2026.",
        location=LocationContext(
            environment="Studio",
            inferred_country="USA",
            inferred_city="Los Angeles",
            inferred_continent="North America",
            confidence=0.3,
        ),
    )

    mock = AsyncMock(return_value=classification)
    monkeypatch.setattr("app.backend.api.images.classify_image", mock)
    return mock


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    """Use a temp directory for uploads so files don't persist."""
    upload_path = str(tmp_path / "uploads")
    os.makedirs(upload_path, exist_ok=True)
    monkeypatch.setattr("app.backend.api.images.settings.upload_dir", upload_path)
    return upload_path


class TestUploadClassifyFilter:
    def test_full_workflow(
        self, client, mock_classifier, upload_dir, db
    ) -> None:
        # --- Step 1: Upload ---
        image_path = FIXTURES_DIR / "test_image.png"
        with open(image_path, "rb") as f:
            res = client.post(
                "/api/images/upload",
                files={"file": ("cargo_pants.png", f, "image/png")},
                data={"uploaded_by": "TestUser"},
            )

        assert res.status_code == 201, res.text
        data = res.json()
        image_id = data["id"]

        # --- Step 2: Verify classification stored ---
        assert data["garment_type"] == "Dress"
        assert data["style"] == "Casual"
        assert data["material"] == "Cotton"
        assert "sundress" in data["ai_description"]
        assert data["season"] == "Summer"
        assert data["uploaded_by"] == "TestUser"
        assert data["original_filename"] == "cargo_pants.png"
        assert data["location"]["continent"] == "North America"
        assert data["location"]["country"] == "USA"

        # Verify file was actually saved to disk
        saved_filename = data["filename"]
        assert os.path.exists(os.path.join(upload_dir, saved_filename))

        # --- Step 3: Verify appears in filtered results ---
        res = client.get("/api/images?garment_type=Dress")
        assert res.status_code == 200
        items = res.json()["items"]
        item_ids = [item["id"] for item in items]
        assert image_id in item_ids

        # --- Step 4: Verify searchable via FTS ---
        res = client.get("/api/images?q=sundress")
        assert res.status_code == 200
        items = res.json()["items"]
        item_ids = [item["id"] for item in items]
        assert image_id in item_ids

        # --- Step 5: Add annotation ---
        res = client.post(
            f"/api/images/{image_id}/annotations",
            json={
                "note": "Great summer piece for the resort collection",
                "tags": ["summer", "resort", "casual"],
                "created_by": "TestUser",
            },
        )
        assert res.status_code == 201, res.text
        annotation_id = res.json()["id"]

        # --- Step 6: Verify annotation on detail ---
        res = client.get(f"/api/images/{image_id}")
        assert res.status_code == 200
        detail = res.json()
        assert detail["garment_type"] == "Dress"
        assert len(detail["annotations"]) == 1
        anno = detail["annotations"][0]
        assert anno["id"] == annotation_id
        assert anno["note"] == "Great summer piece for the resort collection"
        assert "summer" in anno["tags"]
        assert "resort" in anno["tags"]
        assert anno["created_by"] == "TestUser"

        # --- Step 7: Verify filter values updated ---
        res = client.get("/api/filters")
        assert res.status_code == 200
        filters = res.json()
        assert "Dress" in filters["garment_type"]
        assert "Cotton" in filters["material"]
        assert "Summer" in filters["season"]

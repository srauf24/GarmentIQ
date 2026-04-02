"""Unit tests for Pydantic request/response schemas."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.backend.models.schemas import (
    AnnotationCreate,
    AnnotationResponse,
    FilterValuesResponse,
    GarmentClassification,
    ImageResponse,
    LocationContext,
    LocationResponse,
    PaginatedResponse,
)


def _valid_classification_data() -> dict:
    return {
        "description": "A flowing silk midi dress with bohemian flair.",
        "garment_type": "Dress",
        "style": "Bohemian",
        "material": "Silk",
        "color_palette": ["Navy Blue", "Cream"],
        "pattern": "Floral",
        "season": "Spring",
        "occasion": "Casual Daily",
        "consumer_profile": "Young Professional",
        "trend_notes": "Part of the oversized silhouette trend.",
    }


def test_garment_classification_valid_complete() -> None:
    data = _valid_classification_data()
    data["designer_brand"] = "Zimmermann"
    data["location"] = {
        "environment": "Urban Street",
        "inferred_country": "France",
        "inferred_city": "Paris",
        "inferred_continent": "Europe",
        "confidence": 0.85,
    }
    result = GarmentClassification(**data)
    assert result.garment_type == "Dress"
    assert result.designer_brand == "Zimmermann"
    assert result.location.inferred_city == "Paris"
    assert result.location.confidence == 0.85


def test_garment_classification_optional_defaults() -> None:
    result = GarmentClassification(**_valid_classification_data())
    assert result.designer_brand is None
    assert result.location.environment is None
    assert result.location.confidence is None


def test_garment_classification_model_json_schema() -> None:
    schema = GarmentClassification.model_json_schema()
    assert "properties" in schema
    props = schema["properties"]
    assert "garment_type" in props
    assert "description" in props["garment_type"]
    assert "style" in props
    assert "description" in props["style"]
    assert "location" in props


def test_location_context_confidence_bounds() -> None:
    LocationContext(confidence=0.0)
    LocationContext(confidence=1.0)

    with pytest.raises(ValidationError):
        LocationContext(confidence=1.5)

    with pytest.raises(ValidationError):
        LocationContext(confidence=-0.1)


def test_annotation_response_from_attributes() -> None:
    data = {
        "id": uuid4(),
        "image_id": uuid4(),
        "note": "Great piece",
        "tags": ["vintage", "silk"],
        "created_by": "designer1",
        "created_at": datetime.now(timezone.utc),
    }
    result = AnnotationResponse.model_validate(data, from_attributes=True)
    assert result.note == "Great piece"
    assert result.tags == ["vintage", "silk"]


def test_image_response_with_nested_location() -> None:
    now = datetime.now(timezone.utc)
    image_id = uuid4()
    data = {
        "id": image_id,
        "filename": "abc123.jpg",
        "original_filename": "dress.jpg",
        "image_url": "/uploads/abc123.jpg",
        "ai_description": "A silk dress",
        "garment_type": "Dress",
        "style": "Bohemian",
        "material": "Silk",
        "color_palette": ["Blue"],
        "pattern": "Floral",
        "season": "Spring",
        "occasion": "Casual Daily",
        "consumer_profile": "Young Professional",
        "designer_brand": None,
        "trend_notes": "Trending now.",
        "location": LocationResponse(
            environment="Urban Street",
            continent="Europe",
            country="France",
            city="Paris",
        ),
        "uploaded_by": "user1",
        "created_at": now,
        "annotations": [
            {
                "id": uuid4(),
                "image_id": image_id,
                "note": "Love it",
                "tags": ["fav"],
                "created_by": "user1",
                "created_at": now,
            }
        ],
    }
    result = ImageResponse(**data)
    assert result.location.city == "Paris"
    assert len(result.annotations) == 1
    assert result.annotations[0].note == "Love it"


def test_annotation_create_partial() -> None:
    result = AnnotationCreate()
    assert result.note is None
    assert result.tags is None
    assert result.created_by is None


def test_paginated_response_with_image_response() -> None:
    now = datetime.now(timezone.utc)
    image_id = uuid4()
    image = ImageResponse(
        id=image_id,
        filename="test.jpg",
        original_filename="test.jpg",
        image_url="/uploads/test.jpg",
        ai_description=None,
        garment_type=None,
        style=None,
        material=None,
        color_palette=None,
        pattern=None,
        season=None,
        occasion=None,
        consumer_profile=None,
        designer_brand=None,
        trend_notes=None,
        location=LocationResponse(),
        uploaded_by=None,
        created_at=now,
        annotations=[],
    )
    paginated = PaginatedResponse[ImageResponse](
        items=[image],
        total=1,
        page=1,
        page_size=20,
        total_pages=1,
    )
    assert paginated.total == 1
    assert len(paginated.items) == 1
    assert paginated.items[0].id == image_id


def test_filter_values_response_empty_lists() -> None:
    result = FilterValuesResponse(
        garment_type=[],
        style=[],
        material=[],
        color_palette=[],
        pattern=[],
        season=[],
        occasion=[],
        consumer_profile=[],
        designer_brand=[],
        location_continent=[],
        location_country=[],
        location_city=[],
        year=[],
        month=[],
        uploaded_by=[],
    )
    assert result.garment_type == []
    assert result.year == []

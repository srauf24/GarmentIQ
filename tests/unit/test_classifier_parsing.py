"""Unit tests for parsing Claude model output into structured attributes.

These tests validate Pydantic parsing logic in isolation — no API calls,
no database. Uses fixture JSON files that mirror real Claude tool_use output.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.backend.models.schemas import GarmentClassification
from app.backend.services.classifier import _build_fallback

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestValidParsing:
    def test_complete_json_parses_all_fields(self) -> None:
        data = json.loads((FIXTURES / "claude_response_valid.json").read_text())
        result = GarmentClassification.model_validate(data)

        assert result.garment_type == "Dress"
        assert result.style == "Bohemian"
        assert result.material == "Silk"
        assert result.color_palette == ["Emerald Green", "Gold"]
        assert result.pattern == "Floral"
        assert result.season == "Spring"
        assert result.occasion == "Casual Daily"
        assert result.consumer_profile == "Young Professional"
        assert result.designer_brand is None
        assert result.location.inferred_country == "Japan"
        assert result.location.confidence == 0.7

    def test_description_is_preserved(self) -> None:
        data = json.loads((FIXTURES / "claude_response_valid.json").read_text())
        result = GarmentClassification.model_validate(data)
        assert "silk midi dress" in result.description.lower()


class TestMissingOptionalFields:
    def test_missing_designer_brand_defaults_to_none(self) -> None:
        data = json.loads(
            (FIXTURES / "claude_response_missing_fields.json").read_text()
        )
        result = GarmentClassification.model_validate(data)
        assert result.designer_brand is None

    def test_missing_location_gets_empty_defaults(self) -> None:
        data = json.loads(
            (FIXTURES / "claude_response_missing_fields.json").read_text()
        )
        result = GarmentClassification.model_validate(data)
        assert result.location.environment is None
        assert result.location.inferred_country is None
        assert result.location.confidence is None


class TestMalformedInput:
    def test_missing_required_field_raises_validation_error(self) -> None:
        """If garment_type is missing, Pydantic should raise ValidationError."""
        data = {"description": "A dress", "style": "Casual"}
        with pytest.raises(ValidationError):
            GarmentClassification.model_validate(data)

    def test_empty_dict_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GarmentClassification.model_validate({})

    def test_wrong_type_for_color_palette_raises(self) -> None:
        """color_palette should be a list, not a string."""
        data = json.loads((FIXTURES / "claude_response_valid.json").read_text())
        data["color_palette"] = "Red"
        with pytest.raises(ValidationError):
            GarmentClassification.model_validate(data)


class TestFallbackClassification:
    def test_fallback_has_unclassified_defaults(self) -> None:
        result = _build_fallback()
        assert result.garment_type == "Unclassified"
        assert result.style == "Unclassified"
        assert result.material == "Unclassified"
        assert result.color_palette == ["Unknown"]
        assert result.designer_brand is None

    def test_fallback_with_raw_text_preserves_description(self) -> None:
        result = _build_fallback("Some raw text from Claude")
        assert result.description == "Some raw text from Claude"


class TestToolSchemaGeneration:
    def test_schema_is_valid_json_schema(self) -> None:
        schema = GarmentClassification.model_json_schema()
        assert "properties" in schema
        assert "garment_type" in schema["properties"]
        assert "description" in schema["properties"]["garment_type"]

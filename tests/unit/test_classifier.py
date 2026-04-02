"""Unit tests for the Claude Vision classification service."""

import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.backend.models.schemas import GarmentClassification
from app.backend.services.classifier import (
    ClassificationError,
    _build_fallback,
    _build_tool_definition,
    _encode_image,
    classify_image,
)


# --- _build_tool_definition tests ---


def test_tool_definition_has_required_keys() -> None:
    tool = _build_tool_definition()
    assert tool["name"] == "classify_garment"
    assert "description" in tool
    assert "input_schema" in tool


def test_tool_definition_schema_has_field_descriptions() -> None:
    tool = _build_tool_definition()
    props = tool["input_schema"]["properties"]
    assert "garment_type" in props
    assert "description" in props["garment_type"]
    assert "style" in props
    assert "color_palette" in props


# --- _encode_image tests ---


def test_encode_image_jpg(tmp_path) -> None:
    img = tmp_path / "test.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg-data")
    data, media_type = _encode_image(str(img))
    assert media_type == "image/jpeg"
    assert base64.b64decode(data) == b"\xff\xd8\xff\xe0fake-jpeg-data"


def test_encode_image_png(tmp_path) -> None:
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNGfake-png-data")
    data, media_type = _encode_image(str(img))
    assert media_type == "image/png"
    assert base64.b64decode(data) == b"\x89PNGfake-png-data"


def test_encode_image_webp(tmp_path) -> None:
    img = tmp_path / "test.webp"
    img.write_bytes(b"RIFF\x00\x00\x00\x00WEBP")
    data, media_type = _encode_image(str(img))
    assert media_type == "image/webp"


# --- _build_fallback tests ---


def test_fallback_returns_valid_classification() -> None:
    result = _build_fallback()
    assert isinstance(result, GarmentClassification)
    assert result.garment_type == "Unclassified"
    assert result.season == "All-Season"
    assert result.designer_brand is None
    assert result.color_palette == ["Unknown"]
    assert "manual review" in result.description.lower()


def test_fallback_with_raw_text() -> None:
    result = _build_fallback("Some text from Claude")
    assert result.description == "Some text from Claude"
    assert result.garment_type == "Unclassified"


# --- classify_image tests (mocked Claude API) ---


VALID_TOOL_INPUT = {
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
    "location": {
        "environment": "Urban Street",
        "inferred_country": "France",
        "inferred_city": "Paris",
        "inferred_continent": "Europe",
        "confidence": 0.8,
    },
}


def _make_tool_use_response(tool_input: dict):
    """Build a fake Claude response with a tool_use block."""
    tool_block = SimpleNamespace(type="tool_use", name="classify_garment", input=tool_input)
    return SimpleNamespace(content=[tool_block])


def _make_text_only_response():
    """Build a fake Claude response with no tool_use block."""
    text_block = SimpleNamespace(type="text", text="I see a dress.")
    return SimpleNamespace(content=[text_block])


@pytest.fixture
def _mock_encode(monkeypatch):
    """Mock _encode_image to avoid needing a real file."""
    monkeypatch.setattr(
        "app.backend.services.classifier._encode_image",
        lambda path: ("ZmFrZQ==", "image/jpeg"),
    )


@pytest.fixture
def _mock_no_sleep(monkeypatch):
    """Mock asyncio.sleep to avoid actual waits in tests."""
    monkeypatch.setattr(
        "app.backend.services.classifier.asyncio.sleep",
        AsyncMock(),
    )


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_encode", "_mock_no_sleep")
async def test_classify_image_success(monkeypatch) -> None:
    mock_create = AsyncMock(return_value=_make_tool_use_response(VALID_TOOL_INPUT))
    monkeypatch.setattr(
        "app.backend.services.classifier.anthropic.AsyncAnthropic",
        lambda **kwargs: SimpleNamespace(messages=SimpleNamespace(create=mock_create)),
    )

    result = await classify_image("/fake/path.jpg")
    assert isinstance(result, GarmentClassification)
    assert result.garment_type == "Dress"
    assert result.style == "Bohemian"
    assert result.color_palette == ["Navy Blue", "Cream"]
    assert result.location.inferred_city == "Paris"
    mock_create.assert_called_once()


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_encode", "_mock_no_sleep")
async def test_classify_image_api_error_raises_classification_error(monkeypatch) -> None:
    import anthropic as anthropic_module

    mock_create = AsyncMock(
        side_effect=anthropic_module.APIError(
            message="Server error",
            request=SimpleNamespace(method="POST", url="https://api.anthropic.com"),
            body=None,
        )
    )
    monkeypatch.setattr(
        "app.backend.services.classifier.anthropic.AsyncAnthropic",
        lambda **kwargs: SimpleNamespace(messages=SimpleNamespace(create=mock_create)),
    )

    with pytest.raises(ClassificationError, match="Claude API failed"):
        await classify_image("/fake/path.jpg")

    assert mock_create.call_count == 3


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_encode", "_mock_no_sleep")
async def test_classify_image_no_tool_block_returns_fallback(monkeypatch) -> None:
    mock_create = AsyncMock(return_value=_make_text_only_response())
    monkeypatch.setattr(
        "app.backend.services.classifier.anthropic.AsyncAnthropic",
        lambda **kwargs: SimpleNamespace(messages=SimpleNamespace(create=mock_create)),
    )

    result = await classify_image("/fake/path.jpg")
    assert isinstance(result, GarmentClassification)
    assert result.garment_type == "Unclassified"
    assert mock_create.call_count == 3


@pytest.mark.anyio
@pytest.mark.usefixtures("_mock_encode", "_mock_no_sleep")
async def test_classify_image_rate_limit_retries(monkeypatch) -> None:
    import anthropic as anthropic_module

    rate_limit_error = anthropic_module.RateLimitError(
        message="Rate limited",
        response=SimpleNamespace(
            status_code=429,
            headers={"retry-after": "1"},
            request=SimpleNamespace(method="POST", url="https://api.anthropic.com"),
        ),
        body=None,
    )
    # Fail twice with rate limit, succeed on third
    mock_create = AsyncMock(
        side_effect=[
            rate_limit_error,
            rate_limit_error,
            _make_tool_use_response(VALID_TOOL_INPUT),
        ]
    )
    monkeypatch.setattr(
        "app.backend.services.classifier.anthropic.AsyncAnthropic",
        lambda **kwargs: SimpleNamespace(messages=SimpleNamespace(create=mock_create)),
    )

    result = await classify_image("/fake/path.jpg")
    assert isinstance(result, GarmentClassification)
    assert result.garment_type == "Dress"
    assert mock_create.call_count == 3

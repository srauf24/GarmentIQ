import asyncio
import base64
import logging
import time
from pathlib import Path

import anthropic

from app.backend.core.config import settings
from app.backend.models.schemas import GarmentClassification, LocationContext

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert fashion analyst working with a design team.
Analyze garment photos with the eye of a senior fashion designer who has
studied textile construction, global fashion trends, and retail merchandising.

When analyzing an image:
- Identify the PRIMARY garment. If multiple garments are visible, focus on
  the most prominent one.
- Be specific about materials based on visual texture, sheen, and drape.
- Note construction details: stitching, embellishments, hardware, closures.
- For location, ONLY infer geography from visible cues (signs, architecture,
  vegetation, text, distinctive landmarks). Do NOT guess without evidence.
  Set confidence appropriately.
- For designer_brand, ONLY identify if you can see logos, tags, or highly
  distinctive design signatures. Return null otherwise.
- Connect the garment to current or recent fashion trends with specific
  references.
"""


class ClassificationError(Exception):
    """Raised when Claude API is completely unreachable after retries."""

    pass


def _build_tool_definition() -> dict:
    """Convert GarmentClassification Pydantic model to Claude tool schema."""
    return {
        "name": "classify_garment",
        "description": (
            "Classify a fashion garment image by extracting structured "
            "attributes and providing a rich description."
        ),
        "input_schema": GarmentClassification.model_json_schema(),
    }


def _encode_image(image_path: str) -> tuple[str, str]:
    """Read image file, return (base64_data, media_type)."""
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "image/jpeg")
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return data, media_type


def _build_fallback(raw_text: str = "") -> GarmentClassification:
    """Return a classification with defaults when parsing fails."""
    return GarmentClassification(
        description=raw_text
        or "Classification could not be completed. Manual review recommended.",
        garment_type="Unclassified",
        style="Unclassified",
        material="Unclassified",
        color_palette=["Unknown"],
        pattern="Unclassified",
        season="All-Season",
        occasion="Unclassified",
        consumer_profile="Unclassified",
        designer_brand=None,
        trend_notes="Unable to classify — manual review recommended.",
        location=LocationContext(),
    )


async def classify_image(image_path: str) -> GarmentClassification:
    """Send an image to Claude Vision, get structured classification.

    Uses tool_use to force structured output. Retries up to 3 times
    on API errors. Returns fallback classification if all attempts fail
    to produce valid structured data.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    image_data, media_type = _encode_image(image_path)
    tool_def = _build_tool_definition()

    for attempt in range(settings.claude_max_retries):
        try:
            start = time.time()
            logger.info(
                "Classifying image",
                extra={"filename": Path(image_path).name, "attempt": attempt + 1},
            )

            response = await client.messages.create(
                model=settings.claude_model,
                max_tokens=1536,
                system=SYSTEM_PROMPT,
                tools=[tool_def],
                tool_choice={"type": "tool", "name": "classify_garment"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Analyze this fashion/garment image. "
                                "Classify it using the provided tool.",
                            },
                        ],
                    }
                ],
            )

            elapsed = time.time() - start
            logger.info(
                "Claude response received",
                extra={"elapsed_sec": round(elapsed, 2), "attempt": attempt + 1},
            )

            # Find the tool_use content block
            tool_block = None
            for block in response.content:
                if block.type == "tool_use":
                    tool_block = block
                    break

            if tool_block is None:
                logger.warning(
                    "No tool_use block in response, attempt %d", attempt + 1
                )
                continue

            # Parse with Pydantic
            result = GarmentClassification.model_validate(tool_block.input)
            return result

        except anthropic.RateLimitError as e:
            wait = 2**attempt
            logger.warning(
                "Rate limited, waiting %ds", wait, extra={"error": str(e)}
            )
            await asyncio.sleep(wait)

        except anthropic.APIError as e:
            logger.error(
                "Claude API error", extra={"error": str(e), "attempt": attempt + 1}
            )
            if attempt < settings.claude_max_retries - 1:
                await asyncio.sleep(2**attempt)
            else:
                raise ClassificationError(
                    f"Claude API failed after {settings.claude_max_retries} attempts: {e}"
                )

        except Exception as e:
            logger.error(
                "Unexpected error during classification",
                extra={"error": str(e)},
            )
            if attempt < settings.claude_max_retries - 1:
                continue
            return _build_fallback()

    return _build_fallback()

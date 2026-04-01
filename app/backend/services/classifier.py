from app.backend.models.schemas import GarmentClassification


class ClassificationError(Exception):
    """Raised when Claude API fails after retries."""

    pass


async def classify_image(file_path: str) -> GarmentClassification:
    """Classify a garment image using Claude Vision.

    Real implementation will be added in TG-004.
    """
    raise NotImplementedError("Classifier not yet implemented")

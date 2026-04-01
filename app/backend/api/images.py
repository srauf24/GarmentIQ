import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from sqlalchemy import extract, func, or_
from sqlalchemy.orm import Session

from app.backend.core.config import settings
from app.backend.models.database import Annotation, Image, get_db
from app.backend.models.schemas import (
    AnnotationResponse,
    ImageResponse,
    LocationResponse,
    PaginatedResponse,
)
from app.backend.services.classifier import ClassificationError, classify_image

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/images", tags=["images"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _image_to_response(image: Image) -> ImageResponse:
    """Convert SQLAlchemy Image to Pydantic ImageResponse."""
    return ImageResponse(
        id=image.id,
        filename=image.filename,
        original_filename=image.original_filename,
        image_url=f"/uploads/{image.filename}",
        ai_description=image.ai_description,
        garment_type=image.garment_type,
        style=image.style,
        material=image.material,
        color_palette=image.color_palette,
        pattern=image.pattern,
        season=image.season,
        occasion=image.occasion,
        consumer_profile=image.consumer_profile,
        designer_brand=image.designer_brand,
        trend_notes=image.trend_notes,
        location=LocationResponse(
            environment=image.location_environment,
            inferred_geo=image.location_inferred_geo,
            confidence=image.location_confidence,
            continent=image.location_continent,
            country=image.location_country,
            city=image.location_city,
        ),
        uploaded_by=image.uploaded_by,
        created_at=image.created_at,
        annotations=[
            AnnotationResponse.model_validate(a) for a in image.annotations
        ],
    )


@router.get("", response_model=PaginatedResponse[ImageResponse])
async def list_images(
    garment_type: str | None = Query(None),
    style: str | None = Query(None),
    material: str | None = Query(None),
    pattern: str | None = Query(None),
    season: str | None = Query(None),
    occasion: str | None = Query(None),
    consumer_profile: str | None = Query(None),
    designer_brand: str | None = Query(None),
    location_continent: str | None = Query(None),
    location_country: str | None = Query(None),
    location_city: str | None = Query(None),
    year: int | None = Query(None),
    month: int | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ImageResponse]:
    """List images with optional filters, search, and pagination."""
    query = db.query(Image)

    # Apply attribute filters
    filter_map = {
        "garment_type": garment_type,
        "style": style,
        "material": material,
        "pattern": pattern,
        "season": season,
        "occasion": occasion,
        "consumer_profile": consumer_profile,
        "designer_brand": designer_brand,
        "location_continent": location_continent,
        "location_country": location_country,
        "location_city": location_city,
    }
    for col_name, value in filter_map.items():
        if value is not None:
            query = query.filter(getattr(Image, col_name) == value)

    # Time filters
    if year is not None:
        query = query.filter(extract("year", Image.created_at) == year)
    if month is not None:
        query = query.filter(extract("month", Image.created_at) == month)

    # Full-text search (images + annotations)
    if q:
        ts_query = func.plainto_tsquery("english", q)

        # Subquery: find image_ids where annotation note or tags match
        annotation_image_ids = (
            db.query(Annotation.image_id)
            .filter(
                or_(
                    func.to_tsvector("english", Annotation.note).op("@@")(ts_query),
                    Annotation.tags.any(q),
                )
            )
            .distinct()
            .subquery()
        )

        # Image matches if its own search_vector OR any annotation matches
        query = query.filter(
            or_(
                Image.search_vector.op("@@")(ts_query),
                Image.id.in_(annotation_image_ids),
            )
        )

    # Count before pagination
    total = query.count()

    # Paginate
    query = query.order_by(Image.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    images = query.all()

    return PaginatedResponse(
        items=[_image_to_response(img) for img in images],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.post("/upload", response_model=ImageResponse, status_code=201)
async def upload_image(
    file: UploadFile,
    uploaded_by: str = Form(default=None),
    location_country: str = Form(default=None),
    location_city: str = Form(default=None),
    db: Session = Depends(get_db),
) -> ImageResponse:
    """Upload an image, classify with Claude, persist to DB."""

    # 1. Validate file type
    ext = Path(file.filename or "unknown.jpg").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400, f"File type {ext} not allowed. Use: {ALLOWED_EXTENSIONS}"
        )

    # 2. Save file to disk
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    file_path = os.path.join(settings.upload_dir, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info("Saved upload", extra={"filename": filename, "size_bytes": len(content)})

    # 3. Classify with Claude
    try:
        classification = await classify_image(file_path)
    except ClassificationError as e:
        raise HTTPException(502, f"Classification failed: {e}")

    # 4. Merge location: prefer manual input, fill from AI where missing
    loc = classification.location
    final_country = location_country or (loc.inferred_country if loc else None)
    final_city = location_city or (loc.inferred_city if loc else None)
    final_continent = loc.inferred_continent if loc else None

    # Build inferred_geo string for display
    inferred_parts = []
    if loc and loc.inferred_city:
        inferred_parts.append(loc.inferred_city)
    if loc and loc.inferred_country:
        inferred_parts.append(loc.inferred_country)
    inferred_geo = ", ".join(inferred_parts) or None

    # 5. Create DB record
    db_image = Image(
        filename=filename,
        original_filename=file.filename or "unknown",
        file_path=file_path,
        ai_description=classification.description,
        garment_type=classification.garment_type,
        style=classification.style,
        material=classification.material,
        color_palette=classification.color_palette,
        pattern=classification.pattern,
        season=classification.season,
        occasion=classification.occasion,
        consumer_profile=classification.consumer_profile,
        designer_brand=classification.designer_brand,
        trend_notes=classification.trend_notes,
        location_environment=loc.environment if loc else None,
        location_inferred_geo=inferred_geo,
        location_confidence=loc.confidence if loc else None,
        location_continent=final_continent,
        location_country=final_country,
        location_city=final_city,
        uploaded_by=uploaded_by,
    )

    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    logger.info("Image record created", extra={"image_id": str(db_image.id)})

    return _image_to_response(db_image)

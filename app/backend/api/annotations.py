from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.models.database import Annotation, Image, get_db
from app.backend.models.schemas import AnnotationCreate, AnnotationResponse

router = APIRouter(prefix="/api/images", tags=["annotations"])


@router.post(
    "/{image_id}/annotations", response_model=AnnotationResponse, status_code=201
)
async def create_annotation(
    image_id: UUID,
    body: AnnotationCreate,
    db: Session = Depends(get_db),
) -> AnnotationResponse:
    """Add a designer annotation to an image."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(404, "Image not found")

    annotation = Annotation(
        image_id=image_id,
        note=body.note,
        tags=body.tags,
        created_by=body.created_by,
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return AnnotationResponse.model_validate(annotation)


@router.delete("/{image_id}/annotations/{annotation_id}", status_code=204)
async def delete_annotation(
    image_id: UUID,
    annotation_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Remove a designer annotation."""
    annotation = (
        db.query(Annotation)
        .filter(Annotation.id == annotation_id, Annotation.image_id == image_id)
        .first()
    )
    if not annotation:
        raise HTTPException(404, "Annotation not found")

    db.delete(annotation)
    db.commit()

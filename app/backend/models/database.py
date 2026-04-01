import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Column,
    Float,
    ForeignKey,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from app.backend.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)

    # AI-generated classification
    ai_description = Column(Text)
    garment_type = Column(String(100))
    style = Column(String(100))
    material = Column(String(100))
    color_palette = Column(ARRAY(Text))
    pattern = Column(String(100))
    season = Column(String(50))
    occasion = Column(String(100))
    consumer_profile = Column(String(200))
    designer_brand = Column(String(200))
    trend_notes = Column(Text)

    # Location: AI-inferred
    location_environment = Column(String(100))
    location_inferred_geo = Column(String(200))
    location_confidence = Column(Float)

    # Location: used for filters
    location_continent = Column(String(50))
    location_country = Column(String(100))
    location_city = Column(String(100))

    # Upload metadata
    uploaded_by = Column(String(100))
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    annotations = relationship(
        "Annotation",
        back_populates="image",
        cascade="all, delete-orphan",
        order_by="Annotation.created_at.desc()",
    )


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
    )
    note = Column(Text)
    tags = Column(ARRAY(Text))
    created_by = Column(String(100))
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    image = relationship("Image", back_populates="annotations")


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

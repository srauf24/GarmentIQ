"""Unit tests for SQLAlchemy models."""

from unittest.mock import patch

from sqlalchemy.dialects.postgresql import UUID

from app.backend.models.database import Annotation, Image, get_db


def test_image_table_name() -> None:
    assert Image.__tablename__ == "images"


def test_annotation_table_name() -> None:
    assert Annotation.__tablename__ == "annotations"


def test_image_has_all_columns() -> None:
    expected = [
        "id",
        "filename",
        "original_filename",
        "file_path",
        "ai_description",
        "garment_type",
        "style",
        "material",
        "color_palette",
        "pattern",
        "season",
        "occasion",
        "consumer_profile",
        "designer_brand",
        "trend_notes",
        "location_environment",
        "location_inferred_geo",
        "location_confidence",
        "location_continent",
        "location_country",
        "location_city",
        "uploaded_by",
        "created_at",
    ]
    actual = list(Image.__table__.columns.keys())
    for col in expected:
        assert col in actual, f"Missing column: {col}"


def test_annotation_has_all_columns() -> None:
    expected = ["id", "image_id", "note", "tags", "created_by", "created_at"]
    actual = list(Annotation.__table__.columns.keys())
    for col in expected:
        assert col in actual, f"Missing column: {col}"


def test_image_primary_key_is_uuid() -> None:
    col = Image.__table__.c.id
    assert col.primary_key
    assert isinstance(col.type, UUID)


def test_annotation_foreign_key_references_images() -> None:
    col = Annotation.__table__.c.image_id
    fk = list(col.foreign_keys)[0]
    assert fk.target_fullname == "images.id"


def test_image_has_annotations_relationship() -> None:
    assert "annotations" in Image.__mapper__.relationships


def test_annotation_has_image_relationship() -> None:
    assert "image" in Annotation.__mapper__.relationships


def test_get_db_yields_and_closes_session() -> None:
    with patch("app.backend.models.database.SessionLocal") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        gen = get_db()
        session = next(gen)
        assert session is mock_session
        try:
            next(gen)
        except StopIteration:
            pass
        mock_session.close.assert_called_once()

"""Shared test fixtures for integration and e2e tests.

These fixtures connect to the real PostgreSQL database (Docker db service)
and use transactional rollback to isolate each test.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.backend.core.config import settings
from app.backend.models.database import Annotation, Base, Image, get_db

engine = create_engine(settings.database_url)
TestSession = sessionmaker(bind=engine)

# SQL for the search_vector trigger (not created by Base.metadata.create_all)
TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.ai_description, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.trend_notes, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.garment_type, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.style, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.material, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.pattern, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.season, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.occasion, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.designer_brand, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trig_update_search_vector ON images;
CREATE TRIGGER trig_update_search_vector
    BEFORE INSERT OR UPDATE ON images
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();
"""


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create tables and triggers once per test session."""
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(text(TRIGGER_SQL))
        conn.commit()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    """Provide a transactional test DB session — rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSession(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """FastAPI test client with overridden DB dependency."""
    from app.backend.main import app

    def _get_test_db():
        yield db

    app.dependency_overrides[get_db] = _get_test_db
    from starlette.testclient import TestClient

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_images(db):
    """Insert 5 known images for filter testing."""
    images = [
        Image(
            filename="test1.jpg",
            original_filename="dress1.jpg",
            file_path="/uploads/test1.jpg",
            ai_description="A flowing silk midi dress with floral embroidery",
            garment_type="Dress",
            style="Bohemian",
            material="Silk",
            color_palette=["Green", "Gold"],
            pattern="Floral",
            season="Spring",
            occasion="Casual Daily",
            consumer_profile="Young Professional",
            location_continent="Asia",
            location_country="Japan",
            location_city="Tokyo",
            uploaded_by="Alice",
            created_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        ),
        Image(
            filename="test2.jpg",
            original_filename="jacket1.jpg",
            file_path="/uploads/test2.jpg",
            ai_description="A classic black leather biker jacket with silver zippers",
            garment_type="Jacket",
            style="Streetwear",
            material="Leather",
            color_palette=["Black", "Silver"],
            pattern="Solid",
            season="Fall",
            occasion="Casual Daily",
            consumer_profile="Trend-Forward Teen",
            location_continent="Europe",
            location_country="France",
            location_city="Paris",
            uploaded_by="Bob",
            created_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
        ),
        Image(
            filename="test3.jpg",
            original_filename="suit1.jpg",
            file_path="/uploads/test3.jpg",
            ai_description="A tailored navy wool suit with subtle pinstripes",
            garment_type="Suit",
            style="Formal",
            material="Wool",
            color_palette=["Navy Blue"],
            pattern="Striped",
            season="Winter",
            occasion="Business",
            consumer_profile="Classic Adult",
            location_continent="Europe",
            location_country="Italy",
            location_city="Milan",
            uploaded_by="Alice",
            created_at=datetime(2025, 11, 5, tzinfo=timezone.utc),
        ),
        Image(
            filename="test4.jpg",
            original_filename="top1.jpg",
            file_path="/uploads/test4.jpg",
            ai_description="A casual cotton t-shirt with minimalist screen print",
            garment_type="Top",
            style="Casual",
            material="Cotton",
            color_palette=["White", "Black"],
            pattern="Geometric",
            season="Summer",
            occasion="Casual Daily",
            consumer_profile="Young Professional",
            location_continent="North America",
            location_country="USA",
            location_city="New York",
            uploaded_by="Alice",
            created_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
        ),
        Image(
            filename="test5.jpg",
            original_filename="skirt1.jpg",
            file_path="/uploads/test5.jpg",
            ai_description="An artisan handmade linen skirt from a local market",
            garment_type="Skirt",
            style="Bohemian",
            material="Linen",
            color_palette=["Beige", "Brown"],
            pattern="Solid",
            season="Spring",
            occasion="Casual Daily",
            consumer_profile="Eco-Conscious Consumer",
            location_continent="Asia",
            location_country="India",
            location_city="Jaipur",
            uploaded_by="Carol",
            created_at=datetime(2026, 2, 14, tzinfo=timezone.utc),
        ),
    ]
    for img in images:
        db.add(img)
    db.flush()

    annotation = Annotation(
        image_id=images[4].id,
        note="Similar to pieces seen at Jaipur artisan market",
        tags=["artisan", "handmade", "market"],
        created_by="Carol",
    )
    db.add(annotation)
    db.commit()

    return images

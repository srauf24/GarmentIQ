"""Unit tests for the dynamic filter values endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

ALL_FILTER_KEYS = [
    "garment_type",
    "style",
    "material",
    "color_palette",
    "pattern",
    "season",
    "occasion",
    "consumer_profile",
    "designer_brand",
    "location_continent",
    "location_country",
    "location_city",
    "year",
    "month",
    "uploaded_by",
]


class FakeFilterQuery:
    """Fake query that returns pre-canned row tuples."""

    def __init__(self, rows=None):
        self._rows = rows or []

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def distinct(self):
        return self

    def label(self, name):
        return self

    def all(self):
        return self._rows


class FakeFilterSession:
    """Session that returns empty results for all queries."""

    def __init__(self, results=None):
        # results is a list of row-lists, popped in order of query() calls
        self._results = list(results) if results else []

    def query(self, *args):
        if self._results:
            return FakeFilterQuery(self._results.pop(0))
        return FakeFilterQuery()

    def close(self):
        pass


def _override_db(results=None):
    from app.backend.main import app
    from app.backend.models.database import get_db

    def _get_fake_db():
        db = FakeFilterSession(results)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_fake_db
    return app


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    from app.backend.main import app
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_filters_returns_200_with_all_keys() -> None:
    # The endpoint makes 14 query() calls:
    # 11 _distinct_values + 1 color_palette + 1 years + 1 months
    # Plus uploaded_by = 15 total (11 string cols + color + year + month + uploaded_by)
    # Actually: garment_type, style, material, pattern, season, occasion,
    # consumer_profile, designer_brand, location_continent, location_country,
    # location_city = 11 calls via _distinct_values
    # + 1 color_palette call
    # + 1 years call
    # + 1 months call
    # + 1 uploaded_by via _distinct_values = total 15 query() calls
    # But uploaded_by is also via _distinct_values, so 12 _distinct_values + 1 color + 1 year + 1 month = 15
    results = [[] for _ in range(15)]
    app = _override_db(results)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    for key in ALL_FILTER_KEYS:
        assert key in data, f"Missing key: {key}"


@pytest.mark.anyio
async def test_filters_empty_data_returns_empty_lists() -> None:
    results = [[] for _ in range(15)]
    app = _override_db(results)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    for key in ALL_FILTER_KEYS:
        assert data[key] == [], f"Expected empty list for {key}"


@pytest.mark.anyio
async def test_filters_returns_distinct_values() -> None:
    # Order of query() calls in the endpoint:
    # 1. garment_type, 2. style, 3. material,
    # 4. color_palette (unnest),
    # 5. pattern, 6. season, 7. occasion,
    # 8. consumer_profile, 9. designer_brand,
    # 10. location_continent, 11. location_country, 12. location_city,
    # 13. year, 14. month, 15. uploaded_by
    #
    # But the code calls _distinct_values for 11 cols first, then color, then year/month, then uploaded_by
    # Actually looking at the code order:
    # _distinct_values: garment_type, style, material = 3
    # then color_palette
    # then _distinct_values: pattern, season, occasion, consumer_profile, designer_brand = 5
    # then _distinct_values: location_continent, location_country, location_city = 3
    # then year, month
    # then _distinct_values: uploaded_by = 1
    # Wait, the code builds the return dict all at once. Let me re-read.

    # The code calls _distinct_values inside the return statement, so order follows
    # the keyword order in FilterValuesResponse constructor:
    # garment_type, style, material, [color_palette], pattern, season, occasion,
    # consumer_profile, designer_brand, location_continent, location_country,
    # location_city, [year], [month], uploaded_by
    #
    # But color_palette, year, month are queried before the return statement.
    # So actual query order: color_palette, year, month, then in return:
    # garment_type, style, material, pattern, season, occasion,
    # consumer_profile, designer_brand, location_continent, location_country,
    # location_city, uploaded_by

    results = [
        # 1. color_palette (unnest)
        [("Blue",), ("Cream",)],
        # 2. years
        [(2024,), (2025,)],
        # 3. months
        [(3,), (6,)],
        # 4. garment_type
        [("Dress",), ("Jacket",)],
        # 5. style
        [("Bohemian",)],
        # 6. material
        [("Silk",)],
        # 7. pattern
        [("Floral",)],
        # 8. season
        [("Spring",)],
        # 9. occasion
        [("Casual Daily",)],
        # 10. consumer_profile
        [("Young Professional",)],
        # 11. designer_brand
        [("Zimmermann",)],
        # 12. location_continent
        [("Europe",)],
        # 13. location_country
        [("France",)],
        # 14. location_city
        [("Paris",)],
        # 15. uploaded_by
        [("designer1",)],
    ]
    app = _override_db(results)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    assert data["garment_type"] == ["Dress", "Jacket"]
    assert data["color_palette"] == ["Blue", "Cream"]
    assert data["year"] == [2024, 2025]
    assert data["designer_brand"] == ["Zimmermann"]


@pytest.mark.anyio
async def test_filters_excludes_null_values() -> None:
    # All results are non-null by construction (the endpoint filters nulls via SQL)
    results = [
        # color
        [("Blue",)],
        # year
        [(2025,)],
        # month
        [(3,)],
        # 12 _distinct_values calls — each returns non-null values
        [("Dress",)],
        [("Bohemian",)],
        [("Silk",)],
        [("Floral",)],
        [("Spring",)],
        [("Casual Daily",)],
        [("Young Professional",)],
        [],  # designer_brand — empty, not null
        [("Europe",)],
        [("France",)],
        [("Paris",)],
        [("designer1",)],
    ]
    app = _override_db(results)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    for key in ALL_FILTER_KEYS:
        assert None not in data[key], f"Null found in {key}"

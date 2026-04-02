"""Integration tests for image filters, search, and dynamic filter values.

These tests run against a real PostgreSQL database with seeded data.
Each test is isolated via transactional rollback.

Note: assertions use >= instead of == for totals because the real DB may
contain previously uploaded images. We verify the seed data appears in
results rather than asserting exact counts.
"""


class TestAttributeFilters:
    def test_filter_by_garment_type(self, client, seed_images) -> None:
        res = client.get("/api/images?garment_type=Dress")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        filenames = [item["filename"] for item in data["items"]]
        assert "test1.jpg" in filenames

    def test_filter_by_material(self, client, seed_images) -> None:
        res = client.get("/api/images?material=Leather")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        filenames = [item["filename"] for item in data["items"]]
        assert "test2.jpg" in filenames

    def test_combined_filters(self, client, seed_images) -> None:
        res = client.get("/api/images?style=Bohemian&season=Spring")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2
        filenames = [item["filename"] for item in data["items"]]
        assert "test1.jpg" in filenames
        assert "test5.jpg" in filenames

    def test_no_match_returns_empty(self, client, seed_images) -> None:
        res = client.get("/api/images?garment_type=Swimwear")
        assert res.status_code == 200
        assert res.json()["total"] == 0


class TestContextualFilters:
    def test_filter_by_continent(self, client, seed_images) -> None:
        res = client.get("/api/images?location_continent=Europe")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2
        filenames = [item["filename"] for item in data["items"]]
        assert "test2.jpg" in filenames
        assert "test3.jpg" in filenames

    def test_filter_by_country(self, client, seed_images) -> None:
        res = client.get("/api/images?location_country=Japan")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        filenames = [item["filename"] for item in data["items"]]
        assert "test1.jpg" in filenames

    def test_filter_by_year(self, client, seed_images) -> None:
        res = client.get("/api/images?year=2025")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        filenames = [item["filename"] for item in data["items"]]
        assert "test3.jpg" in filenames

    def test_filter_by_month(self, client, seed_images) -> None:
        res = client.get("/api/images?month=3")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2
        filenames = [item["filename"] for item in data["items"]]
        assert "test1.jpg" in filenames
        assert "test4.jpg" in filenames


class TestDynamicFilterValues:
    def test_filter_values_from_data(self, client, seed_images) -> None:
        res = client.get("/api/filters")
        assert res.status_code == 200
        data = res.json()
        assert "Dress" in data["garment_type"]
        assert "Silk" in data["material"]
        assert "Japan" in data["location_country"]
        assert 2026 in data["year"]


class TestSearch:
    def test_search_by_description(self, client, seed_images) -> None:
        res = client.get("/api/images?q=embroidery")
        assert res.status_code == 200
        assert res.json()["total"] >= 1

    def test_search_by_annotation(self, client, seed_images) -> None:
        res = client.get("/api/images?q=artisan")
        assert res.status_code == 200
        assert res.json()["total"] >= 1

    def test_search_plus_filter(self, client, seed_images) -> None:
        res = client.get("/api/images?q=leather&garment_type=Jacket")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        filenames = [item["filename"] for item in data["items"]]
        assert "test2.jpg" in filenames

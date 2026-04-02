from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# --- Claude Classification Schema (tool_use) ---


class LocationContext(BaseModel):
    environment: str | None = Field(
        None,
        description="Setting where the garment was photographed: "
        "e.g., 'Urban Street', 'Retail Store', 'Market Stall', 'Runway'",
    )
    inferred_country: str | None = Field(
        None,
        description="Country inferred from visual cues such as signs, architecture, "
        "or text visible in the image. Return null if not determinable.",
    )
    inferred_city: str | None = Field(
        None,
        description="City inferred from visual cues. Return null if not determinable.",
    )
    inferred_continent: str | None = Field(
        None,
        description="Continent inferred from visual cues. Return null if not determinable.",
    )
    confidence: float | None = Field(
        None,
        description="Confidence in geographic inference from 0.0 (pure guess) "
        "to 1.0 (certain, e.g., visible sign with city name).",
        ge=0.0,
        le=1.0,
    )


class GarmentClassification(BaseModel):
    """Schema used as Claude tool_use definition. Every Field description
    is sent to Claude as part of the tool schema — write them carefully."""

    description: str = Field(
        ...,
        description="Rich 2-3 sentence natural language description of the garment, "
        "covering construction details, visual impact, fabric drape, "
        "and styling context.",
    )
    garment_type: str = Field(
        ...,
        description="Primary garment category. Examples: 'Dress', 'Jacket', "
        "'Trousers', 'Blouse', 'Skirt', 'Coat', 'Knitwear', "
        "'Suit', 'Activewear', 'Accessories', 'Top'",
    )
    style: str = Field(
        ...,
        description="Overall design aesthetic. Examples: 'Bohemian', 'Minimalist', "
        "'Streetwear', 'Formal', 'Casual', 'Vintage', 'Avant-garde', "
        "'Classic', 'Preppy', 'Athleisure', 'Romantic'",
    )
    material: str = Field(
        ...,
        description="Primary visible material/fabric based on texture and drape. "
        "Examples: 'Cotton', 'Silk', 'Denim', 'Leather', 'Wool', "
        "'Synthetic', 'Linen', 'Knit', 'Velvet', 'Polyester'",
    )
    color_palette: list[str] = Field(
        ...,
        description="List of 1-4 dominant colors visible. Use descriptive color "
        "names, e.g., ['Navy Blue', 'Cream', 'Gold'] not hex codes.",
    )
    pattern: str = Field(
        ...,
        description="Pattern type. Examples: 'Solid', 'Striped', 'Floral', "
        "'Plaid', 'Geometric', 'Abstract', 'Animal Print', 'Polka Dot'",
    )
    season: str = Field(
        ...,
        description="Most appropriate season for wearing: 'Spring', 'Summer', "
        "'Fall', 'Winter', or 'All-Season'",
    )
    occasion: str = Field(
        ...,
        description="Best-fit occasion. Examples: 'Casual Daily', 'Business', "
        "'Evening/Formal', 'Active/Sport', 'Festival', 'Beach', "
        "'Smart Casual'",
    )
    consumer_profile: str = Field(
        ...,
        description="Target consumer persona. Examples: 'Young Professional', "
        "'Luxury Shopper', 'Eco-Conscious Consumer', "
        "'Trend-Forward Teen', 'Classic Adult'",
    )
    designer_brand: str | None = Field(
        None,
        description="Brand or designer name ONLY if identifiable from logos, "
        "tags, or highly distinctive design signatures visible in "
        "the image. Return null if not identifiable.",
    )
    trend_notes: str = Field(
        ...,
        description="1-2 sentences connecting this garment to current or recent "
        "fashion trends. E.g., 'Part of the oversized silhouette trend "
        "prominent in 2024-2025 streetwear collections.'",
    )
    location: LocationContext = Field(
        default_factory=LocationContext,
        description="Location context inferred from visual cues in the image",
    )


# --- API Response Schemas ---


class AnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_id: UUID
    note: str | None
    tags: list[str] | None
    created_by: str | None
    created_at: datetime


class LocationResponse(BaseModel):
    environment: str | None = None
    inferred_geo: str | None = None
    confidence: float | None = None
    continent: str | None = None
    country: str | None = None
    city: str | None = None


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    original_filename: str
    image_url: str
    ai_description: str | None
    garment_type: str | None
    style: str | None
    material: str | None
    color_palette: list[str] | None
    pattern: str | None
    season: str | None
    occasion: str | None
    consumer_profile: str | None
    designer_brand: str | None
    trend_notes: str | None
    location: LocationResponse
    uploaded_by: str | None
    created_at: datetime
    annotations: list[AnnotationResponse]


# --- API Request Schemas ---


class AnnotationCreate(BaseModel):
    note: str | None = None
    tags: list[str] | None = None
    created_by: str | None = None


# --- Pagination ---


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Filter Values ---


class FilterValuesResponse(BaseModel):
    garment_type: list[str]
    style: list[str]
    material: list[str]
    color_palette: list[str]
    pattern: list[str]
    season: list[str]
    occasion: list[str]
    consumer_profile: list[str]
    designer_brand: list[str]
    location_continent: list[str]
    location_country: list[str]
    location_city: list[str]
    year: list[int]
    month: list[int]
    uploaded_by: list[str]

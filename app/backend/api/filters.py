from fastapi import APIRouter, Depends
from sqlalchemy import Integer, distinct, extract, func
from sqlalchemy.orm import Session

from app.backend.models.database import Image, get_db
from app.backend.models.schemas import FilterValuesResponse

router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.get("", response_model=FilterValuesResponse)
async def get_filter_values(
    db: Session = Depends(get_db),
) -> FilterValuesResponse:
    """Return distinct values for each filterable field from actual data."""

    def _distinct_values(column) -> list[str]:
        """Get sorted non-null distinct values for a string column."""
        rows = (
            db.query(distinct(column))
            .filter(column.isnot(None))
            .order_by(column)
            .all()
        )
        return [row[0] for row in rows]

    # Flatten color_palette arrays across all images
    color_rows = (
        db.query(func.unnest(Image.color_palette).label("color"))
        .filter(Image.color_palette.isnot(None))
        .distinct()
        .order_by("color")
        .all()
    )
    color_values = [row[0] for row in color_rows]

    # Year and month from created_at
    year_col = func.cast(extract("year", Image.created_at), Integer)
    month_col = func.cast(extract("month", Image.created_at), Integer)

    years = db.query(distinct(year_col)).order_by(year_col).all()
    months = db.query(distinct(month_col)).order_by(month_col).all()

    return FilterValuesResponse(
        garment_type=_distinct_values(Image.garment_type),
        style=_distinct_values(Image.style),
        material=_distinct_values(Image.material),
        color_palette=color_values,
        pattern=_distinct_values(Image.pattern),
        season=_distinct_values(Image.season),
        occasion=_distinct_values(Image.occasion),
        consumer_profile=_distinct_values(Image.consumer_profile),
        designer_brand=_distinct_values(Image.designer_brand),
        location_continent=_distinct_values(Image.location_continent),
        location_country=_distinct_values(Image.location_country),
        location_city=_distinct_values(Image.location_city),
        year=[int(r[0]) for r in years],
        month=[int(r[0]) for r in months],
        uploaded_by=_distinct_values(Image.uploaded_by),
    )

import type { ImageFilters } from "../../types";

const HIDDEN_KEYS = new Set(["page", "page_size", "search"]);

const LABEL_MAP: Record<string, string> = {
  garment_type: "Type",
  style: "Style",
  material: "Material",
  color_palette: "Color",
  pattern: "Pattern",
  season: "Season",
  occasion: "Occasion",
  consumer_profile: "Consumer",
  designer_brand: "Brand",
  location_continent: "Continent",
  location_country: "Country",
  location_city: "City",
  year: "Year",
  month: "Month",
  uploaded_by: "Uploaded by",
};

interface ActiveFiltersProps {
  filters: ImageFilters;
  onRemove: (key: keyof ImageFilters) => void;
  onClearAll: () => void;
}

export function ActiveFilters({
  filters,
  onRemove,
  onClearAll,
}: ActiveFiltersProps) {
  const active = Object.entries(filters).filter(
    ([key, val]) => val !== undefined && !HIDDEN_KEYS.has(key),
  );

  if (active.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {active.map(([key, val]) => (
        <span
          key={key}
          className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-1
                     text-xs text-blue-700"
        >
          {LABEL_MAP[key] || key}: {String(val)}
          <button
            type="button"
            onClick={() => onRemove(key as keyof ImageFilters)}
            className="hover:text-blue-900"
            aria-label={`Remove ${LABEL_MAP[key] || key} filter`}
          >
            &times;
          </button>
        </span>
      ))}
      <button
        type="button"
        onClick={onClearAll}
        className="ml-2 text-xs text-gray-500 hover:text-gray-700"
      >
        Clear all
      </button>
    </div>
  );
}

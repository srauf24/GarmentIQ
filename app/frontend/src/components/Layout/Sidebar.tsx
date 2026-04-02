import { FilterGroup } from "../Filters/FilterGroup";
import { useFilterValues } from "../../hooks/useFilterValues";
import type { ImageFilters } from "../../types";

interface SidebarProps {
  filters: ImageFilters;
  onFilterChange: (
    key: keyof ImageFilters,
    value: string | number | undefined,
  ) => void;
}

export function Sidebar({ filters, onFilterChange }: SidebarProps) {
  const { data, isLoading } = useFilterValues();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-1">
            <div className="h-3 w-20 animate-pulse rounded bg-gray-200" />
            <div className="h-8 w-full animate-pulse rounded bg-gray-200" />
          </div>
        ))}
      </div>
    );
  }

  if (!data) return null;

  function handleStringFilter(key: keyof ImageFilters) {
    return (value: string | undefined) => onFilterChange(key, value);
  }

  function handleNumberFilter(key: keyof ImageFilters) {
    return (value: string | undefined) =>
      onFilterChange(key, value ? Number(value) : undefined);
  }

  return (
    <nav className="space-y-6 overflow-y-auto" aria-label="Filters">
      {/* Garment Attributes */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">
          Garment Attributes
        </h3>
        <div className="space-y-3">
          <FilterGroup
            label="Type"
            options={data.garment_type}
            value={filters.garment_type}
            onChange={handleStringFilter("garment_type")}
          />
          <FilterGroup
            label="Style"
            options={data.style}
            value={filters.style}
            onChange={handleStringFilter("style")}
          />
          <FilterGroup
            label="Material"
            options={data.material}
            value={filters.material}
            onChange={handleStringFilter("material")}
          />
          <FilterGroup
            label="Pattern"
            options={data.pattern}
            value={filters.pattern}
            onChange={handleStringFilter("pattern")}
          />
          <FilterGroup
            label="Season"
            options={data.season}
            value={filters.season}
            onChange={handleStringFilter("season")}
          />
          <FilterGroup
            label="Occasion"
            options={data.occasion}
            value={filters.occasion}
            onChange={handleStringFilter("occasion")}
          />
          <FilterGroup
            label="Consumer Profile"
            options={data.consumer_profile}
            value={filters.consumer_profile}
            onChange={handleStringFilter("consumer_profile")}
          />
          <FilterGroup
            label="Brand"
            options={data.designer_brand}
            value={filters.designer_brand}
            onChange={handleStringFilter("designer_brand")}
          />
        </div>
      </div>

      {/* Context */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">
          Context
        </h3>
        <div className="space-y-3">
          <FilterGroup
            label="Continent"
            options={data.location_continent}
            value={filters.location_continent}
            onChange={handleStringFilter("location_continent")}
          />
          <FilterGroup
            label="Country"
            options={data.location_country}
            value={filters.location_country}
            onChange={handleStringFilter("location_country")}
          />
          <FilterGroup
            label="City"
            options={data.location_city}
            value={filters.location_city}
            onChange={handleStringFilter("location_city")}
          />
          <FilterGroup
            label="Year"
            options={data.year.map(String)}
            value={filters.year !== undefined ? String(filters.year) : undefined}
            onChange={handleNumberFilter("year")}
          />
          <FilterGroup
            label="Month"
            options={data.month.map(String)}
            value={
              filters.month !== undefined ? String(filters.month) : undefined
            }
            onChange={handleNumberFilter("month")}
          />
        </div>
      </div>

      {/* Uploaded By */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">
          Uploaded By
        </h3>
        <FilterGroup
          label="User"
          options={data.uploaded_by}
          value={filters.uploaded_by}
          onChange={handleStringFilter("uploaded_by")}
        />
      </div>
    </nav>
  );
}

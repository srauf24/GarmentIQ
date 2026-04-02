import { useCallback, useState } from "react";

import { ActiveFilters } from "../components/Filters/ActiveFilters";
import { SearchBar } from "../components/Filters/SearchBar";
import { ImageGrid } from "../components/Gallery/ImageGrid";
import { Sidebar } from "../components/Layout/Sidebar";
import { useImages } from "../hooks/useImages";
import type { ImageFilters } from "../types";

const PAGE_SIZE = 20;

export function GalleryPage() {
  const [filters, setFilters] = useState<ImageFilters>({});
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error } = useImages({
    ...filters,
    page,
    page_size: PAGE_SIZE,
  });

  const handleFilterChange = useCallback(
    (key: keyof ImageFilters, value: string | number | undefined) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
      setPage(1);
    },
    [],
  );

  const handleRemoveFilter = useCallback((key: keyof ImageFilters) => {
    setFilters((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setPage(1);
  }, []);

  const handleClearAll = useCallback(() => {
    setFilters({});
    setPage(1);
  }, []);

  const handleSearchChange = useCallback((value: string) => {
    setFilters((prev) => ({
      ...prev,
      search: value || undefined,
    }));
    setPage(1);
  }, []);

  const totalPages = data?.total_pages ?? 0;
  const total = data?.total ?? 0;
  const rangeStart = total > 0 ? (page - 1) * PAGE_SIZE + 1 : 0;
  const rangeEnd = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="flex flex-1">
      {/* Sidebar — hidden on small screens */}
      <aside className="hidden w-64 shrink-0 border-r border-gray-200 bg-white p-4 lg:block">
        <Sidebar filters={filters} onFilterChange={handleFilterChange} />
      </aside>

      {/* Main content */}
      <div className="flex-1 px-8 py-6">
        {/* Search bar */}
        <SearchBar value={filters.search ?? ""} onChange={handleSearchChange} />

        {/* Active filter chips */}
        <div className="mt-3">
          <ActiveFilters
            filters={filters}
            onRemove={handleRemoveFilter}
            onClearAll={handleClearAll}
          />
        </div>

        {/* Error state */}
        {isError && (
          <div className="mt-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-700">
              Failed to load images.{" "}
              {error?.message && (
                <span className="text-red-500">{error.message}</span>
              )}
            </p>
          </div>
        )}

        {/* Image grid */}
        <div className="mt-4">
          <ImageGrid images={data?.items ?? []} isLoading={isLoading} />
        </div>

        {/* Pagination */}
        {total > 0 && (
          <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
            <p className="text-sm text-gray-500">
              Showing {rangeStart}&ndash;{rangeEnd} of {total} images
            </p>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setPage((p) => p - 1)}
                disabled={page <= 1}
                className="rounded-sm border border-gray-300 px-3 py-1.5 text-sm font-medium
                           text-gray-700 transition-colors duration-150
                           hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= totalPages}
                className="rounded-sm border border-gray-300 px-3 py-1.5 text-sm font-medium
                           text-gray-700 transition-colors duration-150
                           hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import { useState } from "react";

import { ImageGrid } from "../components/Gallery/ImageGrid";
import { useImages } from "../hooks/useImages";

const PAGE_SIZE = 20;

export function GalleryPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error } = useImages({
    page,
    page_size: PAGE_SIZE,
  });

  if (isError) {
    return (
      <div className="mx-8 mt-6 rounded-md bg-red-50 p-4">
        <p className="text-sm text-red-700">
          Failed to load images.{" "}
          {error?.message && (
            <span className="text-red-500">{error.message}</span>
          )}
        </p>
      </div>
    );
  }

  const totalPages = data?.total_pages ?? 0;
  const total = data?.total ?? 0;
  const rangeStart = total > 0 ? (page - 1) * PAGE_SIZE + 1 : 0;
  const rangeEnd = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="px-8 py-6">
      <ImageGrid images={data?.items ?? []} isLoading={isLoading} />

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
  );
}

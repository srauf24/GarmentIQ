import { useQuery } from "@tanstack/react-query";

import { fetchImages } from "../api/client";
import type { ImageFilters, ImageResponse, PaginatedResponse } from "../types";

export function useImages(filters?: ImageFilters) {
  return useQuery<PaginatedResponse<ImageResponse>>({
    queryKey: ["images", filters],
    queryFn: () => fetchImages(filters),
  });
}

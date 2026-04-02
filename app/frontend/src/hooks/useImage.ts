import { useQuery } from "@tanstack/react-query";

import { fetchImage } from "../api/client";
import type { ImageResponse } from "../types";

export function useImage(id: string) {
  return useQuery<ImageResponse>({
    queryKey: ["images", id],
    queryFn: () => fetchImage(id),
  });
}

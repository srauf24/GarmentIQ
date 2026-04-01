import { useQuery } from "@tanstack/react-query";

import { fetchFilterValues } from "../api/client";
import type { FilterValuesResponse } from "../types";

export function useFilterValues() {
  return useQuery<FilterValuesResponse>({
    queryKey: ["filterValues"],
    queryFn: fetchFilterValues,
    staleTime: 5 * 60 * 1000,
  });
}

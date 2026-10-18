import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import type { components } from "@/types/api";

export type Health = components["schemas"]["Health"];

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health.all,
    queryFn: () => api.get<Health>("/health"),
  });
}

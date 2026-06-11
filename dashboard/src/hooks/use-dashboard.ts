import { useQuery } from "@tanstack/react-query";
import { fetchOverviewMetrics, fetchRecentActivity, fetchRuntimeMetrics, fetchNamespaces, fetchPrompts, fetchCanary, fetchDrift } from "@/lib/api-client";

export function useOverviewMetrics() {
  return useQuery({
    queryKey: ["dashboard", "overview"],
    queryFn: fetchOverviewMetrics,
  });
}

export function useRecentActivity() {
  return useQuery({
    queryKey: ["dashboard", "activity"],
    queryFn: fetchRecentActivity,
  });
}

export function useNamespaces() {
  return useQuery({
    queryKey: ["namespaces"],
    queryFn: fetchNamespaces,
  });
}

export function useRuntimeMetrics(params: {
  namespace_id?: string;
  provider?: string;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ["dashboard", "runtime", params],
    queryFn: () => fetchRuntimeMetrics(params),
  });
}

export function usePrompts(params: {
  namespace_id?: string;
  status?: string;
}) {
  return useQuery({
    queryKey: ["dashboard", "prompts", params],
    queryFn: () => fetchPrompts(params),
  });
}

export function useCanary(params: {
  namespace_id?: string;
  deployment_state?: string;
}) {
  return useQuery({
    queryKey: ["dashboard", "canary", params],
    queryFn: () => fetchCanary(params),
  });
}

export function useDrift(params: {
  namespace_id?: string;
  severity?: string;
  category?: string;
}) {
  return useQuery({
    queryKey: ["dashboard", "drift", params],
    queryFn: () => fetchDrift(params),
  });
}

export const API_BASE_URL = "http://localhost:8000/api/v1";

export async function fetchOverviewMetrics() {
  const res = await fetch(`${API_BASE_URL}/dashboard/overview`);
  if (!res.ok) {
    throw new Error("Failed to fetch overview metrics");
  }
  return res.json();
}

export async function fetchRecentActivity() {
  const res = await fetch(`${API_BASE_URL}/dashboard/activity`);
  if (!res.ok) {
    throw new Error("Failed to fetch recent activity");
  }
  return res.json();
}

export async function fetchNamespaces() {
  const res = await fetch(`${API_BASE_URL}/namespaces`);
  if (!res.ok) {
    throw new Error("Failed to fetch namespaces");
  }
  return res.json();
}

export async function fetchRuntimeMetrics(params: {
  namespace_id?: string;
  provider?: string;
  start_date?: string;
  end_date?: string;
}) {
  const query = new URLSearchParams();
  if (params.namespace_id) query.append("namespace_id", params.namespace_id);
  if (params.provider) query.append("provider", params.provider);
  if (params.start_date) query.append("start_date", params.start_date);
  if (params.end_date) query.append("end_date", params.end_date);

  const url = `${API_BASE_URL}/dashboard/runtime?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch runtime metrics");
  }
  return res.json();
}

export async function fetchPrompts(params: {
  namespace_id?: string;
  status?: string;
}) {
  const query = new URLSearchParams();
  if (params.namespace_id) query.append("namespace_id", params.namespace_id);
  if (params.status) query.append("status", params.status);

  const url = `${API_BASE_URL}/dashboard/prompts?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch prompts");
  }
  return res.json();
}

export async function fetchCanary(params: {
  namespace_id?: string;
  deployment_state?: string;
}) {
  const query = new URLSearchParams();
  if (params.namespace_id) query.append("namespace_id", params.namespace_id);
  if (params.deployment_state) query.append("deployment_state", params.deployment_state);

  const url = `${API_BASE_URL}/dashboard/canary?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch canary deployments");
  }
  return res.json();
}

export async function fetchDrift(params: {
  namespace_id?: string;
  severity?: string;
  category?: string;
}) {
  const query = new URLSearchParams();
  if (params.namespace_id) query.append("namespace_id", params.namespace_id);
  if (params.severity) query.append("severity", params.severity);
  if (params.category) query.append("category", params.category);

  const url = `${API_BASE_URL}/dashboard/drift?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch drift data");
  }
  return res.json();
}

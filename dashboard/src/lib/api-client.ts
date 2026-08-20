const PRODUCTION_BACKEND = "https://apis-production-d069.up.railway.app";
const backendUrl = process.env.NEXT_PUBLIC_API_URL || PRODUCTION_BACKEND;
export const API_BASE_URL = `${backendUrl}/api/v1`;

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

// ── V1.5 Failure Intelligence & Living Evaluation APIs ────────────────────

export async function fetchFailurePatterns(params?: { namespace_id?: string; demo?: boolean }) {
  const query = new URLSearchParams();
  if (params?.namespace_id) query.append("namespace_id", params.namespace_id);
  if (params?.demo !== undefined) query.append("demo", String(params.demo));
  else query.append("demo", "true");

  const url = `${API_BASE_URL}/failures/patterns?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch failure patterns");
  }
  return res.json();
}

export async function fetchBenchmarkSuites(params?: { namespace_id?: string; demo?: boolean }) {
  const query = new URLSearchParams();
  if (params?.namespace_id) query.append("namespace_id", params.namespace_id);
  if (params?.demo !== undefined) query.append("demo", String(params.demo));
  else query.append("demo", "true");

  const url = `${API_BASE_URL}/failures/benchmarks?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch benchmark suites");
  }
  return res.json();
}

export async function triggerFailureAnalysis(namespace_id: string) {
  const res = await fetch(`${API_BASE_URL}/failures/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ namespace_id, window_days: 14, min_failures: 5, is_demo: false }),
  });
  if (!res.ok) {
    throw new Error("Failed to trigger failure analysis");
  }
  return res.json();
}

export async function pollAnalysisJob(job_id: string) {
  const res = await fetch(`${API_BASE_URL}/failures/jobs/${job_id}`);
  if (!res.ok) {
    throw new Error("Failed to poll analysis job");
  }
  return res.json();
}

export async function evaluateBenchmarkSuite(suite_id: string, prompt_version_id: string, model_name?: string) {
  const res = await fetch(`${API_BASE_URL}/failures/benchmarks/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ suite_id, prompt_version_id, model_name: model_name || "gpt-4o-mini" }),
  });
  if (!res.ok) {
    throw new Error("Failed to evaluate benchmark suite");
  }
  return res.json();
}

export async function evaluatePromptOnBenchmark(payload: {
  namespace_id: string;
  prompt_version_id: string;
  suite_id: string;
}) {
  return evaluateBenchmarkSuite(payload.suite_id, payload.prompt_version_id);
}


// ── V2 Autonomous Optimization APIs ──────────────────────────────────────────

export async function triggerAutonomousOptimization(payload: {
  namespace_id: string;
  parent_configuration_id: string;
  benchmark_suite_id: string;
  candidate_count?: number;
}) {
  const baseUrl = API_BASE_URL.replace("/v1", "/v2");
  const res = await fetch(`${baseUrl}/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      namespace_id: payload.namespace_id,
      parent_configuration_id: payload.parent_configuration_id,
      benchmark_suite_id: payload.benchmark_suite_id,
      candidate_count: payload.candidate_count || 3,
      ranking_policy: "hierarchical_quality_first",
      promotion_thresholds: {
        min_benchmark_improvement_count: 1,
        max_holdout_drop_count: 0,
        max_hard_neg_drop_count: 0,
      },
    }),
  });
  if (!res.ok) {
    throw new Error("Failed to trigger autonomous optimization");
  }
  return res.json();
}

export async function fetchOptimizationExperiment(experiment_id: string) {
  const baseUrl = API_BASE_URL.replace("/v1", "/v2");
  const res = await fetch(`${baseUrl}/optimize/${experiment_id}`);
  if (!res.ok) {
    throw new Error("Failed to fetch optimization experiment");
  }
  return res.json();
}

export async function fetchOptimizationComparison(experiment_id: string) {
  const baseUrl = API_BASE_URL.replace("/v1", "/v2");
  const res = await fetch(`${baseUrl}/optimize/${experiment_id}/comparison`);
  if (!res.ok) {
    throw new Error("Failed to fetch optimization comparison");
  }
  return res.json();
}

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Database, ServerCrash, Zap, ArrowUpRight, ArrowDownRight, GitPullRequest } from "lucide-react";
import { useOverviewMetrics } from "@/hooks/use-dashboard";
import { Skeleton } from "@/components/ui/skeleton";

export function OverviewMetrics() {
  const { data, isLoading, error } = useOverviewMetrics();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-[100px]" />
              <Skeleton className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-[60px]" />
              <Skeleton className="h-3 w-[120px] mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !data) {
    return <div className="text-red-500 text-sm">Failed to load metrics. Is the backend running?</div>;
  }

  const m = data.metrics;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Requests (All time)</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{m.totalRequests.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            <span className="text-emerald-500 font-medium">{m.recentRequests.toLocaleString()}</span> in last 24h
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Runtime Latency</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{m.avgLatency}ms</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            Across all models
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Prompt Versions</CardTitle>
          <Database className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{m.activePromptVersions}</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            Across {m.activeNamespaces} namespaces
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Canary Rollouts</CardTitle>
          <GitPullRequest className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${m.activeCanaryRollouts > 0 ? "text-amber-500" : ""}`}>
            {m.activeCanaryRollouts}
          </div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            Evaluating candidates
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Drift Alerts</CardTitle>
          <ServerCrash className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${m.driftAlerts > 0 ? "text-red-500" : "text-emerald-500"}`}>
            {m.driftAlerts}
          </div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            Unresolved alerts
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Provider Fallbacks</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{m.providerFallbacks}</div>
          <p className="text-xs text-muted-foreground flex items-center mt-1">
            Last 24 hours
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

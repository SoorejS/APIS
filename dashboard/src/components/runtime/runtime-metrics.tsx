"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, CheckCircle2, XCircle, ThumbsDown, Zap, Search } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useRuntimeMetrics } from "@/hooks/use-dashboard";
import { Skeleton } from "@/components/ui/skeleton";

export function RuntimeMetrics() {
  const searchParams = useSearchParams();
  const params = {
    namespace_id: searchParams.get("namespace_id") || undefined,
    provider: searchParams.get("provider") || undefined,
  };

  const { data, isLoading, error } = useRuntimeMetrics(params);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
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
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{m.totalRequests.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground mt-1">
            Matches current filters
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-emerald-500">{m.successRate.toFixed(1)}%</div>
          <p className="text-xs text-muted-foreground mt-1">
            <span className="text-red-500 font-medium">{m.failureRate.toFixed(1)}%</span> failure rate
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Thumbs Down Ratio</CardTitle>
          <ThumbsDown className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${m.thumbsDown > m.thumbsUp ? "text-amber-500" : ""}`}>
            {m.totalRequests > 0 ? ((m.thumbsDown / (m.thumbsUp + m.thumbsDown || 1)) * 100).toFixed(1) : 0}%
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {m.thumbsDown} negative signals
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{m.avgLatency}ms</div>
          <p className="text-xs text-muted-foreground mt-1">
            End-to-end execution
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

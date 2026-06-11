"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { useCanary } from "@/hooks/use-dashboard";
import { useSearchParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";

export function RolloutMetrics() {
  const searchParams = useSearchParams();
  const params = {
    namespace_id: searchParams.get("namespace_id") || undefined,
    deployment_state: searchParams.get("deployment_state") || undefined,
  };

  const { data: deployments, isLoading, error } = useCanary(params);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 mt-4">
        <Card className="h-[400px]">
          <CardHeader><Skeleton className="h-6 w-[200px]" /></CardHeader>
          <CardContent><Skeleton className="h-[300px] w-full" /></CardContent>
        </Card>
        <div className="space-y-4">
          <Card><CardHeader><Skeleton className="h-6 w-[150px]" /></CardHeader><CardContent><Skeleton className="h-20 w-full" /></CardContent></Card>
          <Card><CardHeader><Skeleton className="h-6 w-[150px]" /></CardHeader><CardContent><Skeleton className="h-20 w-full" /></CardContent></Card>
        </div>
      </div>
    );
  }

  if (error || !deployments) return null;

  const activeRollout = deployments.find((d: any) => d.status === "canary") || deployments[0];
  
  // Build chart data from activeRollout metrics
  const comparisonData = activeRollout?.metrics?.map((m: any) => ({
    metric: m.name,
    baseline: parseFloat(m.baseline) || 0,
    candidate: parseFloat(m.current) || 0,
  })) || [];

  const rolledBack = deployments.filter((d: any) => d.status === "rolled_back").slice(0, 5);
  const promoted = deployments.filter((d: any) => d.status === "active").slice(0, 5);

  return (
    <div className="grid gap-4 md:grid-cols-2 mt-4">
      <Card>
        <CardHeader>
          <CardTitle>Baseline vs Candidate ({activeRollout ? activeRollout.version : 'N/A'})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] w-full">
            {comparisonData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="metric" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "hsl(var(--background))", borderColor: "hsl(var(--border))", borderRadius: "8px" }}
                    itemStyle={{ color: "hsl(var(--foreground))" }}
                    cursor={{fill: 'hsl(var(--muted))'}}
                  />
                  <Legend iconType="circle" />
                  <Bar dataKey="baseline" name="Baseline" fill="hsl(var(--muted-foreground))" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="candidate" name="Candidate" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground text-sm">No comparison metrics available</div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Rollback History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[160px] overflow-y-auto pr-2">
              {rolledBack.length > 0 ? rolledBack.map((d: any) => (
                <div key={d.id} className="border-l-2 border-red-500 pl-4 py-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-sm">{d.namespace} {d.version}</span>
                    <span className="text-xs text-muted-foreground">{d.startedAt ? new Date(d.startedAt).toLocaleDateString() : ""}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{d.rollbackReason || "Rolled back due to metric regression."}</p>
                </div>
              )) : (
                <div className="text-sm text-muted-foreground italic">No recent rollbacks.</div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Recent Promotions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[160px] overflow-y-auto pr-2">
              {promoted.length > 0 ? promoted.map((d: any) => (
                <div key={d.id} className="border-l-2 border-emerald-500 pl-4 py-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-sm">{d.namespace} {d.version}</span>
                    <span className="text-xs text-muted-foreground">{d.startedAt ? new Date(d.startedAt).toLocaleDateString() : ""}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Passed all canary gates. Successfully promoted to active.</p>
                </div>
              )) : (
                <div className="text-sm text-muted-foreground italic">No recent promotions.</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

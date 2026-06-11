"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from "recharts";
import { useDrift } from "@/hooks/use-dashboard";
import { useSearchParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";

export function DriftCharts() {
  const searchParams = useSearchParams();
  const params = {
    namespace_id: searchParams.get("namespace_id") || undefined,
    severity: searchParams.get("severity") || undefined,
    category: searchParams.get("category") || undefined,
  };

  const { data, isLoading, error } = useDrift(params);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 mt-4">
        <Card>
          <CardHeader><Skeleton className="h-6 w-[200px]" /></CardHeader>
          <CardContent><Skeleton className="h-[250px] w-full" /></CardContent>
        </Card>
        <Card>
          <CardHeader><Skeleton className="h-6 w-[200px]" /></CardHeader>
          <CardContent><Skeleton className="h-[250px] w-full" /></CardContent>
        </Card>
      </div>
    );
  }

  if (error || !data) return null;

  const hallucinationData = data.charts?.hallucination || [];
  const latencyData = data.charts?.latency || [];

  return (
    <div className="grid gap-4 md:grid-cols-2 mt-4">
      <Card className="transition-all duration-300 hover:shadow-md">
        <CardHeader>
          <CardTitle>Hallucination Rate Drift (%)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hallucinationData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorError" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted-foreground))" strokeOpacity={0.2} />
                <XAxis dataKey="time" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "hsl(var(--background))", borderColor: "hsl(var(--border))", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
                  itemStyle={{ color: "hsl(var(--foreground))" }}
                  cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "3 3" }}
                />
                <ReferenceLine y={4.0} stroke="hsl(var(--destructive))" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'Threshold', fill: 'hsl(var(--destructive))', fontSize: 10 }} />
                <Area type="monotone" dataKey="rate" stroke="hsl(var(--destructive))" strokeWidth={2} fillOpacity={1} fill="url(#colorError)" activeDot={{ r: 6, strokeWidth: 0, fill: "hsl(var(--destructive))" }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="transition-all duration-300 hover:shadow-md">
        <CardHeader>
          <CardTitle>Latency Drift (ms)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={latencyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted-foreground))" strokeOpacity={0.2} />
                <XAxis dataKey="time" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "hsl(var(--background))", borderColor: "hsl(var(--border))", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
                  itemStyle={{ color: "hsl(var(--foreground))" }}
                  cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "3 3" }}
                />
                <Area type="monotone" dataKey="rolling7d" name="7-Day Rolling" stroke="hsl(var(--primary))" strokeWidth={2} fillOpacity={1} fill="url(#colorLatency)" activeDot={{ r: 6, strokeWidth: 0, fill: "hsl(var(--primary))" }} />
                <Area type="monotone" dataKey="rolling30d" name="30-Day Baseline" stroke="hsl(var(--muted-foreground))" strokeWidth={2} fillOpacity={0} strokeDasharray="3 3" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

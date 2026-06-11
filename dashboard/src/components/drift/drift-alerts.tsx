"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ShieldAlert, AlertCircle, Info, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDrift } from "@/hooks/use-dashboard";
import { useSearchParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";

export function DriftAlerts() {
  const searchParams = useSearchParams();
  const params = {
    namespace_id: searchParams.get("namespace_id") || undefined,
    severity: searchParams.get("severity") || undefined,
    category: searchParams.get("category") || undefined,
  };

  const { data, isLoading, error } = useDrift(params);

  if (isLoading) {
    return (
      <Card>
        <CardHeader><Skeleton className="h-6 w-[200px]" /></CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) return null;

  const alerts = data.alerts || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Drift Alerts</CardTitle>
        <CardDescription>
          Automated anomalies detected in production traffic
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {alerts.length > 0 ? alerts.map((alert: any) => (
            <div key={alert.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-lg bg-card hover:bg-muted/50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="mt-1">
                  {alert.severity === "critical" ? <ShieldAlert className="w-5 h-5 text-red-500" /> :
                   alert.severity === "high" ? <AlertTriangle className="w-5 h-5 text-amber-500" /> :
                   alert.severity === "medium" ? <AlertCircle className="w-5 h-5 text-blue-500" /> :
                   <Info className="w-5 h-5 text-muted-foreground" />}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm">{alert.namespace}</span>
                    <Badge variant="outline" className={
                      alert.severity === "critical" ? "border-red-500 text-red-500" :
                      alert.severity === "high" ? "border-amber-500 text-amber-500" :
                      "border-muted-foreground text-muted-foreground"
                    }>
                      {alert.severity.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="text-sm font-medium mb-1 capitalize">
                    {alert.category.replace('_', ' ')}: <span className="font-normal text-muted-foreground">{alert.metric}</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 sm:mt-0 flex flex-col sm:items-end gap-2">
                <div className="text-xs text-muted-foreground">
                  {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : ""}
                </div>
                <Button size="sm" variant={alert.recommendation === "rollback" ? "destructive" : "secondary"}>
                  {alert.recommendation === "rollback" ? "Trigger Rollback" : 
                   alert.recommendation === "human_review" ? "Request Review" : 
                   alert.recommendation === "iterate" ? "Generate Candidate" : "Acknowledge"}
                  <ArrowRight className="w-3 h-3 ml-2" />
                </Button>
              </div>
            </div>
          )) : (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <div className="h-12 w-12 rounded-full bg-emerald-500/10 flex items-center justify-center mb-4">
                <Info className="h-6 w-6 text-emerald-500" />
              </div>
              <h3 className="text-lg font-semibold mb-1">No active drift alerts</h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                System healthy. No prompt performance anomalies or degradation detected matching your filters.
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

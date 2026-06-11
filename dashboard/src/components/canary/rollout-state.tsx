"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Circle, AlertCircle, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCanary } from "@/hooks/use-dashboard";
import { useSearchParams } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";

interface RolloutPhase {
  name: string;
  status: "complete" | "current" | "pending" | "failed";
  percentage: number;
}

export function RolloutState() {
  const searchParams = useSearchParams();
  const params = {
    namespace_id: searchParams.get("namespace_id") || undefined,
    deployment_state: searchParams.get("deployment_state") || undefined,
  };

  const { data: deployments, isLoading, error } = useCanary(params);

  if (isLoading) {
    return (
      <Card>
        <CardHeader><Skeleton className="h-6 w-[250px]" /></CardHeader>
        <CardContent><Skeleton className="h-[200px] w-full" /></CardContent>
      </Card>
    );
  }

  if (error || !deployments) return null;

  // Find the first active/in-progress rollout to highlight
  const activeRollout = deployments.find((d: any) => d.status === "canary") || deployments[0];

  if (!activeRollout) {
    return <div className="text-muted-foreground">No active rollouts matching filters.</div>;
  }

  const isFailed = activeRollout.status === "rolled_back";
  const currentPct = activeRollout.traffic;

  const phases: RolloutPhase[] = [
    { name: "Candidate", status: "complete", percentage: 0 },
    { name: "Canary 10%", status: isFailed && currentPct === 10 ? "failed" : currentPct >= 10 ? (currentPct === 10 ? "current" : "complete") : "pending", percentage: 10 },
    { name: "Canary 25%", status: isFailed && currentPct === 25 ? "failed" : currentPct >= 25 ? (currentPct === 25 ? "current" : "complete") : "pending", percentage: 25 },
    { name: "Canary 50%", status: isFailed && currentPct === 50 ? "failed" : currentPct >= 50 ? (currentPct === 50 ? "current" : "complete") : "pending", percentage: 50 },
    { name: "Active 100%", status: currentPct === 100 ? "complete" : "pending", percentage: 100 },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>Active Rollout: {activeRollout.namespace} {activeRollout.version}</CardTitle>
            <CardDescription className="mt-1">
              {isFailed ? `Rollback initiated during ${activeRollout.stage}` : `Currently evaluating at ${currentPct}% traffic allocation`}
            </CardDescription>
          </div>
          <Badge variant="outline" className={cn(
            isFailed ? "bg-red-500/10 text-red-500 border-red-500/20" : 
            currentPct === 100 ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : 
            "bg-amber-500/10 text-amber-500 border-amber-500/20"
          )}>
            {isFailed ? "Rolled Back" : currentPct === 100 ? "Completed" : "In Progress"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-8">
          <div className="flex justify-between text-sm mb-2">
            <span className="font-medium">Traffic Allocation</span>
            <span className="text-muted-foreground">{currentPct}%</span>
          </div>
          <Progress value={currentPct} className={cn("h-2", isFailed ? "[&>div]:bg-red-500" : "")} />
        </div>

        <div className="relative">
          <div className="absolute top-5 left-6 right-6 h-0.5 bg-muted z-0"></div>
          <div className="absolute top-5 left-6 h-0.5 bg-primary z-0 transition-all duration-500" style={{ width: `${currentPct}%`, backgroundColor: isFailed ? 'hsl(var(--destructive))' : 'hsl(var(--primary))' }}></div>
          
          <div className="flex justify-between relative z-10">
            {phases.map((phase, index) => (
              <div key={phase.name} className="flex flex-col items-center gap-2">
                <div className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center border-4 border-background transition-colors",
                  phase.status === "complete" ? "bg-primary text-primary-foreground" :
                  phase.status === "current" ? "bg-background border-primary text-primary" :
                  phase.status === "failed" ? "bg-destructive text-destructive-foreground" :
                  "bg-muted text-muted-foreground"
                )}>
                  {phase.status === "complete" ? <CheckCircle2 className="w-5 h-5" /> :
                   phase.status === "failed" ? <AlertCircle className="w-5 h-5" /> :
                   <Circle className="w-5 h-5 fill-current opacity-20" />}
                </div>
                <div className="text-xs font-medium text-center max-w-[80px]">
                  {phase.name}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 p-4 bg-muted/50 rounded-lg border">
          <h4 className="text-sm font-medium mb-2">Rollout Timeline</h4>
          <ul className="text-sm space-y-2 text-muted-foreground">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              Deployment started: {activeRollout.startedAt ? new Date(activeRollout.startedAt).toLocaleString() : "Unknown"}
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              Duration: {activeRollout.duration}
            </li>
            {isFailed && (
              <li className="flex items-center gap-2 text-red-500">
                <AlertCircle className="w-4 h-4 text-red-500" />
                Reason: {activeRollout.rollbackReason}
              </li>
            )}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

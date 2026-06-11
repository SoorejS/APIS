import { RolloutState } from "@/components/canary/rollout-state";
import { RolloutMetrics } from "@/components/canary/rollout-metrics";
import { CanaryFilters } from "@/components/canary/canary-filters";

export default function CanaryPage() {
  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Canary Deployments</h2>
          <p className="text-muted-foreground mt-1">Monitor active rollouts and traffic allocation</p>
        </div>
        <CanaryFilters />
      </div>

      <RolloutState />
      <RolloutMetrics />
    </div>
  );
}

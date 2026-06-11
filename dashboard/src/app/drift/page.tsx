import { DriftAlerts } from "@/components/drift/drift-alerts";
import { DriftCharts } from "@/components/drift/drift-charts";
import { DriftFilters } from "@/components/drift/drift-filters";

export default function DriftPage() {
  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Drift Detection</h2>
          <p className="text-muted-foreground mt-1">Real-time monitoring of prompt performance degradation</p>
        </div>
        <DriftFilters />
      </div>

      <DriftAlerts />
      <DriftCharts />
    </div>
  );
}

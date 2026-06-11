import { RuntimeFilters } from "@/components/runtime/runtime-filters";
import { RuntimeMetrics } from "@/components/runtime/runtime-metrics";
import { RuntimeCharts } from "@/components/runtime/runtime-charts";

export default function RuntimeAnalyticsPage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
        <h2 className="text-3xl font-bold tracking-tight">Runtime Analytics</h2>
        <RuntimeFilters />
      </div>
      <RuntimeMetrics />
      <RuntimeCharts />
    </div>
  );
}

import { OverviewMetrics } from "@/components/dashboard/overview-metrics";
import { OverviewCharts } from "@/components/dashboard/overview-charts";
import { RecentActivity } from "@/components/dashboard/recent-activity";

export default function Home() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Overview</h2>
        <div className="flex items-center space-x-2">
          {/* We can add date pickers or namespace filters here later */}
        </div>
      </div>
      <OverviewMetrics />
      <OverviewCharts />
      <RecentActivity />
    </div>
  );
}

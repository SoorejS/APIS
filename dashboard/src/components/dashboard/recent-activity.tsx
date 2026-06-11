import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { useRecentActivity } from "@/hooks/use-dashboard";
import { Skeleton } from "@/components/ui/skeleton";

export function RecentActivity() {
  const { data, isLoading, error } = useRecentActivity();

  if (isLoading) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>System events from the last 24 hours</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-start gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-4 w-[250px]" />
                  <Skeleton className="h-3 w-[200px]" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-red-500">Failed to load recent activity.</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>
          Live system events from APIS Runtime
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {data.length === 0 ? (
            <div className="text-sm text-muted-foreground text-center py-4">No recent activity</div>
          ) : (
            data.map((item: any) => (
              <div key={item.id} className="flex items-start gap-4">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full border ${
                  item.status === "success" ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-500" :
                  item.status === "warning" ? "border-amber-500/50 bg-amber-500/10 text-amber-500" :
                  item.status === "destructive" ? "border-red-500/50 bg-red-500/10 text-red-500" :
                  "border-primary/50 bg-primary/10 text-primary"
                }`}>
                  <span className="text-xs font-semibold">{item.initials}</span>
                </div>
                <div className="flex flex-1 flex-col justify-center space-y-1">
                  <p className="text-sm font-medium leading-none flex items-center justify-between">
                    <span>{item.action}</span>
                    <span className="text-xs text-muted-foreground">
                      {item.time ? formatDistanceToNow(new Date(item.time), { addSuffix: true }) : "just now"}
                    </span>
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

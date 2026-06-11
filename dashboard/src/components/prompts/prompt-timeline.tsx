"use client";

import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { PromptDiff } from "./prompt-diff";
import { CheckCircle2, GitCommit, GitMerge, AlertCircle, ArrowRight } from "lucide-react";
import { usePrompts } from "@/hooks/use-dashboard";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function PromptTimeline() {
  const searchParams = useSearchParams();
  const params = {
    namespace_id: searchParams.get("namespace_id") || undefined,
    status: searchParams.get("status") || undefined,
  };

  const { data: versions, isLoading, error } = usePrompts(params);

  if (isLoading) {
    return (
      <div className="space-y-8 pl-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-4 mb-4">
            <Skeleton className="h-10 w-10 rounded-full shrink-0" />
            <Skeleton className="h-[200px] w-full rounded-xl" />
          </div>
        ))}
      </div>
    );
  }

  if (error || !versions) {
    return <div className="text-red-500">Failed to load prompt history.</div>;
  }

  if (versions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center border rounded-xl bg-card border-dashed">
        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
          <GitCommit className="h-6 w-6 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-1">No prompt evolution history</h3>
        <p className="text-sm text-muted-foreground max-w-sm mx-auto">
          No adaptive iterations found. The system will automatically generate candidate versions when enough feedback is collected.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pl-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-muted-foreground/20 before:to-transparent">
      {versions.map((v: any, index: number) => (
        <div key={v.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
          {/* Timeline Icon */}
          <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-background bg-muted text-muted-foreground shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 absolute left-0 md:left-1/2 -translate-x-1/2 z-10">
            {v.status === "active" ? <CheckCircle2 className="h-5 w-5 text-emerald-500" /> : 
             v.status === "rejected" || v.status === "rolled_back" ? <AlertCircle className="h-5 w-5 text-red-500" /> : 
             <GitCommit className="h-5 w-5" />}
          </div>

          {/* Content Card */}
          <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] ml-8 md:ml-0 p-4 rounded-xl border bg-card shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg">{v.version}</span>
                <Badge variant={v.status === "active" ? "default" : v.status === "rejected" || v.status === "rolled_back" ? "destructive" : "secondary"}>
                  {v.status}
                </Badge>
              </div>
              <span className="text-xs text-muted-foreground">{v.date ? new Date(v.date).toLocaleString() : ""}</span>
            </div>
            
            <p className="text-sm text-muted-foreground mb-4">{v.rationale}</p>
            
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="details" className="border-b-0">
                <AccordionTrigger className="py-2 text-sm hover:no-underline font-medium text-primary">
                  View Details
                </AccordionTrigger>
                <AccordionContent>
                  <div className="space-y-4 pt-2">
                    {v.deltas && v.deltas.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Benchmark Delta</h4>
                        <div className="grid grid-cols-3 gap-2">
                          {v.deltas.map((m: any) => (
                            <div key={m.label} className="p-2 bg-muted/50 rounded text-center">
                              <div className="text-xs text-muted-foreground">{m.label}</div>
                              <div className={cn("text-sm font-bold", m.trend === "up" && m.label !== "Thumbs Down" && m.label !== "Latency" ? "text-emerald-500" : m.trend === "down" && (m.label === "Thumbs Down" || m.label === "Latency") ? "text-emerald-500" : m.trend === "neutral" ? "text-amber-500" : "text-red-500")}>
                                {m.value}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {(v.deployment?.outcome || v.deployment?.rollbackReason) && (
                      <div className="space-y-1">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Decision</h4>
                        <p className="text-sm border-l-2 pl-2 border-primary">
                          {v.deployment.outcome || v.deployment.rollbackReason}
                        </p>
                      </div>
                    )}

                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Changes</h4>
                      <PromptDiff added={v.diff?.added || []} removed={v.diff?.removed || []} modified={v.diff?.modified || []} />
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        </div>
      ))}
    </div>
  );
}

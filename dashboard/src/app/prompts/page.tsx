import { Suspense } from "react";
import { PromptTimeline } from "@/components/prompts/prompt-timeline";
import { PromptFilters } from "@/components/prompts/prompt-filters";

export default function PromptsPage() {
  return (
    <Suspense fallback={<div className="flex-1 p-8 text-center text-muted-foreground animate-pulse">Loading Prompt Evolution...</div>}>
      <div className="flex-1 space-y-8 p-8 pt-6">
        <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Prompt Evolution</h2>
            <p className="text-muted-foreground mt-1">Lifecycle tracking and automated versioning</p>
          </div>
          <PromptFilters />
        </div>

        <div className="mx-auto max-w-4xl pt-8">
          <PromptTimeline />
        </div>
      </div>
    </Suspense>
  );
}

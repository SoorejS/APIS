import { cn } from "@/lib/utils";

interface PromptDiffProps {
  added?: string[];
  removed?: string[];
  modified?: string[];
}

export function PromptDiff({ added = [], removed = [], modified = [] }: PromptDiffProps) {
  if (added.length === 0 && removed.length === 0 && modified.length === 0) {
    return <div className="text-sm text-muted-foreground italic">No content changes.</div>;
  }

  return (
    <div className="rounded-md border bg-muted/50 p-4 font-mono text-sm">
      {removed.length > 0 && (
        <div className="mb-2 space-y-1">
          {removed.map((line, i) => (
            <div key={`rem-${i}`} className="flex items-start text-red-500 dark:text-red-400 bg-red-500/10 dark:bg-red-900/20 px-2 py-0.5 rounded">
              <span className="mr-4 select-none opacity-50">-</span>
              <span className="whitespace-pre-wrap">{line}</span>
            </div>
          ))}
        </div>
      )}
      
      {modified.length > 0 && (
        <div className="mb-2 space-y-1">
          {modified.map((line, i) => (
            <div key={`mod-${i}`} className="flex items-start text-amber-600 dark:text-amber-400 bg-amber-500/10 dark:bg-amber-900/20 px-2 py-0.5 rounded">
              <span className="mr-4 select-none opacity-50">~</span>
              <span className="whitespace-pre-wrap">{line}</span>
            </div>
          ))}
        </div>
      )}

      {added.length > 0 && (
        <div className="space-y-1">
          {added.map((line, i) => (
            <div key={`add-${i}`} className="flex items-start text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 dark:bg-emerald-900/20 px-2 py-0.5 rounded">
              <span className="mr-4 select-none opacity-50">+</span>
              <span className="whitespace-pre-wrap">{line}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

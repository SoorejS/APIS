"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { CalendarDays, Filter } from "lucide-react";
import { useNamespaces } from "@/hooks/use-dashboard";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useCallback } from "react";

export function RuntimeFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { data: namespaces, isLoading } = useNamespaces();

  const createQueryString = useCallback(
    (name: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value === "all") {
        params.delete(name);
      } else {
        params.set(name, value);
      }
      return params.toString();
    },
    [searchParams]
  );

  const handleFilterChange = (key: string, value: string) => {
    router.push(`${pathname}?${createQueryString(key, value)}`);
  };

  const currentNamespace = searchParams.get("namespace_id") || "all";
  const currentProvider = searchParams.get("provider") || "all";

  return (
    <div className="flex items-center space-x-2">
      <Select value={currentNamespace} onValueChange={(val) => handleFilterChange("namespace_id", val || "all")}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Namespace" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Namespaces</SelectItem>
          {!isLoading && namespaces?.map((ns: any) => (
            <SelectItem key={ns.id} value={String(ns.id)}>{ns.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={currentProvider} onValueChange={(val) => handleFilterChange("provider", val || "all")}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Provider" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Providers</SelectItem>
          <SelectItem value="gemini">Gemini</SelectItem>
          <SelectItem value="openai">OpenAI</SelectItem>
          <SelectItem value="anthropic">Anthropic</SelectItem>
          <SelectItem value="google">Google</SelectItem>
          <SelectItem value="ollama">Ollama</SelectItem>
        </SelectContent>
      </Select>

      <Button variant="outline" className="w-[240px] justify-start text-left font-normal" disabled>
        <CalendarDays className="mr-2 h-4 w-4" />
        <span>Last 7 days</span>
      </Button>
      
      <Button variant="ghost" size="icon" onClick={() => router.push(pathname)}>
        <Filter className="h-4 w-4" />
      </Button>
    </div>
  );
}

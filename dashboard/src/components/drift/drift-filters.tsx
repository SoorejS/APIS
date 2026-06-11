"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { useNamespaces } from "@/hooks/use-dashboard";
import { Button } from "@/components/ui/button";
import { Settings2 } from "lucide-react";

export function DriftFilters() {
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
  const currentSeverity = searchParams.get("severity") || "all";
  const currentCategory = searchParams.get("category") || "all";

  return (
    <div className="flex items-center space-x-2">
      <Select value={currentNamespace} onValueChange={(val) => handleFilterChange("namespace_id", val)}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Namespace" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Namespaces</SelectItem>
          {!isLoading && namespaces?.map((ns: any) => (
            <SelectItem key={ns.id} value={ns.id}>{ns.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={currentSeverity} onValueChange={(val) => handleFilterChange("severity", val)}>
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="Severity" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Severities</SelectItem>
          <SelectItem value="critical">Critical</SelectItem>
          <SelectItem value="high">High</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="low">Low</SelectItem>
        </SelectContent>
      </Select>

      <Select value={currentCategory} onValueChange={(val) => handleFilterChange("category", val)}>
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="Category" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Categories</SelectItem>
          <SelectItem value="general">General</SelectItem>
          <SelectItem value="billing">Billing</SelectItem>
          <SelectItem value="technical">Technical</SelectItem>
        </SelectContent>
      </Select>

      <Button variant="outline" size="icon">
        <Settings2 className="h-4 w-4" />
      </Button>
    </div>
  );
}

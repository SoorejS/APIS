"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { useNamespaces } from "@/hooks/use-dashboard";

export function CanaryFilters() {
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
  const currentState = searchParams.get("deployment_state") || "all";

  return (
    <div className="flex items-center space-x-2">
      <Select value={currentNamespace} onValueChange={(val) => handleFilterChange("namespace_id", val || "all")}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select Namespace" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Namespaces</SelectItem>
          {!isLoading && namespaces?.map((ns: any) => (
            <SelectItem key={ns.id} value={String(ns.id)}>{ns.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      <Select value={currentState} onValueChange={(val) => handleFilterChange("deployment_state", val || "all")}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Deployment State" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All States</SelectItem>
          <SelectItem value="canary_10">Canary 10%</SelectItem>
          <SelectItem value="canary_25">Canary 25%</SelectItem>
          <SelectItem value="canary_50">Canary 50%</SelectItem>
          <SelectItem value="active">Active (100%)</SelectItem>
          <SelectItem value="rolled_back">Rolled Back</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

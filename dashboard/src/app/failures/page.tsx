"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  AlertTriangle, 
  CheckCircle2, 
  TrendingUp, 
  TrendingDown, 
  Layers, 
  Sparkles, 
  RefreshCw, 
  ArrowRight,
  ShieldAlert,
  Flame,
  Info
} from "lucide-react";
import { fetchFailurePatterns, triggerFailureAnalysis, fetchNamespaces } from "@/lib/api-client";

export default function FailuresPage() {
  const [patterns, setPatterns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [demoMode, setDemoMode] = useState(true);
  const [selectedPattern, setSelectedPattern] = useState<any>(null);
  const [namespaces, setNamespaces] = useState<any[]>([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pats, ns] = await Promise.all([
        fetchFailurePatterns({ demo: demoMode }),
        fetchNamespaces().catch(() => [])
      ]);
      setPatterns(pats || []);
      setNamespaces(ns || []);
      if (pats && pats.length > 0 && !selectedPattern) {
        setSelectedPattern(pats[0]);
      }
    } catch (err) {
      console.error("Failed to load failure patterns:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [demoMode]);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      const nsId = namespaces[0]?.id || "demo-namespace";
      await triggerFailureAnalysis(nsId);
      setTimeout(() => {
        loadData();
        setAnalyzing(false);
      }, 2500);
    } catch (err) {
      console.error(err);
      setAnalyzing(false);
    }
  };

  const totalInteractions = patterns.reduce((sum, p) => sum + (p.interaction_count || 0), 0);
  const avgClusterConfidence = patterns.length > 0
    ? (patterns.reduce((sum, p) => sum + (p.cluster_confidence || 0), 0) / patterns.length).toFixed(2)
    : "0.00";
  const avgDiagConfidence = patterns.length > 0
    ? (patterns.reduce((sum, p) => sum + (p.diagnosis_confidence || 0), 0) / patterns.length).toFixed(2)
    : "0.00";

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight">Failure Intelligence</h2>
            <Badge variant="outline" className="border-amber-500/30 bg-amber-500/10 text-amber-500">
              V1.5 Active
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1 text-sm">
            Autonomous semantic failure clustering, recurrence trend tracking, and pattern diagnosis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant={demoMode ? "secondary" : "outline"}
            size="sm"
            onClick={() => setDemoMode(!demoMode)}
            className="text-xs"
          >
            {demoMode ? "Demo Mode (Seeded)" : "Live Production"}
          </Button>

          <Button
            onClick={handleRunAnalysis}
            disabled={analyzing}
            className="bg-primary text-primary-foreground font-medium text-sm flex items-center gap-2 shadow-sm"
          >
            <RefreshCw className={`h-4 w-4 ${analyzing ? "animate-spin" : ""}`} />
            {analyzing ? "Analyzing Clusters..." : "Run Windowed Analysis"}
          </Button>
        </div>
      </div>

      {/* Pipeline Telemetry Funnel Bar */}
      <Card className="border-border/60 bg-card/60 backdrop-blur-sm">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              <span className="font-semibold text-foreground">Windowed Pipeline Telemetry:</span>
            </div>
            <div className="flex items-center gap-6 text-muted-foreground">
              <div><strong className="text-foreground">{totalInteractions || 960}</strong> eligible interactions</div>
              <div>→</div>
              <div><strong className="text-foreground">HDBSCAN</strong> cosine clustering</div>
              <div>→</div>
              <div><strong className="text-foreground">{patterns.length}</strong> valid patterns</div>
              <div>→</div>
              <div><strong className="text-foreground">{patterns.length * 3}</strong> benchmark tests generated</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Failure Patterns</CardTitle>
            <Flame className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{patterns.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Across 14-day sliding window</p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Clustered Interactions</CardTitle>
            <Layers className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalInteractions.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">Classified into failure clusters</p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Cluster Cohesion</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">{avgClusterConfidence}</div>
            <p className="text-xs text-muted-foreground mt-1">Mean HDBSCAN membership probability</p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Diagnosis Confidence</CardTitle>
            <Sparkles className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgDiagConfidence}</div>
            <p className="text-xs text-muted-foreground mt-1">LLM evidence certainty score</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Split View: Pattern List + Pattern Detail Inspector */}
      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : patterns.length === 0 ? (
        <Card className="p-12 text-center text-muted-foreground">
          <ShieldAlert className="mx-auto h-12 w-12 text-muted-foreground/50 mb-3" />
          <h3 className="text-lg font-semibold text-foreground">No Failure Patterns Detected</h3>
          <p className="text-sm mt-1">Click "Run Windowed Analysis" to cluster negative production telemetry.</p>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Pattern Cards List */}
          <div className="lg:col-span-7 space-y-4">
            {patterns.map((pat) => {
              const isSelected = selectedPattern?.id === pat.id;
              const isTrendingUp = (pat.recurrence_trend || 0) > 0;
              const trendPct = Math.abs(Math.round((pat.recurrence_trend || 0) * 100));

              return (
                <Card
                  key={pat.id}
                  onClick={() => setSelectedPattern(pat)}
                  className={`cursor-pointer transition-all duration-200 hover:border-primary/50 ${
                    isSelected ? "border-primary bg-primary/5 shadow-sm" : "border-border/60"
                  }`}
                >
                  <CardHeader className="p-5 pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-[10px] uppercase tracking-wider font-mono">
                            {pat.category}
                          </Badge>
                          <Badge
                            className={`text-[10px] uppercase tracking-wider font-mono ${
                              pat.severity === "critical"
                                ? "bg-red-500/10 text-red-500 border-red-500/30"
                                : pat.severity === "high"
                                ? "bg-amber-500/10 text-amber-500 border-amber-500/30"
                                : "bg-blue-500/10 text-blue-500 border-blue-500/30"
                            }`}
                          >
                            {pat.severity}
                          </Badge>
                        </div>
                        <CardTitle className="text-base font-semibold mt-2 leading-tight">
                          {pat.title}
                        </CardTitle>
                      </div>

                      <div className="text-right shrink-0">
                        <div className="text-lg font-bold">
                          {Math.round((pat.recurrence_rate || 0) * 100)}%
                        </div>
                        <div className="text-[11px] text-muted-foreground">recurrence rate</div>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="p-5 pt-0">
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {pat.diagnosis}
                    </p>

                    <div className="flex items-center justify-between mt-4 pt-3 border-t text-xs text-muted-foreground">
                      <div className="flex items-center gap-4">
                        <span><strong>{pat.interaction_count}</strong> interactions</span>
                        <span>Cohesion: <strong>{pat.cluster_cohesion}</strong></span>
                        <span>Conf: <strong>{pat.cluster_confidence}</strong></span>
                      </div>

                      <div className={`flex items-center gap-1 font-medium ${isTrendingUp ? "text-red-500" : "text-emerald-500"}`}>
                        {isTrendingUp ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
                        {isTrendingUp ? `+${trendPct}% WoW` : `-${trendPct}% WoW`}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Selected Pattern Deep-Dive Inspector */}
          <div className="lg:col-span-5">
            {selectedPattern && (
              <Card className="sticky top-6 border-border/80 shadow-md">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">
                      Pattern Inspector
                    </Badge>
                    <span className="text-xs text-muted-foreground font-mono">
                      ID: {selectedPattern.id.slice(0, 8)}
                    </span>
                  </div>
                  <CardTitle className="text-lg font-bold mt-2">
                    {selectedPattern.title}
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Synthesized from {selectedPattern.interaction_count} core cluster exemplars
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4 text-xs">
                  <div>
                    <h4 className="font-semibold text-foreground mb-1">Failure Diagnosis:</h4>
                    <p className="text-muted-foreground leading-relaxed bg-muted/30 p-3 rounded-md border border-border/50">
                      {selectedPattern.diagnosis}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-card border rounded-md">
                      <div className="text-muted-foreground">Cluster Quality</div>
                      <div className="text-base font-bold text-foreground mt-0.5">
                        {selectedPattern.cluster_confidence} / 1.00
                      </div>
                      <div className="text-[10px] text-muted-foreground">Mean probability score</div>
                    </div>

                    <div className="p-3 bg-card border rounded-md">
                      <div className="text-muted-foreground">Diagnosis Certainty</div>
                      <div className="text-base font-bold text-foreground mt-0.5">
                        {selectedPattern.diagnosis_confidence} / 1.00
                      </div>
                      <div className="text-[10px] text-muted-foreground">LLM evidence alignment</div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-foreground mb-1.5 flex items-center justify-between">
                      <span>Exemplar Evidence IDs</span>
                      <span className="text-[10px] text-muted-foreground">Linked production telemetry</span>
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {(selectedPattern.exemplar_interaction_ids || ["ex_101", "ex_102"]).map((eid: string) => (
                        <Badge key={eid} variant="secondary" className="font-mono text-[10px]">
                          {eid}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2">
                    <a
                      href="/evals"
                      className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary/10 py-2 text-xs font-medium text-primary hover:bg-primary/20 border border-primary/20 transition-colors"
                    >
                      <span>View Synthesized Living Benchmark Tests</span>
                      <ArrowRight className="h-4 w-4" />
                    </a>
                  </div>

                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

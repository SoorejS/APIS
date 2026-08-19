"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Terminal, 
  CheckCircle, 
  XCircle, 
  ShieldAlert, 
  Sparkles, 
  Play, 
  Layers, 
  History, 
  Fingerprint, 
  ArrowUpRight,
  Split
} from "lucide-react";
import { fetchBenchmarkSuites, fetchPrompts, evaluatePromptOnBenchmark } from "@/lib/api-client";

export default function LivingEvalsPage() {
  const [suites, setSuites] = useState<any[]>([]);
  const [prompts, setPrompts] = useState<any[]>([]);
  const [selectedSuite, setSelectedSuite] = useState<any>(null);
  const [selectedArchetype, setSelectedArchetype] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<any>(null);
  const [demoMode, setDemoMode] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [suitesData, promptsData] = await Promise.all([
        fetchBenchmarkSuites({ demo: demoMode }),
        fetchPrompts({}).catch(() => [])
      ]);
      setSuites(suitesData || []);
      setPrompts(promptsData || []);
      if (suitesData && suitesData.length > 0 && !selectedSuite) {
        setSelectedSuite(suitesData[0]);
      }
    } catch (err) {
      console.error("Failed to load benchmark suites:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [demoMode]);

  const handleRunEvaluation = async () => {
    if (!selectedSuite) return;
    setEvaluating(true);
    try {
      const promptId = prompts[0]?.id || "00000000-0000-0000-0000-000000000001";
      const res = await evaluatePromptOnBenchmark({
        namespace_id: selectedSuite.namespace_id,
        prompt_version_id: promptId,
        suite_id: selectedSuite.id
      });
      setEvalResult(res);
    } catch (err) {
      console.error("Evaluation failed:", err);
    } finally {
      setEvaluating(false);
    }
  };

  const cases = selectedSuite?.cases || [];
  const filteredCases = selectedArchetype === "all" 
    ? cases 
    : cases.filter((c: any) => c.archetype === selectedArchetype);

  const regressionCount = cases.filter((c: any) => c.archetype === "regression").length;
  const edgeCaseCount = cases.filter((c: any) => c.archetype === "edge_case").length;
  const hardNegCount = cases.filter((c: any) => c.archetype === "hard_negative").length;

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight">Living Benchmark Suite</h2>
            <Badge variant="outline" className="border-primary/40 bg-primary/10 text-primary">
              Immutable Snapshots
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1 text-sm">
            Evolving test suites synthesized from production failures with complete provenance tracking and hard negatives.
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
            onClick={handleRunEvaluation}
            disabled={evaluating || !selectedSuite}
            className="bg-primary text-primary-foreground font-medium text-sm flex items-center gap-2 shadow-sm"
          >
            <Play className={`h-4 w-4 ${evaluating ? "animate-spin" : ""}`} />
            {evaluating ? "Evaluating Candidates..." : "Run Benchmark Evaluation"}
          </Button>
        </div>
      </div>

      {/* KPI Cards & Archetype Breakdown */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Suite Version</CardTitle>
            <History className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Suite v{selectedSuite?.version_number || 1}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Snapshot with {cases.length} validated cases
            </p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">1️⃣ Regression Cases</CardTitle>
            <CheckCircle className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{regressionCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Direct failure remediation tests</p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">2️⃣ Edge Case Variations</CardTitle>
            <Split className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{edgeCaseCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Mixed-state boundary permutations</p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">3️⃣ Hard Negatives</CardTitle>
            <ShieldAlert className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-500">{hardNegCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Crucial negative constraint checks</p>
          </CardContent>
        </Card>
      </div>

      {/* Evaluation Results Banner (If Executed) */}
      {evalResult && (
        <Card className="border-emerald-500/40 bg-emerald-500/5 shadow-md">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-500" />
                <CardTitle className="text-base font-bold text-emerald-500">
                  Benchmark Evaluation Complete — Suite v{evalResult.suite_version}
                </CardTitle>
              </div>
              <Badge className="bg-emerald-500 text-white font-mono text-sm px-3 py-0.5">
                {evalResult.overall_pass_rate}% Overall Pass Rate
              </Badge>
            </div>
            <CardDescription className="text-xs mt-1">
              Evaluation executed across all 3 archetypes comparing candidate remediation to baseline.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 pt-2 border-t text-xs">
              <div className="p-3 bg-card rounded border">
                <div className="text-muted-foreground">Regression Pass Rate</div>
                <div className="text-lg font-bold text-foreground mt-0.5">
                  {evalResult.archetype_breakdown?.regression?.pass_rate || 100}%
                </div>
                <div className="text-[10px] text-muted-foreground">Fixed direct failure patterns</div>
              </div>
              <div className="p-3 bg-card rounded border">
                <div className="text-muted-foreground">Edge Case Pass Rate</div>
                <div className="text-lg font-bold text-foreground mt-0.5">
                  {evalResult.archetype_breakdown?.edge_case?.pass_rate || 100}%
                </div>
                <div className="text-[10px] text-muted-foreground">Maintained boundary stability</div>
              </div>
              <div className="p-3 bg-card rounded border">
                <div className="text-muted-foreground">Hard Negative Pass Rate</div>
                <div className="text-lg font-bold text-purple-500 mt-0.5">
                  {evalResult.archetype_breakdown?.hard_negative?.pass_rate || 100}%
                </div>
                <div className="text-[10px] text-muted-foreground">Respected negative constraints</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Benchmark Explorer Filter & Cases Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Living Test Cases</CardTitle>
              <CardDescription className="text-xs">
                Inspect synthetic prompts, expected criteria, and strict negative constraints
              </CardDescription>
            </div>

            {/* Archetype Filter Tabs */}
            <Tabs value={selectedArchetype} onValueChange={setSelectedArchetype} className="w-auto">
              <TabsList className="grid grid-cols-4 w-full md:w-[480px]">
                <TabsTrigger value="all" className="text-xs">All ({cases.length})</TabsTrigger>
                <TabsTrigger value="regression" className="text-xs">Regression ({regressionCount})</TabsTrigger>
                <TabsTrigger value="edge_case" className="text-xs">Edge Case ({edgeCaseCount})</TabsTrigger>
                <TabsTrigger value="hard_negative" className="text-xs">Hard Negative ({hardNegCount})</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : filteredCases.length === 0 ? (
            <div className="text-center py-10 text-muted-foreground text-sm">
              No test cases found for this archetype.
            </div>
          ) : (
            <div className="space-y-4">
              {filteredCases.map((c: any, index: number) => (
                <div
                  key={c.id || index}
                  className="p-4 rounded-lg border bg-card/60 backdrop-blur-sm space-y-3 transition-all hover:border-primary/40"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge
                        className={`text-[10px] uppercase font-mono tracking-wider ${
                          c.archetype === "hard_negative"
                            ? "bg-purple-500/10 text-purple-500 border-purple-500/30"
                            : c.archetype === "regression"
                            ? "bg-blue-500/10 text-blue-500 border-blue-500/30"
                            : "bg-amber-500/10 text-amber-500 border-amber-500/30"
                        }`}
                      >
                        {c.archetype.replace("_", " ")}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] font-mono">
                        {c.assertion_type}
                      </Badge>
                    </div>

                    {/* Provenance Metadata Badge */}
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Fingerprint className="h-3.5 w-3.5 text-primary" />
                      <span className="font-mono text-[11px]">Provenance: {c.source}</span>
                      <span>•</span>
                      <span className="text-emerald-500 font-medium">
                        Val Conf: {c.validation_confidence}
                      </span>
                    </div>
                  </div>

                  <div>
                    <div className="text-xs font-semibold text-foreground mb-1">Test Input Prompt:</div>
                    <div className="p-2.5 rounded bg-muted/40 font-mono text-xs text-foreground border border-border/40">
                      "{c.input_prompt}"
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="font-semibold text-foreground">Expected Criteria:</span>
                      <p className="text-muted-foreground mt-0.5">{c.expected_output_criteria}</p>
                    </div>

                    {c.negative_constraint && (
                      <div className="p-2.5 rounded bg-purple-500/10 border border-purple-500/20 text-purple-400">
                        <span className="font-bold flex items-center gap-1.5 text-purple-300">
                          <ShieldAlert className="h-3.5 w-3.5" /> Negative Constraint (Must NOT Do):
                        </span>
                        <p className="mt-0.5">{c.negative_constraint}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

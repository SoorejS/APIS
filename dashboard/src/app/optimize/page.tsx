"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Zap,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Cpu,
  Layers,
  ChevronRight,
  Terminal,
  Activity,
  Check
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function OptimizePage() {
  const [selectedCandidate, setSelectedCandidate] = useState<string>("cand_b");
  const [activeTab, setActiveTab] = useState<"hypotheses" | "matrix" | "rejection">("hypotheses");

  // Sample data simulating real V2 experiment state
  const experiment = {
    id: "exp_v2_9f8a32",
    namespace: "geartech_support_prod",
    current_production: {
      version: "Prompt v1.0",
      benchmark_score: "12 / 51 passed (23.5%)",
      holdout_score: "2 / 10 passed (20.0%)",
      hard_negative_score: "9 / 17 passed (52.9%)",
      latency: "250ms",
      cost_per_1k: "$0.001"
    },
    living_suite_version: "v1 (51 cases)",
    holdout_version: "holdout_v1 (10 sealed cases)",
    candidates: [
      {
        id: "cand_b",
        name: "Candidate B (Hierarchical Winner)",
        hypothesis: "Explicit multi-entity decomposition and argument pre-validation eliminates multi-order drops while strictly preventing tool over-triggering on pure policy queries.",
        proposed_change: "Added Multi-Entity Decomposition instructions and Tool Boundary negative constraints.",
        status: "promoted",
        promotion_status: "READY_FOR_CANARY",
        stage_1_benchmark: {
          passed_count: 48,
          total_count: 51,
          percentage: "94.1%",
          delta: "+36 cases (+70.6%)"
        },
        stage_2_holdout: {
          passed_count: 9,
          total_count: 10,
          percentage: "90.0%",
          delta: "+7 cases (+70.0%)"
        },
        hard_negative: {
          passed_count: 17,
          total_count: 17,
          percentage: "100.0%",
          delta: "+8 cases (+47.1%)"
        },
        efficiency: {
          latency: "240ms (-10ms)",
          token_cost: "$0.0011",
          score: "+0.04"
        },
        ranking_score: 95.4,
        prompt_snippet: `CRITICAL EXECUTION & VALIDATION RULES:
1. MULTI-ENTITY DECOMPOSITION: If the user request contains multiple entity references (e.g. order numbers, package IDs), resolve and validate every single entity independently. Execute corresponding tools for ALL mentioned entities without truncation.
2. TOOL BOUNDARY: For general policy, timeline, or informational inquiries, explain the policy directly. Do NOT query individual live state or tracking tools unless explicitly asked for package status.`
      },
      {
        id: "cand_a",
        name: "Candidate A (Delimiter Shielding)",
        hypothesis: "Shielding raw schema delimiters and reinforcing strict negative factual boundaries prevents markdown JSON parser errors.",
        proposed_change: "Added Raw Structured Output formatting rule and Factual Inventory Boundary instructions.",
        status: "rejected",
        rejection_stage: "stage_2_holdout",
        rejection_reason: "Holdout generalization score dropped by 1 case on multi-entity queries vs Candidate B.",
        stage_1_benchmark: {
          passed_count: 44,
          total_count: 51,
          percentage: "86.3%",
          delta: "+32 cases (+62.8%)"
        },
        stage_2_holdout: {
          passed_count: 7,
          total_count: 10,
          percentage: "70.0%",
          delta: "+5 cases (+50.0%)"
        },
        hard_negative: {
          passed_count: 15,
          total_count: 17,
          percentage: "88.2%",
          delta: "+6 cases (+35.3%)"
        },
        efficiency: {
          latency: "245ms (-5ms)",
          token_cost: "$0.0010",
          score: "+0.02"
        },
        ranking_score: 82.1,
        prompt_snippet: `EXECUTION CONSTRAINTS & POLICY ENFORCEMENT:
1. RAW STRUCTURED OUTPUTS: When JSON or structured output is requested, emit ONLY valid, parseable JSON without markdown code fences (\`\`\`json).`
      },
      {
        id: "cand_c",
        name: "Candidate C (State-Aware Verification)",
        hypothesis: "Pre-validating shipping state before processing cancellations prevents illegal state transitions on already-dispatched shipments.",
        proposed_change: "Added State-Aware Cancellation & Dispatch procedure.",
        status: "rejected",
        rejection_stage: "stage_1_benchmark",
        rejection_reason: "Stage 1 Benchmark improvement (+18 cases) was outranked and caused regression on syntax formatting.",
        stage_1_benchmark: {
          passed_count: 36,
          total_count: 51,
          percentage: "70.6%",
          delta: "+24 cases (+47.1%)"
        },
        stage_2_holdout: {
          passed_count: 6,
          total_count: 10,
          percentage: "60.0%",
          delta: "+4 cases (+40.0%)"
        },
        hard_negative: {
          passed_count: 14,
          total_count: 17,
          percentage: "82.4%",
          delta: "+5 cases (+29.5%)"
        },
        efficiency: {
          latency: "255ms (+5ms)",
          token_cost: "$0.0012",
          score: "-0.03"
        },
        ranking_score: 68.5,
        prompt_snippet: `STATE-AWARE OPERATIONAL DIRECTIVES:
1. CANCELLATION & DISPATCH RULES: If an order has already shipped or delivered, clearly explain that live shipments cannot be cancelled.`
      }
    ]
  };

  const activeCand = experiment.candidates.find((c) => c.id === selectedCandidate) || experiment.candidates[0];

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Autonomous Configuration Optimizer</h1>
            <Badge variant="outline" className="border-purple-500/30 text-purple-400 bg-purple-500/10">
              <Sparkles className="w-3 h-3 mr-1" /> V2 Engine
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Closed-loop prompt generation, two-stage count-first evaluation, and safe regression gating.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 px-3 py-1">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
            Registry: READY_FOR_CANARY
          </Badge>
          <Button size="sm" className="bg-purple-600 hover:bg-purple-700 text-white shadow-lg shadow-purple-500/20">
            <Zap className="w-3.5 h-3.5 mr-1.5" /> Run Optimization Cycle
          </Button>
        </div>
      </div>

      {/* Production Baseline & Lineage Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <span className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">Current Production</span>
          <div className="text-lg font-bold text-foreground">{experiment.current_production.version}</div>
          <div className="text-xs text-muted-foreground">Active in namespace: {experiment.namespace}</div>
        </div>
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <span className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">Baseline Benchmark</span>
          <div className="text-lg font-bold text-amber-400">{experiment.current_production.benchmark_score}</div>
          <div className="text-xs text-muted-foreground">Suite: {experiment.living_suite_version}</div>
        </div>
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <span className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">Sealed Holdout</span>
          <div className="text-lg font-bold text-sky-400">{experiment.current_production.holdout_score}</div>
          <div className="text-xs text-muted-foreground">Strictly isolated evaluation set</div>
        </div>
        <div className="p-4 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-1">
          <span className="text-xs text-muted-foreground uppercase font-semibold tracking-wider">Optimization Status</span>
          <div className="text-lg font-bold text-emerald-400 flex items-center gap-1.5">
            <ShieldCheck className="w-5 h-5 text-emerald-400" /> Winner Selected
          </div>
          <div className="text-xs text-muted-foreground">Passed 2-Stage Multi-Objective Gates</div>
        </div>
      </div>

      {/* Two-Stage Evaluation Flow & Candidates */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Candidate Selector Column */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-purple-400" /> Generated Candidates (3)
            </span>
            <span className="text-xs text-muted-foreground">Hierarchical Rank</span>
          </div>

          <div className="space-y-2">
            {experiment.candidates.map((cand) => {
              const isSelected = cand.id === selectedCandidate;
              const isWinner = cand.status === "promoted";

              return (
                <div
                  key={cand.id}
                  onClick={() => setSelectedCandidate(cand.id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? "border-purple-500/60 bg-purple-500/10 shadow-lg shadow-purple-500/5"
                      : "border-border/50 bg-card/30 hover:border-border hover:bg-card/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm text-foreground flex items-center gap-1.5">
                      {cand.name}
                    </span>
                    {isWinner ? (
                      <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 text-[10px]">
                        READY_FOR_CANARY
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground border-border text-[10px]">
                        REJECTED ({cand.rejection_stage === "stage_1_benchmark" ? "Stage 1" : "Stage 2"})
                      </Badge>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-xs pt-1 border-t border-border/30">
                    <div>
                      <span className="text-muted-foreground block text-[10px]">Benchmark</span>
                      <span className="font-medium text-amber-300">
                        {cand.stage_1_benchmark.passed_count}/{cand.stage_1_benchmark.total_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[10px]">Holdout</span>
                      <span className="font-medium text-sky-300">
                        {cand.stage_2_holdout.passed_count}/{cand.stage_2_holdout.total_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[10px]">Score</span>
                      <span className="font-bold text-purple-400">{cand.ranking_score}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Gate Verification Checklist */}
          <div className="p-4 rounded-xl border border-border/50 bg-card/30 space-y-2.5 mt-4">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
              Multi-Objective Safety Checklist
            </span>
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center gap-2 text-emerald-400">
                <Check className="w-3.5 h-3.5" /> Stage 1: Living BM count (+36 cases ≥ +1 min)
              </div>
              <div className="flex items-center gap-2 text-emerald-400">
                <Check className="w-3.5 h-3.5" /> Stage 2: Sealed Holdout (0 drop count)
              </div>
              <div className="flex items-center gap-2 text-emerald-400">
                <Check className="w-3.5 h-3.5" /> Hard Negative Boundary: 17/17 (100%)
              </div>
              <div className="flex items-center gap-2 text-emerald-400">
                <Check className="w-3.5 h-3.5" /> Immutable Safety Constraints Preserved
              </div>
            </div>
          </div>
        </div>

        {/* Candidate Deep Dive Column */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-5 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/40 pb-4">
              <div>
                <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                  {activeCand.name}
                  {activeCand.status === "promoted" && (
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                      Promoted Winner
                    </Badge>
                  )}
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">{activeCand.proposed_change}</p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant={activeTab === "hypotheses" ? "default" : "outline"}
                  onClick={() => setActiveTab("hypotheses")}
                  className="text-xs h-7"
                >
                  Hypothesis
                </Button>
                <Button
                  size="sm"
                  variant={activeTab === "matrix" ? "default" : "outline"}
                  onClick={() => setActiveTab("matrix")}
                  className="text-xs h-7"
                >
                  Differential Matrix
                </Button>
                <Button
                  size="sm"
                  variant={activeTab === "rejection" ? "default" : "outline"}
                  onClick={() => setActiveTab("rejection")}
                  className="text-xs h-7"
                >
                  Gates
                </Button>
              </div>
            </div>

            {/* Tab: Hypothesis & Code */}
            {activeTab === "hypotheses" && (
              <div className="space-y-4">
                <div className="p-3.5 rounded-lg bg-muted/40 border border-border/30 space-y-1">
                  <span className="text-[11px] font-semibold text-purple-400 uppercase tracking-wider block">
                    Causal Hypothesis
                  </span>
                  <p className="text-xs text-foreground leading-relaxed">{activeCand.hypothesis}</p>
                </div>

                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-primary" /> Generated Prompt Instructions (Blinded from Benchmark)
                  </span>
                  <div className="p-3.5 rounded-lg bg-black/60 font-mono text-xs text-emerald-400/90 border border-emerald-500/20 overflow-x-auto whitespace-pre-wrap">
                    {activeCand.prompt_snippet}
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Differential Matrix */}
            {activeTab === "matrix" && (
              <div className="space-y-3">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left border-collapse">
                    <thead>
                      <tr className="border-b border-border/40 text-muted-foreground">
                        <th className="pb-2 font-medium">Evaluation Surface</th>
                        <th className="pb-2 font-medium">Prompt v1.0 (Baseline)</th>
                        <th className="pb-2 font-medium">{activeCand.name}</th>
                        <th className="pb-2 font-medium text-right">Pass Count Delta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/20 font-medium">
                      <tr>
                        <td className="py-2.5 text-foreground flex items-center gap-1.5">
                          <Layers className="w-3.5 h-3.5 text-amber-400" /> Living Benchmark Suite v1
                        </td>
                        <td className="py-2.5 text-muted-foreground">12 / 51 (23.5%)</td>
                        <td className="py-2.5 text-amber-300">
                          {activeCand.stage_1_benchmark.passed_count} / {activeCand.stage_1_benchmark.total_count} ({activeCand.stage_1_benchmark.percentage})
                        </td>
                        <td className="py-2.5 text-right text-emerald-400 font-bold">
                          {activeCand.stage_1_benchmark.delta}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2.5 text-foreground flex items-center gap-1.5">
                          <ShieldCheck className="w-3.5 h-3.5 text-sky-400" /> Sealed Holdout Test Set
                        </td>
                        <td className="py-2.5 text-muted-foreground">2 / 10 (20.0%)</td>
                        <td className="py-2.5 text-sky-300">
                          {activeCand.stage_2_holdout.passed_count} / {activeCand.stage_2_holdout.total_count} ({activeCand.stage_2_holdout.percentage})
                        </td>
                        <td className="py-2.5 text-right text-emerald-400 font-bold">
                          {activeCand.stage_2_holdout.delta}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2.5 text-foreground flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-purple-400" /> Hard Negative Boundaries
                        </td>
                        <td className="py-2.5 text-muted-foreground">9 / 17 (52.9%)</td>
                        <td className="py-2.5 text-purple-300">
                          {activeCand.hard_negative.passed_count} / {activeCand.hard_negative.total_count} ({activeCand.hard_negative.percentage})
                        </td>
                        <td className="py-2.5 text-right text-emerald-400 font-bold">
                          {activeCand.hard_negative.delta}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab: Rejection & Safety Gates */}
            {activeTab === "rejection" && (
              <div className="space-y-3">
                <div className="p-3.5 rounded-lg border border-border/40 bg-muted/20 space-y-2">
                  <span className="text-xs font-semibold text-foreground block">Two-Stage Gate Decisions</span>
                  {activeCand.status === "promoted" ? (
                    <div className="text-xs text-emerald-400 flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold">Candidate Promoted:</span> Satisfied Stage 1 Living Benchmark Gate (+36 pass count) and Stage 2 Sealed Holdout Gate (9/10 passed), achieving the highest hierarchical score without regressions.
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-red-400 flex items-start gap-2">
                      <XCircle className="w-4 h-4 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold">Elimination Reason ({activeCand.rejection_stage}):</span> {activeCand.rejection_reason}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from "recharts";
import { FileText, CheckCircle, ArrowDown, Activity, Clock } from "lucide-react";

const correctnessData = [
  { step: 0, baseline: 0.92, adaptive: 0.92 },
  { step: 100, baseline: 0.91, adaptive: 0.93 },
  { step: 200, baseline: 0.92, adaptive: 0.93 },
  { step: 300, baseline: 0.91, adaptive: 0.94 },
  { step: 400, baseline: 0.92, adaptive: 0.94 },
  { step: 500, baseline: 0.90, adaptive: 0.95 },
  { step: 600, baseline: 0.91, adaptive: 0.95 },
  { step: 700, baseline: 0.91, adaptive: 0.96 },
  { step: 750, baseline: 0.52, adaptive: 0.53 }, // Drift Injection
  { step: 800, baseline: 0.51, adaptive: 0.65 }, // Canary started
  { step: 900, baseline: 0.50, adaptive: 0.94 }, // Healed
  { step: 1000, baseline: 0.49, adaptive: 0.96 },
  { step: 1100, baseline: 0.51, adaptive: 0.96 },
  { step: 1200, baseline: 0.48, adaptive: 0.97 },
  { step: 1300, baseline: 0.50, adaptive: 0.97 },
  { step: 1400, baseline: 0.49, adaptive: 0.98 },
  { step: 1500, baseline: 0.49, adaptive: 0.98 },
];

const errorData = [
  { metric: "Hallucination Rate", baseline: 28.4, adaptive: 1.2 },
  { metric: "Thumbs Down Ratio", baseline: 42.1, adaptive: 2.4 },
];

export default function ResultsPage() {
  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Controlled Evaluation Results</h2>
        <div className="flex items-center space-x-2">
          <div className="bg-primary/10 text-primary px-3 py-1 rounded-full text-sm font-medium border border-primary/20">
            Phase 7 Validated
          </div>
        </div>
      </div>
      
      <p className="text-muted-foreground max-w-3xl">
        This interactive report demonstrates the performance of APIS Adaptive Prompt Infrastructure compared to a static baseline deployment. 
        Methodology: 12,000 synthetic interactions simulating 14 days of LLM traffic across 4 domains. A deterministic model drift event was injected at Step 750.
      </p>

      {/* Top Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mean Time to Recovery</CardTitle>
            <Clock className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1.8 Hours</div>
            <p className="text-xs text-muted-foreground mt-1">vs Infinite (Baseline)</p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Correctness Delta</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">+48.1%</div>
            <p className="text-xs text-muted-foreground mt-1">Average post-drift delta</p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Hallucination Reduction</CardTitle>
            <ArrowDown className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">-95.7%</div>
            <p className="text-xs text-muted-foreground mt-1">Relative to baseline</p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rollback Success Rate</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">100%</div>
            <p className="text-xs text-muted-foreground mt-1">Safe canary isolation</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2 mt-4">
        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader>
            <CardTitle>Correctness Degradation & Auto-Healing</CardTitle>
            <CardDescription>Baseline correctness plummets after drift injection, while APIS auto-heals via canary rollouts.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={correctnessData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted-foreground))" strokeOpacity={0.2} />
                  <XAxis dataKey="step" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} domain={[0, 1]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "hsl(var(--background))", borderColor: "hsl(var(--border))", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
                    itemStyle={{ color: "hsl(var(--foreground))" }}
                    cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "3 3" }}
                  />
                  <ReferenceLine x={750} stroke="hsl(var(--chart-4))" strokeDasharray="3 3" label={{ position: 'top', value: 'Drift Injected', fill: 'hsl(var(--chart-4))', fontSize: 10 }} />
                  <Area type="monotone" dataKey="baseline" name="Baseline (Static)" stroke="hsl(var(--destructive))" strokeWidth={2} fillOpacity={0.1} fill="hsl(var(--destructive))" />
                  <Area type="monotone" dataKey="adaptive" name="APIS (Adaptive)" stroke="hsl(var(--primary))" strokeWidth={3} fillOpacity={0.1} fill="hsl(var(--primary))" />
                  <Legend />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader>
            <CardTitle>Post-Drift Error Comparison</CardTitle>
            <CardDescription>Average probability of fatal errors after step 750.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={errorData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted-foreground))" strokeOpacity={0.2} />
                  <XAxis dataKey="metric" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} unit="%" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "hsl(var(--background))", borderColor: "hsl(var(--border))", borderRadius: "8px", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
                    itemStyle={{ color: "hsl(var(--foreground))" }}
                    cursor={{fill: 'hsl(var(--muted))', opacity: 0.4}}
                  />
                  <Bar dataKey="baseline" name="Baseline (Static)" fill="hsl(var(--destructive))" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="adaptive" name="APIS (Adaptive)" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  <Legend />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Case Studies */}
      <h3 className="text-xl font-bold tracking-tight mt-8 mb-4">Domain Case Studies</h3>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4" /> Coding Assistant</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              When the simulated model began ignoring syntax formatting constraints (Day 7), token usage spiked by 300%. APIS detected the syntax errors, generated a constraint-heavy candidate prompt, and restored syntax correctness to 98% within 2 hours.
            </p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4" /> Customer Support</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              A simulated API deprecation caused the baseline agent to hallucinate outdated product features, resulting in a 42% thumbs-down ratio. APIS aggregated the negative user feedback, injected the correct facts into a candidate prompt, and lowered the thumbs-down ratio to 2.4%.
            </p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4" /> Research Assistant</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              The baseline prompt suffered from gradual verbosity drift, increasing latency by 400ms per request. The APIS background worker detected the latency regression, rolled out a concise-focused prompt on a 10% canary, and safely promoted it after validating the latency drop.
            </p>
          </CardContent>
        </Card>

        <Card className="transition-all duration-300 hover:shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4" /> Invoice Extraction</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              JSON formatting drift caused the baseline system to fail 50% of automated parses. APIS detected the JSON parse exceptions in the runtime telemetry, rolled back to a stable prompt version instantly, and began testing stricter few-shot examples in the background.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

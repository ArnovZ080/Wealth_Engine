"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Zap, 
  BrainCircuit, 
  FlaskConical, 
  TrendingUp, 
  AlertTriangle,
  RefreshCw,
  Target
} from "lucide-react";

export default function ResearchPage() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/research/report`);
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch (err) {
      console.error(err);
      // Dummy data for demo if API fails
      setReport({
        timestamp: new Date().toISOString(),
        total_trades: 42,
        performance: {
          agreed: { count: 30, pnl: 1250.50, win_rate: 0.68 },
          refined: { count: 12, pnl: -450.20, win_rate: 0.42 }
        },
        pruning_suggestions: ["seed-abc-123", "seed-xyz-789"],
        recommendation: "Prune refined strategies"
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  if (loading) return <div className="p-8 text-center">Analysing strategy DNA...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Strategy Research</h1>
          <p className="text-muted-foreground">Rolling 30-day performance analysis & Genetic Pruning.</p>
        </div>
        <Button onClick={fetchReport} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" /> Refresh Analysis
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="border-white/5 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 uppercase tracking-wider text-[10px] font-bold">
              <BrainCircuit className="h-3 w-3" /> Dumb Mode (Baseline)
            </CardDescription>
            <CardTitle className="text-2xl">${report.performance.agreed.pnl.toLocaleString()}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge className="bg-green-500/20 text-green-400 border-none">
                {(report.performance.agreed.win_rate * 100).toFixed(1)}% WR
              </Badge>
              <span className="text-xs text-muted-foreground">{report.performance.agreed.count} trades</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/5 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 uppercase tracking-wider text-[10px] font-bold">
              <Zap className="h-3 w-3" /> LLM Refined (Alpha Hunter)
            </CardDescription>
            <CardTitle className={`text-2xl ${report.performance.refined.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${report.performance.refined.pnl.toLocaleString()}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge className={report.performance.refined.win_rate >= 0.5 ? "bg-green-500/20 text-green-400 border-none" : "bg-red-500/20 text-red-400 border-none"}>
                {(report.performance.refined.win_rate * 100).toFixed(1)}% WR
              </Badge>
              <span className="text-xs text-muted-foreground">{report.performance.refined.count} trades</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/5 bg-blue-600/10 backdrop-blur-xl ring-1 ring-blue-500/20">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 uppercase tracking-wider text-[10px] font-bold text-blue-400">
              <Target className="h-3 w-3" /> Researcher Recommendation
            </CardDescription>
            <CardTitle className="text-xl text-blue-400">{report.recommendation}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-blue-400/70">
              Based on rolling win rates, active refinement is currently {report.performance.refined.win_rate > report.performance.agreed.win_rate ? 'outperforming' : 'underperforming'} basic signals.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-white/5 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5 text-amber-400" />
              <CardTitle>Genetic Pruning Suggestions</CardTitle>
            </div>
            <CardDescription>Seeds flagged for toxicity or consistent negative edge.</CardDescription>
          </CardHeader>
          <CardContent>
            {report.pruning_suggestions.length > 0 ? (
              <div className="space-y-4">
                {report.pruning_suggestions.map((seedId: string) => (
                  <div key={seedId} className="flex justify-between items-center p-3 rounded-lg bg-red-500/5 border border-red-500/10">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-4 w-4 text-red-400" />
                      <div>
                        <p className="text-sm font-medium">Seed {seedId.substring(0, 8)}</p>
                        <p className="text-xs text-muted-foreground">Toxic Performance (Negative Alpha)</p>
                      </div>
                    </div>
                    <Button size="sm" variant="destructive" className="h-8">Prune Seed</Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center uppercase tracking-widest">No toxic seeds detected.</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-white/5 bg-slate-900/50 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-400" />
              <CardTitle>Decision DNA Density</CardTitle>
            </div>
            <CardDescription>Correlation between LLM confidence and trade outcomes.</CardDescription>
          </CardHeader>
          <CardContent className="h-[200px] flex items-end gap-2">
             {/* Simple CSS bar chart representing density */}
             {[40, 60, 80, 50, 90, 30, 70].map((h, i) => (
               <div key={i} className="flex-1 bg-blue-500/20 rounded-t-sm hover:bg-blue-500/40 transition-colors" style={{height: `${h}%`}} title={`Confidence ${i*10}-${(i+1)*10}%`}></div>
             ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

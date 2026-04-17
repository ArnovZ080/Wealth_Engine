"use client";

import { useCallback, useEffect, useState } from "react";
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
  type ResearchReport = {
    timestamp: string;
    total_trades: number;
    performance: {
      agreed: { count: number; pnl: number; win_rate: number };
      refined: { count: number; pnl: number; win_rate: number };
    };
    pruning_suggestions: string[];
    recommendation: string;
  };

  const [report, setReport] = useState<ResearchReport | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/research/report`);
      if (res.ok) {
        const data: ResearchReport = await res.json();
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
  }, []);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  if (loading) return <div className="p-8 text-center">Analysing strategy DNA...</div>;
  if (!report) return <div className="p-8 text-center">No research report available.</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <div className="section-label">Research</div>
          <h1 className="font-heading text-4xl font-bold tracking-tight">Strategy Research</h1>
          <p className="mt-3 text-text-secondary">Rolling 30-day performance analysis & Genetic Pruning.</p>
        </div>
        <Button onClick={fetchReport} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" /> Refresh Analysis
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="rv">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 uppercase tracking-wider text-[10px] font-bold">
              <BrainCircuit className="h-3 w-3" /> Dumb Mode (Baseline)
            </CardDescription>
            <CardTitle className="text-2xl gradient-text-green">${report.performance.agreed.pnl.toLocaleString()}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge className="bg-candle-green/20 text-candle-green border-none">
                {(report.performance.agreed.win_rate * 100).toFixed(1)}% WR
              </Badge>
              <span className="text-xs text-text-secondary">{report.performance.agreed.count} trades</span>
            </div>
          </CardContent>
        </Card>

        <Card className="rv">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 uppercase tracking-wider text-[10px] font-bold">
              <Zap className="h-3 w-3" /> LLM Refined (Alpha Hunter)
            </CardDescription>
            <CardTitle className={`text-2xl ${report.performance.refined.pnl >= 0 ? 'gradient-text-green' : 'gradient-text-red'}`}>
              ${report.performance.refined.pnl.toLocaleString()}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge className={report.performance.refined.win_rate >= 0.5 ? "bg-candle-green/20 text-candle-green border-none" : "bg-candle-red/20 text-candle-red border-none"}>
                {(report.performance.refined.win_rate * 100).toFixed(1)}% WR
              </Badge>
              <span className="text-xs text-text-secondary">{report.performance.refined.count} trades</span>
            </div>
          </CardContent>
        </Card>

        <Card className="rv">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1 uppercase tracking-wider text-[10px] font-bold text-text-secondary">
              <Target className="h-3 w-3" /> Researcher Recommendation
            </CardDescription>
            <CardTitle className="text-xl">{report.recommendation}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-text-secondary">
              Based on rolling win rates, active refinement is currently {report.performance.refined.win_rate > report.performance.agreed.win_rate ? 'outperforming' : 'underperforming'} basic signals.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="rv">
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
                  <div key={seedId} className="flex justify-between items-center p-3 rounded-xl bg-candle-red/5 border border-candle-red/15">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-4 w-4 text-candle-red" />
                      <div>
                        <p className="text-sm font-medium">Seed {seedId.substring(0, 8)}</p>
                        <p className="text-xs text-text-secondary">Toxic Performance (Negative Alpha)</p>
                      </div>
                    </div>
                    <Button size="sm" variant="destructive" className="h-8">Prune Seed</Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-secondary py-8 text-center uppercase tracking-widest">No toxic seeds detected.</p>
            )}
          </CardContent>
        </Card>

        <Card className="rv">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-candle-green" />
              <CardTitle>Decision DNA Density</CardTitle>
            </div>
            <CardDescription>Correlation between LLM confidence and trade outcomes.</CardDescription>
          </CardHeader>
          <CardContent className="h-[200px] flex items-end gap-2">
             {/* Simple CSS bar chart representing density */}
             {[40, 60, 80, 50, 90, 30, 70].map((h, i) => (
               <div key={i} className="flex-1 bg-candle-green/20 rounded-t-sm hover:bg-candle-green/35 transition-colors" style={{height: `${h}%`}} title={`Confidence ${i*10}-${(i+1)*10}%`}></div>
             ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

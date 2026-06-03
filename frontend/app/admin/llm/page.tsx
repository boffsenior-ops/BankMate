"use client";

import React, { useEffect, useState } from "react";
import { adminApi } from "@/lib/api";
import { ShieldCheck, Activity, BrainCircuit, Server, Zap, RotateCcw, ShieldAlert, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LLMStatusPage() {
  const [loading, setLoading] = useState(true);
  const [statuses, setStatuses] = useState<any[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [st, us] = await Promise.all([
        adminApi.getProviderStatuses(),
        adminApi.getLLMUsage(),
      ]);
      setStatuses(st);
      setUsage(us);
    } catch (err) {
      console.error("Xatolik:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (name: string) => {
    setTestingProvider(name);
    setTestResult(null);
    try {
      const res = await adminApi.testProvider(name);
      setTestResult({ provider: name, ...res });
    } catch (err: any) {
      setTestResult({ provider: name, success: false, reason: err.message });
    } finally {
      setTestingProvider(null);
      loadData(); // refreshing cooldown status if any
    }
  };

  if (loading && !statuses.length) {
    return <div className="p-8 text-white">Yuklanmoqda...</div>;
  }

  return (
    <div className="p-8 max-w-6xl text-slate-100">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BrainCircuit className="h-6 w-6 text-indigo-400" />
            LLM Router va Status
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Faol LLM provayderlar va API token xarajatlari
          </p>
        </div>
        <Button onClick={loadData} variant="outline" className="border-slate-800 bg-slate-900">
          <RotateCcw className="h-4 w-4 mr-2" /> Yangilash
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Provayderlar Holati */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Server className="h-5 w-5 text-blue-400" /> Provayderlar navbati
          </h2>
          <div className="space-y-3">
            {statuses.map((s, idx) => (
              <div key={s.name} className={`flex items-center justify-between p-3 rounded-lg border ${s.in_cooldown ? 'bg-rose-500/10 border-rose-500/20' : 'bg-slate-950 border-slate-800'}`}>
                <div className="flex items-center gap-3">
                  <div className="h-6 w-6 rounded bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">
                    {idx + 1}
                  </div>
                  <div>
                    <p className="font-medium text-sm text-white">{s.display}</p>
                    {s.in_cooldown ? (
                      <p className="text-xs text-rose-400 flex items-center gap-1 mt-0.5">
                        <ShieldAlert className="h-3 w-3" /> Cooldown ({s.cooldown_ttl_sec}s)
                      </p>
                    ) : (
                      <p className="text-xs text-emerald-400 flex items-center gap-1 mt-0.5">
                        <CheckCircle className="h-3 w-3" /> Tayyor
                      </p>
                    )}
                  </div>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="border-slate-700 bg-slate-800 text-xs h-7"
                  onClick={() => handleTest(s.name)}
                  disabled={testingProvider === s.name}
                >
                  {testingProvider === s.name ? "Sinov..." : "Test"}
                </Button>
              </div>
            ))}
          </div>

          {testResult && (
            <div className={`mt-4 p-3 rounded-lg border text-sm ${testResult.success ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200' : 'bg-rose-500/10 border-rose-500/20 text-rose-200'}`}>
              <div className="font-semibold mb-1 flex justify-between">
                <span>{testResult.provider} test natijasi</span>
                <span>{testResult.latency_ms}ms</span>
              </div>
              <p className="text-xs opacity-90">{testResult.success ? testResult.response : `Xatolik: ${testResult.reason}`}</p>
            </div>
          )}
        </div>

        {/* Xarajatlar va Statistika */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-400" /> Token va Xarajat (Oxirgi 30 kun)
          </h2>
          
          <div className="space-y-4">
            {usage?.providers?.map((u: any) => (
              <div key={u.provider} className="bg-slate-950 border border-slate-800 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <p className="font-medium text-white capitalize">{u.provider}</p>
                  <p className="font-mono text-emerald-400 font-semibold">${u.total_cost_usd.toFixed(4)}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-xs text-slate-400">
                  <div className="flex justify-between">
                    <span>So'rovlar:</span>
                    <span className="text-slate-200">{u.requests_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>O'rtacha tezlik:</span>
                    <span className="text-slate-200">{u.avg_latency_ms} ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Input Token:</span>
                    <span className="text-slate-200">{u.total_prompt_tokens.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Output Token:</span>
                    <span className="text-slate-200">{u.total_completion_tokens.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between col-span-2 mt-1 pt-1 border-t border-slate-800">
                    <span className="text-amber-400/80">Zaxira sifatida ishladi (Failover):</span>
                    <span className="text-amber-400 font-medium">{u.failover_count} marta</span>
                  </div>
                </div>
              </div>
            ))}
            
            {(!usage?.providers || usage.providers.length === 0) && (
              <p className="text-sm text-slate-500 text-center py-8">Hozircha xarajat ma'lumotlari yo'q</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

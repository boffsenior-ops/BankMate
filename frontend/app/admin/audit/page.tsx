"use client";

import React, { useEffect, useState } from "react";
import { useToastStore } from "@/store/toastStore";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollText, Search, Download, RefreshCw, Filter } from "lucide-react";
import { cn } from "@/lib/utils";

interface AuditLog {
  id: number;
  user_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  metadata: Record<string, any> | null;
  created_at: string;
}

const ACTION_COLORS: Record<string, string> = {
  LOGIN_SUCCESS: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  LOGIN_FAILED: "text-rose-400 bg-rose-500/10 border-rose-500/30",
  LOGIN_RATE_LIMITED: "text-orange-400 bg-orange-500/10 border-orange-500/30",
  LOGOUT: "text-slate-400 bg-slate-800 border-slate-700",
  USER_CREATED: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  USER_UPDATED: "text-sky-400 bg-sky-500/10 border-sky-500/30",
  USER_DEACTIVATED: "text-rose-400 bg-rose-500/10 border-rose-500/30",
  PASSWORD_RESET: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  DOCUMENT_UPLOADED: "text-violet-400 bg-violet-500/10 border-violet-500/30",
  DOCUMENT_DELETED: "text-rose-400 bg-rose-500/10 border-rose-500/30",
  ADMIN_STATS_VIEW: "text-slate-400 bg-slate-800 border-slate-700",
};

export default function AuditPage() {
  const { toast } = useToastStore();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (actionFilter) params.set("action", actionFilter);
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      params.set("limit", "200");
      const res = await fetch(`/api/admin/audit-logs?${params}`);
      const data = await res.json();
      setLogs(Array.isArray(data) ? data : []);
    } catch {
      toast({ title: "Xatolik yuz berdi", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      // Direct call to backend (via cookie auth — works from SSR context only)
      // We use a simple window.open trick or re-fetch
      const token = document.cookie.split("; ").find((r) => r.startsWith("access_token="))?.split("=")[1];
      const res = await fetch(`/api/admin/audit-logs/export?${params}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast({ title: "Export xatoligi", variant: "destructive" });
    }
  };

  const filtered = logs.filter((log) => {
    const q = search.toLowerCase();
    return (
      log.action.toLowerCase().includes(q) ||
      (log.resource_type || "").toLowerCase().includes(q) ||
      (log.ip_address || "").includes(q) ||
      String(log.user_id || "").includes(q)
    );
  });

  return (
    <div className="p-8 max-w-7xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ScrollText className="h-6 w-6 text-amber-400" />
            Audit log
          </h1>
          <p className="text-slate-400 text-sm mt-1">{logs.length} ta yozuv • Barcha tizim harakatlari</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={load} variant="outline" size="sm" className="border-slate-800 bg-slate-900 text-slate-300 hover:text-white">
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button onClick={handleExport} variant="outline" size="sm" className="border-slate-800 bg-slate-900 text-slate-300 hover:text-white">
            <Download className="h-4 w-4 mr-2" />
            CSV
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-5 p-4 rounded-xl border border-slate-800 bg-slate-900/50">
        <Filter className="h-4 w-4 text-slate-500 shrink-0" />
        <div className="relative flex-1 min-w-40 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Qidirish..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 border-slate-800 bg-slate-950/80 text-white placeholder-slate-500 h-8 text-sm"
          />
        </div>
        <Input
          placeholder="Harakat turi"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="border-slate-800 bg-slate-950/80 text-white placeholder-slate-500 h-8 text-sm w-44"
        />
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>Dan:</span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="rounded border border-slate-800 bg-slate-950 text-slate-300 px-2 py-1 text-xs"
          />
          <span>Gacha:</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="rounded border border-slate-800 bg-slate-950 text-slate-300 px-2 py-1 text-xs"
          />
        </div>
        <Button onClick={load} size="sm" className="bg-blue-600 hover:bg-blue-500 text-white h-8 text-xs px-3">
          Filtrlash
        </Button>
      </div>

      {/* Log Table */}
      <div className="rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-slate-950/80">
            <tr className="text-left text-[11px] text-slate-500 uppercase tracking-wider">
              <th className="px-4 py-3 w-16">#</th>
              <th className="px-4 py-3">Harakat</th>
              <th className="px-4 py-3">Resurs</th>
              <th className="px-4 py-3">User ID</th>
              <th className="px-4 py-3">IP manzil</th>
              <th className="px-4 py-3">Meta</th>
              <th className="px-4 py-3">Vaqt</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500">Yuklanmoqda...</td>
              </tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500">Yozuvlar topilmadi</td>
              </tr>
            )}
            {filtered.map((log) => {
              const actionStyle = ACTION_COLORS[log.action] || "text-slate-400 bg-slate-800 border-slate-700";
              return (
                <tr key={log.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="px-4 py-2.5 text-slate-600">{log.id}</td>
                  <td className="px-4 py-2.5">
                    <span className={cn("inline-block px-2 py-0.5 rounded-full border font-medium text-[10px] tracking-wide", actionStyle)}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-400">
                    {log.resource_type ? (
                      <span>
                        {log.resource_type}
                        {log.resource_id && <span className="text-slate-600"> #{log.resource_id}</span>}
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-slate-500">
                    {log.user_id ?? <span className="text-slate-700">—</span>}
                  </td>
                  <td className="px-4 py-2.5 text-slate-500 font-mono">{log.ip_address || "—"}</td>
                  <td className="px-4 py-2.5 text-slate-600 max-w-xs truncate">
                    {log.metadata && Object.keys(log.metadata).length > 0 ? (
                      <span className="font-mono text-[10px]" title={JSON.stringify(log.metadata)}>
                        {Object.entries(log.metadata)
                          .slice(0, 2)
                          .map(([k, v]) => `${k}=${v}`)
                          .join(", ")}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-slate-500 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString("uz-UZ", {
                      day: "2-digit", month: "2-digit", year: "numeric",
                      hour: "2-digit", minute: "2-digit",
                    })}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

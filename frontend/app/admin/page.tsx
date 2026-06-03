"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import {
  Users, FileText, MessageSquare, CheckCircle, Clock, TrendingUp, ShieldAlert, BarChart3,
} from "lucide-react";

interface Stats {
  users: number;
  documents: number;
  indexed_documents: number;
  pending_documents: number;
  conversations: number;
  messages: number;
}

function StatCard({
  label, value, icon: Icon, color, sub,
}: {
  label: string; value: number | string; icon: any; color: string; sub?: string;
}) {
  return (
    <div className={`relative overflow-hidden rounded-xl border p-5 bg-slate-900/70 border-slate-800/80 shadow-lg`}>
      <div className={`absolute inset-0 opacity-5 ${color}`} />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">{label}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${color} bg-opacity-15 border border-current border-opacity-20`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const { user } = useAuthStore();
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user && user.role !== "ADMIN" && user.role !== "CONTENT_MANAGER") {
      router.replace("/chat");
      return;
    }
    fetch("/api/admin/stats")
      .then((r) => r.json())
      .then((d) => { setStats(d); setLoading(false); })
      .catch(() => { setError("Ma'lumot yuklanmadi"); setLoading(false); });
  }, [user, router]);

  return (
    <div className="p-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-blue-400" />
          Admin Dashboard
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          BankMate tizimi holati — {new Date().toLocaleDateString("uz-UZ")}
        </p>
      </div>

      {loading && (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-28 rounded-xl bg-slate-800 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-4">
          <ShieldAlert className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {stats && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            <StatCard label="Foydalanuvchilar" value={stats.users} icon={Users} color="text-blue-400" />
            <StatCard label="Jami hujjatlar" value={stats.documents} icon={FileText} color="text-violet-400" />
            <StatCard
              label="Indekslangan"
              value={stats.indexed_documents}
              icon={CheckCircle}
              color="text-emerald-400"
              sub={`${stats.pending_documents} kutmoqda`}
            />
            <StatCard label="Suhbatlar" value={stats.conversations} icon={MessageSquare} color="text-sky-400" />
            <StatCard label="Xabarlar" value={stats.messages} icon={TrendingUp} color="text-amber-400" />
            <StatCard
              label="Kutilayotgan"
              value={stats.pending_documents}
              icon={Clock}
              color="text-orange-400"
              sub="Hujjatlar navbatda"
            />
          </div>

          {/* Quick Actions */}
          <div>
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Tezkor harakatlar</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { label: "LLM Holati", href: "/admin/llm", icon: BarChart3, desc: "Provayder va Xarajatlar" },
                { label: "Hujjat yuklash", href: "/admin/documents", icon: FileText, desc: "Yangi hujjat qo'shish" },
                { label: "Foydalanuvchi qo'shish", href: "/admin/users", icon: Users, desc: "Yangi xodim ro'yxatga olish" },
                { label: "Audit loglarni ko'rish", href: "/admin/audit", icon: ShieldAlert, desc: "Tizim harakatlarini tekshirish" },
              ].map((action) => (
                <button
                  key={action.href}
                  onClick={() => router.push(action.href)}
                  className="flex items-center gap-4 p-4 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-900 hover:border-blue-500/30 transition-all text-left group"
                >
                  <div className="h-10 w-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 group-hover:bg-blue-500/20 transition-colors shrink-0">
                    <action.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-white text-sm">{action.label}</p>
                    <p className="text-xs text-slate-500">{action.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import {
  LayoutDashboard,
  FileText,
  Users,
  ScrollText,
  MessageSquare,
  LogOut,
  ShieldCheck,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { label: "LLM Holati", href: "/admin/llm", icon: LayoutDashboard },
  { label: "Hujjatlar", href: "/admin/documents", icon: FileText },
  { label: "Foydalanuvchilar", href: "/admin/users", icon: Users },
  { label: "Audit log", href: "/admin/audit", icon: ScrollText },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const pathname = usePathname();
  const router = useRouter();

  // RBAC guard
  if (user && user.role !== "ADMIN" && user.role !== "CONTENT_MANAGER") {
    router.replace("/chat");
    return null;
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 flex flex-col border-r border-slate-800/60 bg-slate-950">
        {/* Logo */}
        <div className="p-5 border-b border-slate-800/60">
          <Link href="/admin" className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
              <ShieldCheck className="h-4 w-4 text-blue-400" />
            </div>
            <div>
              <p className="font-bold text-sm text-white">BankMate</p>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Admin Panel</p>
            </div>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href || (item.href !== "/admin" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                  active
                    ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                    : "text-slate-400 hover:text-white hover:bg-slate-900"
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.label}
                {active && <ChevronRight className="ml-auto h-3 w-3" />}
              </Link>
            );
          })}
        </nav>

        {/* Divider - Chat link */}
        <div className="px-3 pb-2">
          <Link
            href="/chat"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-500 hover:text-slate-300 hover:bg-slate-900 transition-all"
          >
            <MessageSquare className="h-4 w-4" />
            Chat sahifasiga o'tish
          </Link>
        </div>

        {/* User footer */}
        <div className="p-4 border-t border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <div className="h-7 w-7 rounded-full bg-blue-600/15 border border-blue-500/20 flex items-center justify-center text-[10px] font-bold text-blue-400 shrink-0">
              {user?.full_name?.slice(0, 2).toUpperCase() || "A"}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.full_name}</p>
              <p className="text-[10px] text-slate-500 truncate">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="p-1.5 text-slate-500 hover:text-rose-400 transition-colors rounded-md hover:bg-rose-500/10"
            title="Chiqish"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto bg-slate-900/30">{children}</main>
    </div>
  );
}

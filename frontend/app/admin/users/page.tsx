"use client";

import React, { useEffect, useState } from "react";
import { useToastStore } from "@/store/toastStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Users, Plus, Search, UserX, Key, Pencil, RefreshCw, ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface UserItem {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  branch_id: number | null;
  is_active: boolean;
  created_at: string;
}

const ROLES = ["USER", "BRANCH_MANAGER", "CONTENT_MANAGER", "AUDITOR", "ADMIN"];

const roleColors: Record<string, string> = {
  ADMIN: "text-rose-400 border-rose-500/30 bg-rose-500/10",
  CONTENT_MANAGER: "text-violet-400 border-violet-500/30 bg-violet-500/10",
  BRANCH_MANAGER: "text-blue-400 border-blue-500/30 bg-blue-500/10",
  AUDITOR: "text-amber-400 border-amber-500/30 bg-amber-500/10",
  USER: "text-slate-400 border-slate-700 bg-slate-800",
};

export default function UsersPage() {
  const { toast } = useToastStore();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", full_name: "", password: "", role: "USER" });
  const [creating, setCreating] = useState(false);

  // Edit dialog
  const [editUser, setEditUser] = useState<UserItem | null>(null);
  const [editForm, setEditForm] = useState({ full_name: "", role: "", is_active: true });
  const [editing, setEditing] = useState(false);

  // Reset password dialog
  const [resetUser, setResetUser] = useState<UserItem | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [resetting, setResetting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/admin/users");
      const data = await res.json();
      setUsers(Array.isArray(data) ? data : []);
    } catch {
      toast({ title: "Xatolik yuz berdi", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Xatolik");
      }
      toast({ title: "Foydalanuvchi yaratildi!" });
      setCreateOpen(false);
      setForm({ username: "", email: "", full_name: "", password: "", role: "USER" });
      load();
    } catch (err: any) {
      toast({ title: err.message, variant: "destructive" });
    } finally {
      setCreating(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser) return;
    setEditing(true);
    try {
      const res = await fetch(`/api/admin/users/${editUser.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm),
      });
      if (!res.ok) throw new Error("Yangilashda xatolik");
      toast({ title: "Foydalanuvchi yangilandi!" });
      setEditUser(null);
      load();
    } catch (err: any) {
      toast({ title: err.message, variant: "destructive" });
    } finally {
      setEditing(false);
    }
  };

  const handleDeactivate = async (u: UserItem) => {
    if (!confirm(`"${u.full_name}" ni o'chirishni tasdiqlaysizmi?`)) return;
    try {
      const res = await fetch(`/api/admin/users/${u.id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Xatolik");
      toast({ title: "Foydalanuvchi o'chirildi" });
      load();
    } catch {
      toast({ title: "Xatolik yuz berdi", variant: "destructive" });
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetUser) return;
    setResetting(true);
    try {
      const res = await fetch(`/api/admin/users/${resetUser.id}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: newPassword }),
      });
      if (!res.ok) throw new Error("Xatolik");
      toast({ title: "Parol yangilandi!" });
      setResetUser(null);
      setNewPassword("");
    } catch {
      toast({ title: "Xatolik yuz berdi", variant: "destructive" });
    } finally {
      setResetting(false);
    }
  };

  const filtered = users.filter(
    (u) =>
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="h-6 w-6 text-blue-400" />
            Foydalanuvchilar
          </h1>
          <p className="text-slate-400 text-sm mt-1">{users.length} ta xodim ro'yxatda</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={load} variant="outline" size="sm" className="border-slate-800 bg-slate-900 text-slate-300 hover:text-white">
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button onClick={() => setCreateOpen(true)} className="bg-blue-600 hover:bg-blue-500 text-white" size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Yangi foydalanuvchi
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-xs mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <Input
          placeholder="Qidirish..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9 border-slate-800 bg-slate-950/80 text-white placeholder-slate-500"
        />
      </div>

      {/* Table */}
      <div className="rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-950/80">
            <tr className="text-left text-xs text-slate-500 uppercase tracking-wider">
              <th className="px-4 py-3">Foydalanuvchi</th>
              <th className="px-4 py-3">Rol</th>
              <th className="px-4 py-3">Holat</th>
              <th className="px-4 py-3">Sana</th>
              <th className="px-4 py-3 text-right">Amallar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">Yuklanmoqda...</td>
              </tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">Foydalanuvchi topilmadi</td>
              </tr>
            )}
            {filtered.map((u) => (
              <tr key={u.id} className={cn("hover:bg-slate-900/40 transition-colors", !u.is_active && "opacity-50")}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-xs font-bold text-blue-400">
                      {u.full_name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium text-white">{u.full_name}</p>
                      <p className="text-xs text-slate-500">@{u.username} • {u.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={cn("inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border", roleColors[u.role] || roleColors.USER)}>
                    <ShieldCheck className="h-3 w-3" />
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <Badge variant="outline" className={cn("text-xs", u.is_active ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10" : "border-slate-700 text-slate-500")}>
                    {u.is_active ? "Faol" : "Nofaol"}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">
                  {new Date(u.created_at).toLocaleDateString("uz-UZ")}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => { setEditUser(u); setEditForm({ full_name: u.full_name, role: u.role, is_active: u.is_active }); }}
                      className="p-1.5 text-slate-500 hover:text-blue-400 hover:bg-blue-500/10 rounded-md transition-colors"
                      title="Tahrirlash"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setResetUser(u)}
                      className="p-1.5 text-slate-500 hover:text-amber-400 hover:bg-amber-500/10 rounded-md transition-colors"
                      title="Parolni tiklash"
                    >
                      <Key className="h-4 w-4" />
                    </button>
                    {u.is_active && (
                      <button
                        onClick={() => handleDeactivate(u)}
                        className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition-colors"
                        title="O'chirish"
                      >
                        <UserX className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="border-slate-800 bg-slate-950 text-slate-100 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Yangi foydalanuvchi</DialogTitle>
            <DialogDescription className="text-slate-400">Tizimga yangi xodim qo'shish</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-3 py-2">
            {[
              { id: "username", label: "Username", type: "text", key: "username" },
              { id: "full_name", label: "To'liq ism", type: "text", key: "full_name" },
              { id: "email", label: "Email", type: "email", key: "email" },
              { id: "password", label: "Parol", type: "password", key: "password" },
            ].map((f) => (
              <div key={f.id}>
                <Label className="text-slate-400 text-xs">{f.label}</Label>
                <Input
                  id={f.id}
                  type={f.type}
                  value={(form as any)[f.key]}
                  onChange={(e) => setForm((p) => ({ ...p, [f.key]: e.target.value }))}
                  required
                  className="mt-1 border-slate-800 bg-slate-900 text-white"
                />
              </div>
            ))}
            <div>
              <Label className="text-slate-400 text-xs">Rol</Label>
              <select
                value={form.role}
                onChange={(e) => setForm((p) => ({ ...p, role: e.target.value }))}
                className="w-full mt-1 rounded-md border border-slate-800 bg-slate-900 text-white px-3 py-2 text-sm"
              >
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)} className="border-slate-800 bg-slate-900 text-slate-300">
                Bekor
              </Button>
              <Button type="submit" disabled={creating} className="bg-blue-600 hover:bg-blue-500 text-white">
                {creating ? "Saqlanmoqda..." : "Yaratish"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editUser} onOpenChange={() => setEditUser(null)}>
        <DialogContent className="border-slate-800 bg-slate-950 text-slate-100 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Tahrirlash: {editUser?.username}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEdit} className="space-y-3 py-2">
            <div>
              <Label className="text-slate-400 text-xs">To'liq ism</Label>
              <Input
                value={editForm.full_name}
                onChange={(e) => setEditForm((p) => ({ ...p, full_name: e.target.value }))}
                className="mt-1 border-slate-800 bg-slate-900 text-white"
              />
            </div>
            <div>
              <Label className="text-slate-400 text-xs">Rol</Label>
              <select
                value={editForm.role}
                onChange={(e) => setEditForm((p) => ({ ...p, role: e.target.value }))}
                className="w-full mt-1 rounded-md border border-slate-800 bg-slate-900 text-white px-3 py-2 text-sm"
              >
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active_edit"
                checked={editForm.is_active}
                onChange={(e) => setEditForm((p) => ({ ...p, is_active: e.target.checked }))}
                className="accent-blue-500"
              />
              <Label htmlFor="is_active_edit" className="text-slate-300 text-sm cursor-pointer">Faol</Label>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditUser(null)} className="border-slate-800 bg-slate-900 text-slate-300">
                Bekor
              </Button>
              <Button type="submit" disabled={editing} className="bg-blue-600 hover:bg-blue-500 text-white">
                {editing ? "Saqlanmoqda..." : "Saqlash"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={!!resetUser} onOpenChange={() => setResetUser(null)}>
        <DialogContent className="border-slate-800 bg-slate-950 text-slate-100 max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white">Parolni tiklash</DialogTitle>
            <DialogDescription className="text-slate-400">{resetUser?.username} uchun yangi parol</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleResetPassword} className="space-y-3 py-2">
            <Input
              type="password"
              placeholder="Yangi parol"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              className="border-slate-800 bg-slate-900 text-white"
            />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setResetUser(null)} className="border-slate-800 bg-slate-900 text-slate-300">
                Bekor
              </Button>
              <Button type="submit" disabled={resetting} className="bg-amber-600 hover:bg-amber-500 text-white">
                {resetting ? "Tiklanmoqda..." : "Tiklash"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useToastStore } from "@/store/toastStore";
import {
  FileText, Trash2, Upload, Loader2, CheckCircle, Clock, XCircle, Search, RefreshCw, Activity
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface Document {
  id: number;
  title: string;
  category: string;
  status: string;
  version: number;
  created_at: string;
  indexed_at: string | null;
}

const CATEGORIES = ["credit", "aml", "products", "cards", "currency", "regulations", "other"];

const statusConfig: Record<string, { label: string; icon: any; cls: string }> = {
  indexed: { label: "Indekslangan", icon: CheckCircle, cls: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
  uploaded: { label: "Yuklangan", icon: Clock, cls: "text-amber-400 border-amber-500/30 bg-amber-500/10" },
  processing: { label: "Jarayonda", icon: Loader2, cls: "text-blue-400 border-blue-500/30 bg-blue-500/10" },
  failed: { label: "Xato", icon: XCircle, cls: "text-rose-400 border-rose-500/30 bg-rose-500/10" },
  deleted: { label: "O'chirilgan", icon: XCircle, cls: "text-slate-500 border-slate-700 bg-slate-900" },
};

export default function DocumentsPage() {
  const { toast } = useToastStore();
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");

  // Upload form state
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadCategory, setUploadCategory] = useState("credit");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Reindex state
  const [showReindexModal, setShowReindexModal] = useState(false);
  const [reindexStats, setReindexStats] = useState<{total: number, indexed: number, processing: number, pending: number, error: number} | null>(null);
  const [polling, setPolling] = useState(false);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      const res = await fetch(`/api/admin/documents?${params}`);
      const data = await res.json();
      setDocs(Array.isArray(data) ? data : []);
    } catch {
      toast({ title: "Xatolik yuz berdi", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDocs(); }, [category]);

  const handleReindexAll = async () => {
    if (!confirm("Barcha indekslanmagan hujjatlar qayta indekslanadi. Ishonchingiz komilmi?")) return;
    try {
      const res = await fetch("/api/admin/documents/reindex", { method: "POST" });
      if (!res.ok) throw new Error("Xatolik");
      setShowReindexModal(true);
      setPolling(true);
    } catch (err: any) {
      toast({ title: "Xatolik yuz berdi", variant: "destructive" });
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (polling && showReindexModal) {
      const fetchStats = async () => {
        try {
          const res = await fetch("/api/admin/documents/stats");
          const data = await res.json();
          setReindexStats(data);
          if (data.processing === 0 && data.pending === 0 && data.total > 0) {
            setPolling(false);
            loadDocs();
          }
        } catch (e) {}
      };
      fetchStats();
      interval = setInterval(fetchStats, 3000);
    }
    return () => clearInterval(interval);
  }, [polling, showReindexModal]);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setUploadFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"] },
    maxFiles: 1,
  });

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle.trim()) {
      toast({ title: "Fayl va sarlavha kiritilishi shart", variant: "destructive" });
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("title", uploadTitle);
      formData.append("category", uploadCategory);
      const res = await fetch("/api/admin/documents/upload", { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload xatosi");
      }
      toast({ title: "Hujjat muvaffaqiyatli yuklandi!" });
      setUploadFile(null);
      setUploadTitle("");
      setUploadCategory("credit");
      loadDocs();
    } catch (err: any) {
      toast({ title: err.message, variant: "destructive" });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`"${title}" hujjatini o'chirishni tasdiqlaysizmi?`)) return;
    try {
      const res = await fetch(`/api/admin/documents/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("O'chirishda xatolik");
      toast({ title: "Hujjat o'chirildi" });
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch {
      toast({ title: "O'chirishda xatolik yuz berdi", variant: "destructive" });
    }
  };

  const filtered = docs.filter(
    (d) => d.title.toLowerCase().includes(search.toLowerCase()) || d.category.includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="h-6 w-6 text-violet-400" />
            Hujjatlar boshqaruvi
          </h1>
          <p className="text-slate-400 text-sm mt-1">{docs.length} ta hujjat • Drag-and-drop yuklash</p>
        </div>
        <div className="flex gap-3">
          <Button onClick={handleReindexAll} variant="default" size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white border-0 shadow-lg shadow-emerald-900/20">
            <Activity className="h-4 w-4 mr-2" />
            Barchasini qayta indekslash
          </Button>
          <Button onClick={loadDocs} variant="outline" size="sm" className="border-slate-800 bg-slate-900 text-slate-300 hover:text-white">
            <RefreshCw className="h-4 w-4 mr-2" />
            Yangilash
          </Button>
        </div>
      </div>

      {/* Upload Form */}
      <div className="mb-8 p-6 rounded-xl border border-slate-800 bg-slate-900/50">
        <h2 className="text-sm font-semibold text-slate-300 mb-4 uppercase tracking-wider">Yangi hujjat yuklash</h2>
        <form onSubmit={handleUpload} className="space-y-4">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all",
              isDragActive
                ? "border-blue-500 bg-blue-500/10 text-blue-400"
                : uploadFile
                ? "border-emerald-500/50 bg-emerald-500/5 text-emerald-400"
                : "border-slate-700 hover:border-slate-600 text-slate-500"
            )}
          >
            <input {...getInputProps()} />
            <Upload className="h-8 w-8 mx-auto mb-2" />
            {uploadFile ? (
              <p className="font-medium text-sm">{uploadFile.name}</p>
            ) : isDragActive ? (
              <p className="text-sm">Faylni shu yerga tashlang...</p>
            ) : (
              <p className="text-sm">PDF yoki DOCX faylni tashlang yoki bosing</p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <Input
                placeholder="Hujjat sarlavhasi"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                className="border-slate-800 bg-slate-950/80 text-white placeholder-slate-500"
                required
              />
            </div>
            <select
              value={uploadCategory}
              onChange={(e) => setUploadCategory(e.target.value)}
              className="rounded-md border border-slate-800 bg-slate-950/80 text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <Button
            type="submit"
            disabled={uploading || !uploadFile}
            className="bg-blue-600 hover:bg-blue-500 text-white"
          >
            {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
            {uploading ? "Yuklanmoqda..." : "Yuklash"}
          </Button>
        </form>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Qidirish..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 border-slate-800 bg-slate-950/80 text-white placeholder-slate-500"
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-md border border-slate-800 bg-slate-950/80 text-white px-3 py-2 text-sm focus:outline-none"
        >
          <option value="">Barcha kategoriyalar</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Document list */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-slate-800/50 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-950/80">
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wider">
                <th className="px-4 py-3">Sarlavha</th>
                <th className="px-4 py-3">Kategoriya</th>
                <th className="px-4 py-3">Holat</th>
                <th className="px-4 py-3">Sana</th>
                <th className="px-4 py-3 text-right">Amal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    Hujjatlar topilmadi
                  </td>
                </tr>
              )}
              {filtered.map((doc) => {
                const st = statusConfig[doc.status] || statusConfig.uploaded;
                const StIcon = st.icon;
                return (
                  <tr key={doc.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-slate-500 shrink-0" />
                        <span className="text-white font-medium truncate max-w-xs">{doc.title}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className="border-slate-700 text-slate-400 text-xs">
                        {doc.category}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full border", st.cls)}>
                        <StIcon className="h-3 w-3" />
                        {st.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {new Date(doc.created_at).toLocaleDateString("uz-UZ")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.title)}
                        className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition-colors"
                        title="O'chirish"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Reindex Progress Modal */}
      <Dialog open={showReindexModal} onOpenChange={(open) => {
        if (!open) setPolling(false);
        setShowReindexModal(open);
      }}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-emerald-400" />
              Qayta indekslash jarayoni
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {reindexStats ? (
              <div className="space-y-6">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Jami hujjatlar:</span>
                  <span className="font-bold text-lg">{reindexStats.total}</span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-emerald-400 font-medium">Muvaffaqiyatli:</span>
                    <span>{reindexStats.indexed} ta</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                    <div 
                      className="bg-emerald-500 h-full transition-all duration-500 ease-out relative" 
                      style={{ width: `${reindexStats.total > 0 ? (reindexStats.indexed / reindexStats.total) * 100 : 0}%` }}
                    >
                      {polling && <div className="absolute top-0 left-0 right-0 bottom-0 bg-white/20 animate-pulse" />}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 pt-6 border-t border-slate-800/60">
                  <div className="text-center bg-slate-800/30 rounded-lg p-3">
                    <div className="text-3xl font-light text-blue-400 mb-1">{reindexStats.processing}</div>
                    <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Jarayonda</div>
                  </div>
                  <div className="text-center bg-slate-800/30 rounded-lg p-3">
                    <div className="text-3xl font-light text-amber-400 mb-1">{reindexStats.pending}</div>
                    <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Navbatda</div>
                  </div>
                  <div className="text-center bg-slate-800/30 rounded-lg p-3">
                    <div className="text-3xl font-light text-rose-400 mb-1">{reindexStats.error}</div>
                    <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Xato</div>
                  </div>
                </div>

                {!polling && reindexStats.processing === 0 && reindexStats.pending === 0 && (
                   <div className="mt-6 p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-center text-sm flex flex-col items-center justify-center gap-2">
                     <CheckCircle className="h-8 w-8 mb-1" />
                     <span className="font-medium">Barcha jarayonlar yakunlandi!</span>
                   </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="text-slate-400 text-sm">Ma'lumotlar olinmoqda...</span>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

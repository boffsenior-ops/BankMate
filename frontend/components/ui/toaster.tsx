"use client";

import { useToastStore } from "@/store/toastStore";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export function Toaster() {
  const { toasts, dismiss } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "relative flex w-full items-start justify-between gap-4 overflow-hidden rounded-md border p-4 shadow-lg transition-all duration-300 animate-in slide-in-from-bottom-5",
            t.variant === "destructive"
              ? "border-destructive/50 bg-destructive text-destructive-foreground"
              : "border-border bg-background text-foreground"
          )}
        >
          <div className="flex flex-col gap-1">
            {t.title && <h5 className="font-semibold text-sm">{t.title}</h5>}
            {t.description && <p className="text-xs opacity-90">{t.description}</p>}
          </div>
          <button
            onClick={() => dismiss(t.id)}
            className="rounded-md p-1 transition-colors hover:bg-black/10 text-current/50 hover:text-current"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

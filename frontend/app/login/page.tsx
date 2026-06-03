"use client";

import React, { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { useRouter } from "next/navigation";
import { uz } from "@/locales/uz";
import { ru } from "@/locales/ru";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToastStore } from "@/store/toastStore";
import { Globe, ShieldAlert } from "lucide-react";

export default function LoginPage() {
  const { login, language, setLanguage } = useAuthStore();
  const { toast } = useToastStore();
  const router = useRouter();
  
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const t = language === "uz" ? uz : ru;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setLoading(true);
    try {
      await login(username, password);
      toast({
        title: language === "uz" ? "Muvaffaqiyatli kirildi" : "Успешный вход",
        description: language === "uz" ? "Xush kelibsiz!" : "Добро пожаловать!",
      });
      router.push("/chat");
    } catch (err: any) {
      console.error(err);
      toast({
        title: t.auth.errorTitle,
        description: err.response?.data?.detail || t.auth.invalidCredentials,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleLanguage = () => {
    setLanguage(language === "uz" ? "ru" : "uz");
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center p-4 bg-radial from-slate-900 via-slate-950 to-black overflow-hidden">
      {/* Background patterns */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-40"></div>
      
      {/* Glow Effects */}
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-blue-500/10 blur-[128px]"></div>
      <div className="absolute bottom-1/4 right-1/4 h-96 w-96 rounded-full bg-teal-500/10 blur-[128px]"></div>

      {/* Language Switcher */}
      <div className="absolute top-4 right-4 z-10">
        <Button
          variant="outline"
          size="sm"
          onClick={toggleLanguage}
          className="flex items-center gap-2 border-slate-800 bg-slate-950/50 hover:bg-slate-900 text-slate-300 hover:text-white backdrop-blur-md"
        >
          <Globe className="h-4 w-4" />
          <span>{language === "uz" ? "Русский" : "O'zbekcha"}</span>
        </Button>
      </div>

      <Card className="relative w-full max-w-md border-slate-800/80 bg-slate-950/70 shadow-2xl backdrop-blur-xl animate-in fade-in-50 zoom-in-95 duration-500">
        <CardHeader className="space-y-2 text-center pb-4">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-400 border border-blue-500/30">
            <span className="font-extrabold text-xl tracking-wider">BM</span>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-white mt-2">
            {t.auth.loginTitle}
          </CardTitle>
          <CardDescription className="text-slate-400 text-sm">
            {t.auth.subtitle}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-slate-300">
                {t.auth.usernameLabel}
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="border-slate-800 bg-slate-900/50 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500/20"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-300">
                {t.auth.passwordLabel}
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="border-slate-800 bg-slate-900/50 text-white placeholder-slate-500 focus:border-blue-500 focus:ring-blue-500/20"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors duration-200 mt-2 shadow-lg shadow-blue-500/20"
            >
              {loading ? t.auth.loggingIn : t.auth.loginButton}
            </Button>
          </form>

          {/* Secure indicator */}
          <div className="flex items-center justify-center gap-1.5 mt-6 text-xs text-slate-500">
            <ShieldAlert className="h-3.5 w-3.5" />
            <span>Xavfsiz va shaxsiy ichki bank tizimi</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { create } from "zustand";
import { UserInfo } from "@/types";
import { authApi } from "@/lib/api";

interface AuthStoreState {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  language: "uz" | "ru";
  
  setLanguage: (lang: "uz" | "ru") => void;
  setUser: (user: UserInfo | null) => void;
  checkAuth: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthStoreState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  language: "uz", // default to Uzbek

  setLanguage: (lang) => {
    set({ language: lang });
    if (typeof window !== "undefined") {
      localStorage.setItem("bankmate_lang", lang);
    }
  },

  setUser: (user) => set({ user, isAuthenticated: !!user }),

  checkAuth: async () => {
    set({ isLoading: true });
    
    // Load local language preference
    if (typeof window !== "undefined") {
      const savedLang = localStorage.getItem("bankmate_lang") as "uz" | "ru";
      if (savedLang) {
        set({ language: savedLang });
      }
    }
    
    try {
      const data = await authApi.me();
      set({ user: data.user, isAuthenticated: true });
    } catch (err) {
      set({ user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },

  login: async (username, password) => {
    set({ isLoading: true });
    try {
      const data = await authApi.login(username, password);
      set({ user: data.user, isAuthenticated: true });
    } catch (err) {
      set({ user: null, isAuthenticated: false });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await authApi.logout();
    } catch (err) {
      console.error("Logout error", err);
    } finally {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));

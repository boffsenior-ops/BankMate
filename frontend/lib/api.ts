import axios from "axios";
import { Conversation, Message, UserInfo } from "@/types";

// Client-side API client calling Next.js API routes
const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export const authApi = {
  login: async (username: string, password: string): Promise<{ user: UserInfo }> => {
    const res = await api.post("/auth/login", { username, password });
    return res.data;
  },
  logout: async (): Promise<void> => {
    await api.post("/auth/logout");
  },
  me: async (): Promise<{ user: UserInfo }> => {
    const res = await api.get("/auth/me");
    return res.data;
  },
};

export const chatApi = {
  getConversations: async (): Promise<Conversation[]> => {
    const res = await api.get("/chat/conversations");
    return res.data;
  },
  getMessages: async (conversationId: number): Promise<Message[]> => {
    const res = await api.get(`/chat/conversations/${conversationId}/messages`);
    return res.data;
  },
  saveFeedback: async (messageId: number, feedback: "like" | "dislike"): Promise<void> => {
    await api.post(`/chat/messages/${messageId}/feedback`, { feedback });
  },
};

export const adminApi = {
  getLLMUsage: async () => {
    const res = await api.get("/admin/usage");
    return res.data;
  },
  getProviderStatuses: async () => {
    const res = await api.get("/admin/providers/status");
    return res.data;
  },
  testProvider: async (providerName: string) => {
    const res = await api.post(`/admin/providers/${providerName}/test`);
    return res.data;
  },
};

export default api;

export type Role = "USER" | "BRANCH_MANAGER" | "CONTENT_MANAGER" | "AUDITOR" | "ADMIN";

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: Role;
  branch_id?: number | null;
  is_active: boolean;
}

export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  document_id?: number;
  title: string;
  page_number: string | number;
  score?: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  sources_json?: Source[] | null;
  feedback?: "like" | "dislike" | null;
  provider?: string;
  provider_display?: string;
  was_failover?: boolean;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    cost_usd: number;
    latency_ms: number;
  };
  created_at: string;
}

export interface AuthState {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

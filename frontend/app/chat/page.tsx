"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuthStore } from "@/store/authStore";
import { chatApi } from "@/lib/api";
import { Conversation, Message, Source } from "@/types";
import { uz } from "@/locales/uz";
import { ru } from "@/locales/ru";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useToastStore } from "@/store/toastStore";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  MessageSquare,
  Send,
  LogOut,
  Globe,
  Plus,
  ThumbsUp,
  ThumbsDown,
  BookOpen,
  FileText,
  User,
  Bot,
  Loader2,
  Copy,
  Check,
  Menu,
} from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export default function ChatPage() {
  const { user, logout, language, setLanguage } = useAuthStore();
  const { toast } = useToastStore();
  const t = language === "uz" ? uz : ru;

  // Conversations and Messages States
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  // Modal State for Source Details
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);

  // References
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Fetch messages when active conversation changes
  useEffect(() => {
    if (activeConversationId) {
      loadMessages(activeConversationId);
    } else {
      setMessages([]);
    }
  }, [activeConversationId]);

  // Scroll to bottom on messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadConversations = async () => {
    try {
      const data = await chatApi.getConversations();
      setConversations(data);
    } catch (err) {
      console.error(err);
      toast({
        title: t.errors.general,
        variant: "destructive",
      });
    }
  };

  const loadMessages = async (id: number) => {
    try {
      const data = await chatApi.getMessages(id);
      setMessages(data);
    } catch (err) {
      console.error(err);
      toast({
        title: t.errors.general,
        variant: "destructive",
      });
    }
  };

  const handleStartNewChat = () => {
    if (isStreaming) return;
    setActiveConversationId(null);
    setMessages([]);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isStreaming) return;

    const userQuery = inputMessage.trim();
    setInputMessage("");

    // Create temporary message array
    const userMsg: Message = {
      id: Date.now(),
      conversation_id: activeConversationId || 0,
      role: "user",
      content: userQuery,
      created_at: new Date().toISOString(),
    };

    const aiMsgPlaceholder: Message = {
      id: Date.now() + 1,
      conversation_id: activeConversationId || 0,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, aiMsgPlaceholder]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userQuery,
          conversation_id: activeConversationId,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error("Stream connection failed");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No readable stream");

      const decoder = new TextDecoder();
      let buffer = "";
      let streamedContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6);
            if (dataStr === "[DONE]") continue;

            try {
              const data = JSON.parse(dataStr);
              if (data.type === "provider_start") {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.role === "assistant" && msg.id === aiMsgPlaceholder.id
                      ? { ...msg, provider: data.name, provider_display: data.display }
                      : msg
                  )
                );
              } else if (data.type === "token") {
                streamedContent += data.content;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.role === "assistant" && msg.id === aiMsgPlaceholder.id
                      ? { ...msg, content: streamedContent }
                      : msg
                  )
                );
              } else if (data.type === "usage") {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.role === "assistant" && msg.id === aiMsgPlaceholder.id
                      ? {
                          ...msg,
                          provider: data.provider || msg.provider,
                          provider_display: data.display || msg.provider_display,
                          was_failover: data.was_failover,
                          usage: {
                            prompt_tokens: data.prompt_tokens,
                            completion_tokens: data.completion_tokens,
                            cost_usd: data.cost_usd,
                            latency_ms: data.latency_ms,
                          },
                        }
                      : msg
                  )
                );
              } else if (data.type === "sources") {
                // Update final message properties including citations and database ids
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.role === "assistant" && msg.id === aiMsgPlaceholder.id
                      ? {
                          ...msg,
                          id: data.message_id || msg.id,
                          conversation_id: data.conversation_id,
                          sources_json: data.sources,
                        }
                      : msg
                  )
                );
                
                // If it's a new conversation, update active ID and refresh sidebar list
                if (!activeConversationId && data.conversation_id) {
                  setActiveConversationId(data.conversation_id);
                  loadConversations();
                }
              } else if (data.type === "error" || data.type === "all_failed" || data.type === "stream_broken") {
                toast({
                  title: t.errors.general,
                  description: data.content || "Stream failed or broken.",
                  variant: "destructive",
                });
              }
            } catch (e) {
              console.error("Parse line error:", e);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        console.log("Stream aborted by user");
      } else {
        console.error(err);
        toast({
          title: t.errors.general,
          variant: "destructive",
        });
        // Remove the placeholder assistant message if it failed
        setMessages((prev) => prev.filter((m) => m.id !== aiMsgPlaceholder.id));
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  };

  const handleCopyMessage = (id: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast({
      title: t.chat.copied,
    });
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleFeedback = async (messageId: number, feedbackType: "like" | "dislike") => {
    try {
      await chatApi.saveFeedback(messageId, feedbackType);
      setMessages((prev) =>
        prev.map((msg) => (msg.id === messageId ? { ...msg, feedback: feedbackType } : msg))
      );
      toast({
        title: feedbackType === "like" ? t.chat.feedbackLiked : t.chat.feedbackDisliked,
      });
    } catch (err) {
      console.error(err);
      toast({
        title: t.errors.general,
        variant: "destructive",
      });
    }
  };

  const openSourceModal = (source: Source) => {
    setSelectedSource(source);
    setIsSourceModalOpen(true);
  };

  // Group conversations by date (Bugun, Kecha, Bu hafta, Older)
  const groupConversations = () => {
    const today: Conversation[] = [];
    const yesterday: Conversation[] = [];
    const thisWeek: Conversation[] = [];
    const older: Conversation[] = [];

    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startOfYesterday = new Date(startOfToday.getTime() - 24 * 60 * 60 * 1000);
    const startOfWeek = new Date(startOfToday.getTime() - 7 * 24 * 60 * 60 * 1000);

    conversations.forEach((c) => {
      const date = new Date(c.updated_at);
      if (date >= startOfToday) {
        today.push(c);
      } else if (date >= startOfYesterday) {
        yesterday.push(c);
      } else if (date >= startOfWeek) {
        thisWeek.push(c);
      } else {
        older.push(c);
      }
    });

    return { today, yesterday, thisWeek, older };
  };

  const grouped = groupConversations();

  const SidebarContent = () => (
    <div className="flex h-full flex-col bg-slate-950 border-r border-slate-900">
      {/* Sidebar Header */}
      <div className="p-4 flex items-center justify-between border-b border-slate-900">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 font-black text-sm">
            BM
          </div>
          <span className="font-bold text-white tracking-wide">BankMate</span>
        </div>
        <Button
          onClick={handleStartNewChat}
          variant="outline"
          size="icon"
          className="border-slate-800 bg-slate-900/50 text-slate-300 hover:text-white"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* History scrollarea */}
      <ScrollArea className="flex-1 px-3 py-2">
        <div className="space-y-4">
          {/* Today */}
          {grouped.today.length > 0 && (
            <div>
              <div className="px-2 text-xs font-semibold text-slate-500 mb-1">{t.chat.today}</div>
              {grouped.today.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveConversationId(c.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all truncate flex items-center gap-2 ${
                    activeConversationId === c.id
                      ? "bg-blue-600/10 text-blue-400 font-medium border-l-2 border-blue-500 pl-2.5"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{c.title}</span>
                </button>
              ))}
            </div>
          )}

          {/* Yesterday */}
          {grouped.yesterday.length > 0 && (
            <div>
              <div className="px-2 text-xs font-semibold text-slate-500 mb-1">{t.chat.yesterday}</div>
              {grouped.yesterday.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveConversationId(c.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all truncate flex items-center gap-2 ${
                    activeConversationId === c.id
                      ? "bg-blue-600/10 text-blue-400 font-medium border-l-2 border-blue-500 pl-2.5"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{c.title}</span>
                </button>
              ))}
            </div>
          )}

          {/* This Week */}
          {grouped.thisWeek.length > 0 && (
            <div>
              <div className="px-2 text-xs font-semibold text-slate-500 mb-1">{t.chat.thisWeek}</div>
              {grouped.thisWeek.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveConversationId(c.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all truncate flex items-center gap-2 ${
                    activeConversationId === c.id
                      ? "bg-blue-600/10 text-blue-400 font-medium border-l-2 border-blue-500 pl-2.5"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{c.title}</span>
                </button>
              ))}
            </div>
          )}

          {/* Older */}
          {grouped.older.length > 0 && (
            <div>
              <div className="px-2 text-xs font-semibold text-slate-500 mb-1">{t.chat.older}</div>
              {grouped.older.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveConversationId(c.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all truncate flex items-center gap-2 ${
                    activeConversationId === c.id
                      ? "bg-blue-600/10 text-blue-400 font-medium border-l-2 border-blue-500 pl-2.5"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                >
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{c.title}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* User settings footer */}
      <div className="p-4 border-t border-slate-900 bg-slate-950/50 flex items-center justify-between">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 text-slate-300 hover:text-white transition-all text-left outline-none">
              <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-semibold border border-slate-700">
                {user?.full_name?.slice(0, 2).toUpperCase() || "U"}
              </div>
              <div className="flex-1 truncate">
                <p className="text-xs font-semibold truncate text-white">{user?.full_name}</p>
                <p className="text-[10px] text-slate-500 truncate">{user?.role}</p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 border-slate-800 bg-slate-950 text-slate-200">
            <DropdownMenuLabel>Mening profilim</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-slate-900" />
            <DropdownMenuItem
              onClick={() => setLanguage(language === "uz" ? "ru" : "uz")}
              className="flex items-center gap-2 focus:bg-slate-900 focus:text-white"
            >
              <Globe className="h-4 w-4" />
              <span>Til: {language === "uz" ? "Русский" : "O'zbekcha"}</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-slate-900" />
            <DropdownMenuItem
              onClick={logout}
              className="flex items-center gap-2 focus:bg-destructive/15 focus:text-destructive text-rose-400"
            >
              <LogOut className="h-4 w-4" />
              <span>{t.chat.logoutButton}</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col shrink-0">
        <SidebarContent />
      </div>

      {/* Main Container */}
      <div className="flex flex-1 flex-col overflow-hidden bg-slate-900/50">
        {/* Header */}
        <header className="flex h-14 items-center justify-between px-4 border-b border-slate-900 bg-slate-950/80 backdrop-blur-md z-10 shrink-0">
          <div className="flex items-center gap-3">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden text-slate-300 hover:text-white">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="p-0 border-none w-64 bg-slate-950">
                <SidebarContent />
              </SheetContent>
            </Sheet>
            
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-blue-400" />
              <h1 className="font-bold text-white tracking-wide">
                {activeConversationId ? conversations.find(c => c.id === activeConversationId)?.title : t.chat.newChat}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLanguage(language === "uz" ? "ru" : "uz")}
              className="border-slate-800 bg-slate-950/50 hover:bg-slate-900 text-slate-300 hover:text-white"
            >
              <Globe className="h-4 w-4 mr-1.5" />
              <span>{language === "uz" ? "RU" : "UZ"}</span>
            </Button>
          </div>
        </header>

        {/* Chat area */}
        <ScrollArea className="flex-1 p-4 md:p-6">
          {messages.length === 0 ? (
            <div className="flex h-[70vh] flex-col items-center justify-center text-center px-4 max-w-xl mx-auto">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-4 animate-bounce">
                <Bot className="h-8 w-8" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">{t.chat.emptyStateTitle}</h2>
              <p className="text-sm text-slate-400">{t.chat.emptyStateSubtitle}</p>
            </div>
          ) : (
            <div className="space-y-6 max-w-3xl mx-auto pb-8">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {/* Left Avatar for Bot */}
                  {msg.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}

                  {/* Message body */}
                  <div
                    className={`flex flex-col gap-2 max-w-[85%] rounded-xl px-4 py-3 border shadow-sm ${
                      msg.role === "user"
                        ? "bg-blue-600/15 border-blue-500/30 text-slate-100"
                        : "bg-slate-950/80 border-slate-800/80 text-slate-200"
                    }`}
                  >
                    <div className="prose prose-invert max-w-none text-sm leading-relaxed">
                      {msg.content === "" && isStreaming ? (
                        <div className="flex items-center gap-1.5 py-1 text-slate-400">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>{t.chat.loadingMessage}</span>
                        </div>
                      ) : (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      )}
                    </div>

                    {/* Citations section */}
                    {msg.role === "assistant" && msg.sources_json && msg.sources_json.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-900">
                        <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1">
                          <BookOpen className="h-3.5 w-3.5" />
                          <span>{t.chat.sourcesTitle}</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {msg.sources_json.map((source, index) => (
                            <Badge
                              key={index}
                              variant="outline"
                              onClick={() => openSourceModal(source)}
                              className="cursor-pointer border-slate-800 bg-slate-900 hover:bg-slate-800 text-xs text-blue-400 hover:text-blue-300 font-medium py-1 px-2.5 rounded-md flex items-center gap-1"
                            >
                              <FileText className="h-3 w-3" />
                              <span>{source.title.split("/").pop()}</span>
                              <span className="text-[10px] text-slate-500">p. {source.page_number}</span>
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Actions and feedback */}
                    {msg.role === "assistant" && msg.content !== "" && (
                      <div className="flex items-center justify-between gap-4 mt-2 pt-2 border-t border-slate-900/30 text-xs text-slate-500">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleCopyMessage(msg.id, msg.content)}
                            className="p-1 hover:text-white transition-colors"
                            title={t.chat.copyTooltip}
                          >
                            {copiedId === msg.id ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
                          </button>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          {msg.provider && (
                            <Badge variant="outline" className={`text-[10px] capitalize pointer-events-none ${msg.was_failover ? "bg-amber-500/10 text-amber-500 border-amber-500/20" : "text-slate-500 bg-slate-900 border-slate-800"}`}>
                              {msg.provider_display || msg.provider} {msg.was_failover && "(Failover)"}
                            </Badge>
                          )}
                          {msg.id && (
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => handleFeedback(msg.id, "like")}
                                className={`p-1 hover:text-white transition-colors rounded ${
                                  msg.feedback === "like" ? "text-green-400" : ""
                                }`}
                              >
                                <ThumbsUp className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={() => handleFeedback(msg.id, "dislike")}
                                className={`p-1 hover:text-white transition-colors rounded ${
                                  msg.feedback === "dislike" ? "text-rose-400" : ""
                                }`}
                              >
                                <ThumbsDown className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right Avatar for User */}
                  {msg.role === "user" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600/10 text-blue-400 border border-blue-500/20">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-900 bg-slate-950/40 shrink-0">
          <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto relative flex items-center gap-2">
            <Input
              type="text"
              placeholder={t.chat.inputPlaceholder}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              className="border-slate-800 bg-slate-950/80 text-white placeholder-slate-500 py-6 pr-12 focus:border-blue-500 focus:ring-blue-500/20"
            />
            <div className="absolute right-2 flex items-center gap-1">
              {isStreaming ? (
                <Button
                  type="button"
                  onClick={handleStopStreaming}
                  size="icon"
                  className="bg-rose-600 hover:bg-rose-500 text-white h-9 w-9 rounded-lg"
                  title={t.chat.stopTooltip}
                >
                  <Loader2 className="h-4 w-4 animate-spin" />
                </Button>
              ) : (
                <Button
                  type="submit"
                  disabled={!inputMessage.trim()}
                  size="icon"
                  className="bg-blue-600 hover:bg-blue-500 text-white h-9 w-9 rounded-lg disabled:opacity-50 disabled:bg-slate-800"
                  title={t.chat.sendTooltip}
                >
                  <Send className="h-4 w-4" />
                </Button>
              )}
            </div>
          </form>
        </div>
      </div>

      {/* Citation Dialog */}
      <Dialog open={isSourceModalOpen} onOpenChange={setIsSourceModalOpen}>
        <DialogContent className="border-slate-800 bg-slate-950 text-slate-100 max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white font-bold">
              <FileText className="h-5 w-5 text-blue-400" />
              <span>{t.chat.sourceModalTitle}</span>
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedSource?.title.split("/").pop()}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-3">
            <div className="flex justify-between text-sm border-b border-slate-900 pb-2">
              <span className="text-slate-400">Sahifa:</span>
              <span className="font-semibold text-white">{selectedSource?.page_number}</span>
            </div>
            {selectedSource?.score !== undefined && (
              <div className="flex justify-between text-sm border-b border-slate-900 pb-2">
                <span className="text-slate-400">{t.chat.sourceModalScore}:</span>
                <span className="font-semibold text-emerald-400">
                  {Math.round(selectedSource.score * 100)}%
                </span>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              onClick={() => setIsSourceModalOpen(false)}
              className="bg-blue-600 hover:bg-blue-500 text-white"
            >
              Yopish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

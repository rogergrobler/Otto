"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { sendMessage } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const STORAGE_KEY = "otto_chat_history";

function loadHistory(): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Array<{
      id: string;
      role: "user" | "assistant";
      content: string;
      timestamp: string;
    }>;
    return parsed.map((m) => ({ ...m, timestamp: new Date(m.timestamp) }));
  } catch {
    return [];
  }
}

function saveHistory(messages: Message[]) {
  if (typeof window === "undefined") return;
  // Keep last 100 messages
  const toSave = messages.slice(-100);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const history = loadHistory();
    if (history.length === 0) {
      // Welcome message
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content:
            "Hello! I'm Otto, your digital health twin. I can help you understand your health data, answer questions about your labs, nutrition, and wearable metrics. What would you like to know?",
          timestamp: new Date(),
        },
      ]);
    } else {
      setMessages(history);
    }
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    saveHistory(messages);
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const res = await sendMessage(text);
      const reply = res.reply || (res as unknown as { message?: string }).message || "I didn't get a response.";
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: reply,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message.");
      // Remove optimistic user message on failure
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
      setInput(text);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function formatTime(date: Date) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function clearHistory() {
    localStorage.removeItem(STORAGE_KEY);
    setMessages([
      {
        id: "welcome-new",
        role: "assistant",
        content: "Chat history cleared. How can I help you today?",
        timestamp: new Date(),
      },
    ]);
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#111111] border-b border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-full flex items-center justify-center">
            <span className="text-sm font-bold text-white">O</span>
          </div>
          <div>
            <p className="text-sm font-semibold">Otto</p>
            <p className="text-xs text-green-400">Online</p>
          </div>
        </div>
        <button
          onClick={clearHistory}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
        >
          Clear
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 pb-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mr-2 mt-1">
                <span className="text-xs font-bold text-white">O</span>
              </div>
            )}
            <div className={`max-w-[80%] space-y-1`}>
              <div
                className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-sm"
                    : "bg-[#1a1a1a] text-gray-100 rounded-bl-sm"
                }`}
                style={{ whiteSpace: "pre-wrap" }}
              >
                {msg.content}
              </div>
              <p
                className={`text-[10px] text-gray-600 ${
                  msg.role === "user" ? "text-right" : "text-left"
                }`}
              >
                {formatTime(msg.timestamp)}
              </p>
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex justify-start">
            <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mr-2 mt-1">
              <span className="text-xs font-bold text-white">O</span>
            </div>
            <div className="bg-[#1a1a1a] rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1 items-center h-4">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center">
            <p className="text-xs text-red-400 bg-red-500/10 px-3 py-1.5 rounded-lg">{error}</p>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-4 py-3 bg-[#111111] border-t border-gray-800 mb-16">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Otto anything…"
            rows={1}
            className="flex-1 bg-[#1a1a1a] border border-gray-800 rounded-2xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none text-sm leading-5 transition-colors"
            style={{ maxHeight: "120px", overflowY: "auto" }}
            onInput={(e) => {
              const el = e.currentTarget;
              el.style.height = "auto";
              el.style.height = Math.min(el.scrollHeight, 120) + "px";
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="w-10 h-10 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-white">
              <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

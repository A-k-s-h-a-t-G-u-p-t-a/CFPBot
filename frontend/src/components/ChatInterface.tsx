"use client";

import { useRef, useState, useEffect, useTransition } from "react";
import { IconSend, IconLoader2 } from "@tabler/icons-react";
import AnswerCard from "./AnswerCard";

// ── Types ───────────────────────────────────────────────────────────────────

interface DbMessage {
  id: string;
  role: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
  createdAt: Date | string;
}

interface ChatInterfaceProps {
  conversationId: string;
  initialMessages: DbMessage[];
}

interface OptimisticMessage {
  id: string;
  role: "USER" | "ASSISTANT";
  content: string;
  pending?: boolean;
}

// ── Component ───────────────────────────────────────────────────────────────

export default function ChatInterface({
  conversationId,
  initialMessages,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<OptimisticMessage[]>(
    initialMessages.map((m) => ({ id: m.id, role: m.role as "USER" | "ASSISTANT", content: m.content }))
  );
  const [input, setInput] = useState("");
  const [isPending, startTransition] = useTransition();
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-grow textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  function submit() {
    const q = input.trim();
    if (!q || isPending) return;

    const userMsgId = crypto.randomUUID();
    const pendingId = crypto.randomUUID();

    // Optimistic update
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "USER", content: q },
      { id: pendingId, role: "ASSISTANT", content: "", pending: true },
    ]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    startTransition(async () => {
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: q, conversationId }),
        });

        const data = await res.json();

        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingId
              ? { id: pendingId, role: "ASSISTANT", content: JSON.stringify(data) }
              : m
          )
        );
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingId
              ? {
                  id: pendingId,
                  role: "ASSISTANT",
                  content: JSON.stringify({
                    error_code: "LLM_UNAVAILABLE",
                    message: "Network error — could not reach the backend.",
                    recoverable: true,
                  }),
                }
              : m
          )
        );
      }
    });
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-1">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-slate-500">Ask anything about your transactions.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={msg.role === "USER" ? "flex justify-end" : "flex justify-start"}>
            {msg.role === "USER" ? (
              <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-cyan-600/20 border border-cyan-500/20 px-4 py-2.5">
                <p className="text-sm text-slate-100">{msg.content}</p>
              </div>
            ) : (
              <div className="max-w-[90%] rounded-2xl rounded-tl-sm border border-white/10 bg-white/3 px-4 py-3">
                {msg.pending ? (
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <IconLoader2 className="h-3.5 w-3.5 animate-spin" />
                    Analysing…
                  </div>
                ) : (
                  <AnswerCard raw={msg.content} />
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="mt-4 flex items-end gap-3 rounded-xl border border-white/10 bg-[#030915]/80 px-4 py-3 backdrop-blur-sm">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about revenue, channel breakdown, trends…"
          className="flex-1 resize-none bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
          style={{ maxHeight: "160px" }}
        />
        <button
          onClick={submit}
          disabled={!input.trim() || isPending}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-600 text-white transition-opacity disabled:opacity-40 hover:bg-cyan-500"
        >
          {isPending ? (
            <IconLoader2 className="h-4 w-4 animate-spin" />
          ) : (
            <IconSend className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}

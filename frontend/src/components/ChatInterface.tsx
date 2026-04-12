"use client";

import { useRef, useState, useTransition } from "react";
import {
  IconLoader2,
  IconSparkles,
  IconUser,
  IconTrendingUp,
  IconChartBar,
  IconSearch,
  IconBolt,
  IconArrowUp,
} from "@tabler/icons-react";
import AnswerCard from "./AnswerCard";

// ── Types ────────────────────────────────────────────────────────────────────

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

// ── Suggestion prompts ────────────────────────────────────────────────────────

const PROMPTS = [
  { icon: IconTrendingUp, text: "What's driving revenue growth this quarter?" },
  { icon: IconChartBar,   text: "Break down sales by region and channel" },
  { icon: IconSearch,     text: "Why did customer complaints spike last week?" },
  { icon: IconBolt,       text: "Compare this month vs last month metrics" },
];

// ── Typing indicator ──────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="block h-1.5 w-1.5 rounded-full bg-neutral-400"
          style={{ animation: `dotBounce 1.4s ease-in-out ${i * 0.18}s infinite` }}
        />
      ))}
    </div>
  );
}

// ── Input bar (shared between empty and active state) ─────────────────────────

interface InputBarProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
  isPending: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}

function InputBar({ value, onChange, onKeyDown, onSubmit, isPending, textareaRef }: InputBarProps) {
  return (
    <div className="flex items-end gap-2 rounded-2xl border border-neutral-700 bg-neutral-800 px-4 py-3 transition-colors focus-within:border-neutral-500">
      <textarea
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={onChange}
        onKeyDown={onKeyDown}
        placeholder="Ask about revenue, channel breakdown, trends…"
        className="flex-1 resize-none bg-transparent text-sm text-white placeholder:text-neutral-500 focus:outline-none leading-relaxed"
        style={{ maxHeight: "140px" }}
      />
      <button
        onClick={onSubmit}
        disabled={!value.trim() || isPending}
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white text-black transition-all hover:bg-neutral-200 disabled:opacity-25 disabled:cursor-not-allowed"
      >
        {isPending
          ? <IconLoader2 className="h-4 w-4 animate-spin" />
          : <IconArrowUp className="h-4 w-4" />}
      </button>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ChatInterface({ conversationId, initialMessages }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<OptimisticMessage[]>(
    initialMessages.map((m) => ({
      id: m.id,
      role: m.role as "USER" | "ASSISTANT",
      content: m.content,
    }))
  );
  const [input, setInput] = useState("");
  const [isPending, startTransition] = useTransition();
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () =>
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 60);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 140) + "px"; }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  function submit(override?: string) {
    const q = (override ?? input).trim();
    if (!q || isPending) return;

    const userId = crypto.randomUUID();
    const pendingId = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      { id: userId, role: "USER", content: q },
      { id: pendingId, role: "ASSISTANT", content: "", pending: true },
    ]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    scrollToBottom();

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
            m.id === pendingId ? { id: pendingId, role: "ASSISTANT", content: JSON.stringify(data) } : m
          )
        );
        scrollToBottom();
        window.dispatchEvent(new CustomEvent("ml:conversation-updated"));
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingId
              ? { id: pendingId, role: "ASSISTANT", content: JSON.stringify({ error_code: "LLM_UNAVAILABLE", message: "Network error — could not reach the backend.", recoverable: true }) }
              : m
          )
        );
      }
    });
  }

  const isEmpty = messages.length === 0;

  // ── Empty state: centered layout, input in the middle ──────────────────────
  if (isEmpty) {
    return (
      <div className="flex flex-1 items-center justify-center px-4 py-8">
        <div className="w-full max-w-2xl">

          {/* Icon */}
          <div className="mb-5 flex justify-center">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600">
              <IconSparkles className="h-5 w-5 text-white" />
            </div>
          </div>

          {/* Heading */}
          <h1 className="mb-1 text-center text-2xl font-semibold tracking-tight text-white">
            What would you like to explore?
          </h1>
          <p className="mb-8 text-center text-sm text-neutral-400">
            Ask me about your metrics, trends, and business data.
          </p>

          {/* Input — centered, prominent */}
          <InputBar
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onSubmit={() => submit()}
            isPending={isPending}
            textareaRef={textareaRef}
          />
          <p className="mt-2 text-center text-xs text-neutral-600">
            Enter to send · Shift+Enter for new line
          </p>

          {/* Suggestion cards */}
          <div className="mt-5 grid grid-cols-2 gap-2">
            {PROMPTS.map((p, i) => (
              <button
                key={i}
                onClick={() => submit(p.text)}
                className="flex items-start gap-3 rounded-xl border border-neutral-700/60 bg-neutral-800/50 px-4 py-3 text-left transition-colors hover:border-neutral-600 hover:bg-neutral-800 group"
              >
                <p.icon className="mt-0.5 h-4 w-4 shrink-0 text-neutral-500 group-hover:text-neutral-400 transition-colors" />
                <span className="text-sm text-neutral-300 group-hover:text-white transition-colors leading-snug">
                  {p.text}
                </span>
              </button>
            ))}
          </div>

        </div>
      </div>
    );
  }

  // ── Active state: messages + input at bottom ───────────────────────────────
  return (
    <div className="flex flex-1 flex-col overflow-hidden">

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-2 py-4">
        <div className="mx-auto max-w-2xl space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === "USER" ? "flex-row-reverse" : "flex-row"}`}
              style={{ animation: "messageIn 0.2s ease-out both" }}
            >
              {/* Avatar */}
              <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                msg.role === "USER"
                  ? "bg-blue-600"
                  : "bg-neutral-700"
              }`}>
                {msg.role === "USER"
                  ? <IconUser className="h-3.5 w-3.5 text-white" />
                  : <IconSparkles className="h-3.5 w-3.5 text-neutral-300" />}
              </div>

              {/* Bubble */}
              <div className={`max-w-[80%] ${msg.role === "USER" ? "items-end" : "items-start"} flex flex-col`}>
                {msg.role === "USER" ? (
                  <div className="rounded-2xl rounded-tr-sm bg-blue-600 px-3.5 py-2.5">
                    <p className="text-sm text-white leading-relaxed">{msg.content}</p>
                  </div>
                ) : (
                  <div className="rounded-2xl rounded-tl-sm border border-neutral-700/60 bg-neutral-800/60 px-3.5 py-3">
                    {msg.pending ? <TypingIndicator /> : <AnswerCard raw={msg.content} />}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input — bottom */}
      <div className="shrink-0 px-4 pb-4 pt-2">
        <div className="mx-auto max-w-2xl">
          <InputBar
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onSubmit={() => submit()}
            isPending={isPending}
            textareaRef={textareaRef}
          />
          <p className="mt-1.5 text-center text-xs text-neutral-600">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>

    </div>
  );
}

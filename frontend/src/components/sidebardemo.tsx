"use client";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  IconBrandTabler,
  IconPlus,
  IconSearch,
  IconSettings,
  IconRobot,
  IconMenu2,
  IconX,
} from "@tabler/icons-react";
import { cn } from "@/src/lib/utils";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

type ConversationItem = {
  id: string;
  title: string | null;
  updatedAt: string;
};

export function SidebarDemo() {
  const [open, setOpen] = useState(false);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [query, setQuery] = useState("");
  const [creating, setCreating] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const isChatPage = pathname === "/chat";
  const activeConversationId = searchParams.get("conversationId");

  const links = [
    {
      label: "Chat",
      href: "/chat",
      icon: <IconBrandTabler className="h-4 w-4 shrink-0" />,
    },
    {
      label: "My Workspace",
      href: "/myworkspace",
      icon: <IconSettings className="h-4 w-4 shrink-0" />,
    },
    {
      label: "AI Assistant",
      href: "/ai-assistant",
      icon: <IconRobot className="h-4 w-4 shrink-0" />,
    },
  ];

  const fetchConversations = useCallback(async () => {
    if (!isChatPage) return;
    const res = await fetch("/api/conversations", { method: "GET", cache: "no-store" });
    if (!res.ok) { setConversations([]); return; }
    const data = await res.json();
    setConversations(data.conversations ?? []);
  }, [isChatPage]);

  // Initial fetch
  useEffect(() => {
    void fetchConversations();
  }, [fetchConversations]);

  // Listen for conversation updates (new message sent / title changed)
  useEffect(() => {
    if (!isChatPage) return;
    const handler = () => void fetchConversations();
    window.addEventListener("ml:conversation-updated", handler);
    return () => window.removeEventListener("ml:conversation-updated", handler);
  }, [isChatPage, fetchConversations]);

  const filteredConversations = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return conversations;
    return conversations.filter((c) =>
      (c.title ?? "New conversation").toLowerCase().includes(normalized)
    );
  }, [conversations, query]);

  const handleCreateConversation = async () => {
    if (creating) return;
    setCreating(true);
    const res = await fetch("/api/conversations", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      // Add to list immediately — no refresh needed
      setConversations((prev) => [
        { id: data.conversation.id, title: null, updatedAt: new Date().toISOString() },
        ...prev,
      ]);
      router.push(`/chat?conversationId=${data.conversation.id}`);
    }
    setCreating(false);
  };

  return (
    <div
      className={cn(
        "relative flex flex-col border-r border-neutral-800 bg-neutral-900 transition-all duration-300 ease-in-out shrink-0",
        open ? "w-60" : "w-14"
      )}
    >
      <div className="flex flex-1 flex-col overflow-hidden px-2 py-3">

        {/* Toggle button + Logo row */}
        <div className={cn("flex items-center gap-3 mb-4 px-1", open ? "justify-between" : "justify-center")}>
          {open && <Logo />}
          <button
            onClick={() => setOpen(!open)}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-white"
            aria-label="Toggle sidebar"
          >
            {open ? <IconX className="h-4 w-4" /> : <IconMenu2 className="h-4 w-4" />}
          </button>
        </div>

        {/* Nav links */}
        <div className="flex flex-col gap-1">
          {links.map((link, idx) => (
            <NavLink
              key={idx}
              href={link.href}
              icon={link.icon}
              label={link.label}
              active={pathname === link.href}
              showLabel={open}
            />
          ))}
        </div>

        {/* Conversation list */}
        {isChatPage && (
          <div className="mt-3 border-t border-neutral-800 pt-3 flex flex-col gap-1 min-h-0">
            {/* New conversation */}
            <button
              type="button"
              onClick={handleCreateConversation}
              disabled={creating}
              title={open ? undefined : "New conversation"}
              className={cn(
                "flex items-center gap-2 rounded-md px-2 py-1.5 text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-white disabled:opacity-50",
                !open && "justify-center"
              )}
            >
              <IconPlus className="h-4 w-4 shrink-0" />
              {open && <span className="text-[13px]">{creating ? "Creating…" : "New conversation"}</span>}
            </button>

            {open && (
              <>
                {/* Search */}
                <div className="relative mt-1">
                  <IconSearch className="pointer-events-none absolute left-2.5 top-2 h-3 w-3 text-neutral-500" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search conversations"
                    className="w-full rounded-md border border-neutral-700 bg-neutral-800 py-1.5 pl-7 pr-2 text-[13px] text-neutral-200 placeholder:text-neutral-500 outline-none focus:border-neutral-600"
                  />
                </div>

                {/* List */}
                <div className="mt-2 overflow-y-auto flex flex-col">
                  <p className="px-2 pb-1 text-[11px] font-medium text-neutral-500">
                    Recents
                  </p>
                  {filteredConversations.map((c) => {
                    const isActive = c.id === activeConversationId;
                    return (
                      <Link
                        key={c.id}
                        href={`/chat?conversationId=${c.id}`}
                        className={cn(
                          "block truncate rounded-md px-2 py-1.5 text-[13px] transition-colors",
                          isActive
                            ? "bg-neutral-700 text-white"
                            : "text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200"
                        )}
                      >
                        {c.title ?? "New conversation"}
                      </Link>
                    );
                  })}
                  {filteredConversations.length === 0 && (
                    <p className="px-2 py-1.5 text-[13px] text-neutral-600">No conversations yet.</p>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function NavLink({
  href,
  icon,
  label,
  active,
  showLabel,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
  showLabel: boolean;
}) {
  return (
    <Link
      href={href}
      title={showLabel ? undefined : label}
      className={cn(
        "flex items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors",
        active
          ? "bg-neutral-700 text-white"
          : "text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200",
        !showLabel && "justify-center"
      )}
    >
      <span className="shrink-0">{icon}</span>
      {showLabel && <span className="text-[13px]">{label}</span>}
    </Link>
  );
}

export const Logo = () => (
  <a href="#" className="flex items-center gap-2 py-1 text-sm font-normal text-white">
    <div className="h-5 w-6 rounded bg-white shrink-0" />
    <span className="whitespace-nowrap font-medium">MetricLens.</span>
  </a>
);

export const LogoIcon = () => (
  <a href="#" className="flex items-center py-1">
    <div className="h-5 w-6 rounded bg-white" />
  </a>
);

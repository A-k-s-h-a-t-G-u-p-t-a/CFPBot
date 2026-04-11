"use client";
import React, { useEffect, useMemo, useState } from "react";
import {
  IconBrandTabler,
  IconMessageCircle,
  IconPlus,
  IconSearch,
  IconSettings,
  IconRobot,
} from "@tabler/icons-react";
import { motion } from "framer-motion";
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
      icon: <IconBrandTabler className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
    {
      label: "My Workspace",
      href: "/myworkspace",
      icon: <IconSettings className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
    {
      label: "Ai Assistant",
      href: "/ai-assistant",
      icon: <IconRobot className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
    },
  ];

  useEffect(() => {
    if (!isChatPage) return;

    const fetchConversations = async () => {
      const res = await fetch("/api/conversations", {
        method: "GET",
        cache: "no-store",
      });

      if (!res.ok) {
        setConversations([]);
        return;
      }

      const data = await res.json();
      setConversations(data.conversations ?? []);
    };

    void fetchConversations();
  }, [isChatPage]);

  const filteredConversations = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return conversations;

    return conversations.filter((conversation) =>
      (conversation.title ?? "New conversation").toLowerCase().includes(normalized)
    );
  }, [conversations, query]);

  const handleCreateConversation = async () => {
    if (creating) return;

    setCreating(true);
    const res = await fetch("/api/conversations", { method: "POST" });

    if (res.ok) {
      const data = await res.json();
      router.push(`/chat?conversationId=${data.conversation.id}`);
      router.refresh();
    }

    setCreating(false);
  };

  return (
    <div
      className={cn(
        "group relative flex flex-col overflow-hidden border-r border-neutral-900 bg-gray-100 transition-all duration-300 dark:border-neutral-700 dark:bg-neutral-900",
        "hover:w-64",
        open ? "w-64" : "w-16"
      )}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <div className="flex flex-1 flex-col justify-between gap-6 px-2 py-6">
        <div className="flex flex-1 flex-col overflow-y-auto">
          {open ? <Logo /> : <LogoIcon />}
          <div className="mt-8 flex flex-col gap-2">
            {links.map((link, idx) => (
              <SidebarLink key={idx} link={link} labelVisible={open} />
            ))}
          </div>

          {isChatPage && (
            <div className="mt-6">
              <button
                type="button"
                onClick={handleCreateConversation}
                className="flex w-full items-center gap-2 rounded px-3 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-200 disabled:opacity-50 dark:text-neutral-200 dark:hover:bg-neutral-800"
                disabled={creating}
              >
                <IconPlus className="h-4 w-4 shrink-0" />
                {open && <span>{creating ? "Creating..." : "Start new conversation"}</span>}
              </button>

              {open && (
                <div className="mt-3 space-y-3">
                  <div className="relative">
                    <IconSearch className="pointer-events-none absolute left-2 top-2.5 h-4 w-4 text-neutral-500" />
                    <input
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Search conversations"
                      className="w-full rounded border border-neutral-300 bg-white py-2 pl-8 pr-2 text-xs text-neutral-800 outline-none focus:border-cyan-500 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
                    />
                  </div>

                  <div className="space-y-1">
                    <p className="px-2 text-[10px] uppercase tracking-wide text-neutral-500">
                      Previous conversations
                    </p>
                    {filteredConversations.map((conversation) => {
                      const isActive = conversation.id === activeConversationId;
                      return (
                        <Link
                          key={conversation.id}
                          href={`/chat?conversationId=${conversation.id}`}
                          className={cn(
                            "block rounded px-2 py-2 text-xs text-neutral-700 hover:bg-neutral-200 dark:text-neutral-200 dark:hover:bg-neutral-800",
                            isActive && "bg-neutral-200 dark:bg-neutral-800"
                          )}
                        >
                          <div className="flex items-center gap-2">
                            <IconMessageCircle className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate">{conversation.title ?? "New conversation"}</span>
                          </div>
                        </Link>
                      );
                    })}
                    {filteredConversations.length === 0 && (
                      <p className="px-2 py-2 text-xs text-neutral-500">No conversations yet.</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
}

export const Logo = () => (
  <a
    href="#"
    className="flex items-center space-x-2 py-1 text-sm font-normal text-black dark:text-white"
  >
    <div className="h-5 w-6 rounded bg-black dark:bg-white" />
    <motion.span
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="whitespace-nowrap font-medium"
    >
      MetricLens.
    </motion.span>
  </a>
);

export const LogoIcon = () => (
  <a href="#" className="flex items-center py-1">
    <div className="h-5 w-6 rounded bg-black dark:bg-white" />
  </a>
);

export interface Links {
  label: string;
  href: string;
  icon: React.ReactNode;
}

interface SidebarLinkProps {
  link: Links;
  className?: string;
  labelVisible?: boolean;
}

export function SidebarLink({ link, className, labelVisible = true }: SidebarLinkProps) {
  return (
    <Link
      href={link.href}
      className={cn(
        "flex items-center gap-3 rounded px-3 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-200 dark:text-neutral-200 dark:hover:bg-neutral-800",
        className
      )}
    >
      {link.icon}
      {labelVisible && <span>{link.label}</span>}
    </Link>
  );
}

'use client';

import { useState, useRef, useEffect } from 'react';
import { IconMessageCircle, IconSend } from '@tabler/icons-react';
import { sendMessage } from './actions';

type Message = {
  id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  createdAt: Date;
};

type ChatClientProps = {
  initialMessages: Message[];
  conversationId: string | undefined;
  userId: string;
};

export function ChatClient({ initialMessages, conversationId, userId }: ChatClientProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isPending, setIsPending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async () => {
    if (!inputValue.trim() || !conversationId) return;

    const newContent = inputValue.trim();
    setInputValue('');
    
    // Optimistic UI update
    const tempId = `temp-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: tempId,
        role: 'USER',
        content: newContent,
        createdAt: new Date(),
      },
    ]);

    setIsPending(true);
    try {
      const savedMessage = await sendMessage(conversationId, userId, newContent);
      if (savedMessage) {
        setMessages((prev) => prev.map(m => m.id === tempId ? { ...m, id: savedMessage.id } : m));
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Optional: Remove optimistic message or show error
    } finally {
      setIsPending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  if (!conversationId) {
    return (
      <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-white/15 bg-[#030915]/50">
        <div className="flex flex-col items-center text-center">
          <IconMessageCircle className="mb-3 h-8 w-8 text-cyan-300" />
          <p className="text-sm text-slate-300">No conversation selected yet.</p>
          <p className="mt-1 text-xs text-slate-500">Use "Start new conversation" in the sidebar.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col h-full rounded-xl border border-dashed border-white/15 bg-[#030915]/50 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <IconMessageCircle className="mb-3 h-8 w-8 text-cyan-300" />
            <p className="text-sm text-slate-300">Start the conversation</p>
            <p className="mt-1 text-xs text-slate-500">Your messages will appear here.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex w-full mb-4 ${msg.role === 'USER' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'USER'
                    ? 'bg-blue-600/80 text-white rounded-br-sm'
                    : 'bg-white/10 text-slate-200 rounded-bl-sm'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-white/5 bg-[#020816]/80 flex items-end gap-2">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask something..."
          className="flex-1 resize-none bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-cyan-500 min-h-[44px] max-h-32"
          rows={1}
          disabled={isPending}
        />
        <button
          onClick={handleSubmit}
          disabled={!inputValue.trim() || isPending}
          className="p-3 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:hover:bg-cyan-600 rounded-xl text-white transition-colors"
        >
          <IconSend className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

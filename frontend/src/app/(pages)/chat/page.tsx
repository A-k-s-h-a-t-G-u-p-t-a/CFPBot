import { getServerSession } from 'next-auth';
import { redirect } from 'next/navigation';
import { authOptions } from '@/src/lib/auth-options';
import { prisma } from '@/src/lib/prisma';
import ChatInterface from '@/src/components/ChatInterface';
import { IconMessageCircle } from '@tabler/icons-react';

type ChatPageProps = {
  searchParams: Promise<{ conversationId?: string }>;
};

export default async function ChatPage({ searchParams }: ChatPageProps) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) redirect('/signin');

  const params = await searchParams;
  const selectedConversationId = params.conversationId;

  const conversations = await prisma.conversation.findMany({
    where: { userId: session.user.id },
    orderBy: { updatedAt: 'desc' },
    select: { id: true, title: true },
  });

  const fallbackConversationId = conversations[0]?.id;
  const activeConversationId = selectedConversationId ?? fallbackConversationId;

  const activeConversation = activeConversationId
    ? await prisma.conversation.findFirst({
        where: { id: activeConversationId, userId: session.user.id },
        include: {
          messages: {
            orderBy: { createdAt: 'asc' },
            select: { id: true, role: true, content: true, createdAt: true },
          },
        },
      })
    : null;

  return (
    <section className="flex h-full flex-col bg-neutral-950">
      {/* Header */}
      <header className="shrink-0 border-b border-neutral-800 bg-neutral-900 px-5 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold text-white">
              {activeConversation?.title ?? 'New conversation'}
            </h1>
            <p className="text-xs text-neutral-500">MetricLens Analytics</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-neutral-500">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Live
          </div>
        </div>
      </header>

      {/* Chat area — fills remaining space */}
      <div className="flex flex-1 flex-col overflow-hidden px-4 py-4">
        {activeConversation ? (
          <ChatInterface
            key={activeConversation.id}
            conversationId={activeConversation.id}
            initialMessages={activeConversation.messages}
          />
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-neutral-800">
            <IconMessageCircle className="h-8 w-8 text-neutral-600" />
            <div className="text-center">
              <p className="text-sm text-neutral-400">No conversation selected</p>
              <p className="mt-0.5 text-xs text-neutral-600">
                Click &ldquo;New conversation&rdquo; in the sidebar to get started.
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

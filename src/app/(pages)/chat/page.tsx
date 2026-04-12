
import { getServerSession } from 'next-auth';
import { redirect } from 'next/navigation';
import { authOptions } from '@/src/lib/auth-options';
import { prisma } from '@/src/lib/prisma';
import { ChatClient } from './chat-client';


type ChatPageProps = {
  searchParams: Promise<{
    conversationId?: string;
  }>;
};

export default async function ChatPage({ searchParams }: ChatPageProps) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    redirect('/signin');
  }

  const params = await searchParams;
  const selectedConversationId = params.conversationId;

  const conversations = await prisma.conversation.findMany({
    where: { userId: session.user.id },
    orderBy: { updatedAt: 'desc' },
    select: {
      id: true,
      title: true,
    },
  });

  const fallbackConversationId = conversations[0]?.id;
  const activeConversationId = selectedConversationId ?? fallbackConversationId;

  const activeConversation = activeConversationId
    ? await prisma.conversation.findFirst({
        where: {
          id: activeConversationId,
          userId: session.user.id,
        },
        include: {
          messages: {
            orderBy: { createdAt: 'asc' },
            select: {
              id: true,
              role: true,
              content: true,
              createdAt: true,
            },
          },
        },
      })
    : null;

  return (
    <section className="relative flex min-h-screen flex-1 flex-col p-6 md:p-10 bg-[#020816] text-white">
      <div className="pointer-events-none absolute -left-40 top-16 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
      <div className="pointer-events-none absolute right-0 top-10 h-112 w-md rounded-full bg-blue-600/15 blur-3xl" />

      <div className="relative z-10 mx-auto flex w-full max-w-4xl flex-1 flex-col rounded-2xl border border-white/10 bg-white/3 p-5 backdrop-blur-sm md:p-8">
        <div className="mb-6 border-b border-white/10 pb-4">
          <h1 className="text-lg font-semibold text-slate-100">{activeConversation?.title ?? 'New conversation'}</h1>
          <p className="mt-1 text-sm text-slate-400">Ask questions about metric changes, breakdowns, and trends.</p>
        </div>

        <ChatClient 
          initialMessages={activeConversation?.messages ?? []} 
          conversationId={activeConversationId} 
          userId={session.user.id}
        />
      </div>
    </section>
  );
}

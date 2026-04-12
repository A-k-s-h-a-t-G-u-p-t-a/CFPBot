'use server';

import { prisma } from '@/src/lib/prisma';
import { revalidatePath } from 'next/cache';

export async function sendMessage(conversationId: string, userId: string, content: string) {
  if (!content || !content.trim()) return null;

  const message = await prisma.message.create({
    data: {
      role: 'USER',
      content: content.trim(),
      conversationId,
      userId,
    },
  });

  // Optional: Add bot reply logic here
  // const botMessage = await prisma.message.create({ ... });

  revalidatePath('/chat');
  return message;
}

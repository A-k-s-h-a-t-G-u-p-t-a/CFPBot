import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/src/lib/auth-options";
import { prisma } from "@/src/lib/prisma";

export const runtime = "nodejs";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const { message, conversationId } = body as {
    message: string;
    conversationId: string;
  };

  if (!message?.trim() || !conversationId) {
    return NextResponse.json({ error: "message and conversationId required" }, { status: 400 });
  }

  // Verify conversation belongs to user
  const conversation = await prisma.conversation.findFirst({
    where: { id: conversationId, userId },
    include: { messages: { orderBy: { createdAt: "asc" }, take: 1 } },
  });

  if (!conversation) {
    return NextResponse.json({ error: "Conversation not found" }, { status: 404 });
  }

  // Persist user message
  await prisma.message.create({
    data: {
      role: "USER",
      content: message,
      conversationId,
      userId,
    },
  });

  // Call FastAPI backend
  let fastapiData: Record<string, unknown>;
  try {
    const fastapiRes = await fetch(`${FASTAPI_URL}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: message, session_id: conversationId }),
    });

    if (!fastapiRes.ok) {
      const errText = await fastapiRes.text();
      throw new Error(`FastAPI ${fastapiRes.status}: ${errText}`);
    }

    fastapiData = await fastapiRes.json();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    fastapiData = {
      error_code: "LLM_UNAVAILABLE",
      message: `Backend unreachable: ${message}`,
      recoverable: true,
      suggestion: "Make sure the Python backend is running on port 8000.",
    };
  }

  // Persist assistant response (store full JSON so AnswerCard can render it)
  await prisma.message.create({
    data: {
      role: "ASSISTANT",
      content: JSON.stringify(fastapiData),
      conversationId,
    },
  });

  // Auto-title conversation on first exchange
  if (conversation.messages.length === 0) {
    const title =
      message.length > 60 ? message.slice(0, 57) + "..." : message;
    await prisma.conversation.update({
      where: { id: conversationId },
      data: { title },
    });
  } else {
    // Touch updatedAt so sidebar ordering stays correct
    await prisma.conversation.update({
      where: { id: conversationId },
      data: { updatedAt: new Date() },
    });
  }

  return NextResponse.json(fastapiData, { status: 200 });
}

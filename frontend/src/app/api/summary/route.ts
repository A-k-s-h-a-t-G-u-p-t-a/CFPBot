import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/src/lib/auth-options";

export const runtime = "nodejs";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const res = await fetch(`${FASTAPI_URL}/api/summary`, {
      headers: { "Content-Type": "application/json" },
      next: { revalidate: 300 }, // cache 5 min
    });

    if (!res.ok) {
      throw new Error(`FastAPI summary ${res.status}`);
    }

    const data = await res.json();
    return NextResponse.json(data, { status: 200 });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: "Backend unavailable", detail: message },
      { status: 502 }
    );
  }
}

import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { prisma } from '@/src/lib/prisma';
// Using the shared prisma instance instead of creating a new one
export async function POST(req: Request) {
  const { email, password } = await req.json();

  if (!email || !password ) {
    return NextResponse.json({ error: "Missing fields" }, { status: 400 });
  }

  const existingUser = await prisma.user.findUnique({ where: { email } });
  if (existingUser) {
    return NextResponse.json({ error: "Email already used" }, { status: 409 });
  }

  const hashedPassword = await bcrypt.hash(password, 10);
  const user = await prisma.user.create({
    data: { email, hashedPassword },
  });

  return NextResponse.json({ user }, { status: 201 });
}

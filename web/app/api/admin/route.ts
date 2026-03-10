import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const ADMIN_USER = process.env.ADMIN_USER || 'admin';
const ADMIN_PASS = process.env.ADMIN_PASS || 'dt_sg_2026!';

export async function POST(req: NextRequest) {
  let body;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const { username, password } = body as { username: string; password: string };

  if (username === ADMIN_USER && password === ADMIN_PASS) {
    return NextResponse.json({ ok: true });
  }

  return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
}

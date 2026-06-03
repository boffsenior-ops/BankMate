import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(request: NextRequest) {
  return request.cookies.get("access_token")?.value;
}

// GET /api/admin/users  — list users
// POST /api/admin/users — create user
export async function GET(request: NextRequest) {
  const token = getToken(request);
  if (!token) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  const url = new URL(`${BACKEND_URL}/api/v1/admin/users`);
  request.nextUrl.searchParams.forEach((v, k) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

export async function POST(request: NextRequest) {
  const token = getToken(request);
  if (!token) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  const body = await request.json();
  const res = await fetch(`${BACKEND_URL}/api/v1/admin/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}

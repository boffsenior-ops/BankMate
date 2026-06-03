import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(r: NextRequest) {
  return r.cookies.get("access_token")?.value;
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const token = getToken(request);
  if (!token) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  const body = await request.json();
  const res = await fetch(`${BACKEND_URL}/api/v1/admin/users/${id}/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}

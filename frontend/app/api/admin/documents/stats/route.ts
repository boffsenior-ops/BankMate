import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(r: NextRequest) {
  return r.cookies.get("access_token")?.value;
}

export async function GET(request: NextRequest) {
  const token = getToken(request);
  if (!token) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  
  const url = new URL(`${BACKEND_URL}/api/v1/admin/documents/stats`);
  const res = await fetch(url.toString(), { 
    headers: { Authorization: `Bearer ${token}` } 
  });
  
  return NextResponse.json(await res.json(), { status: res.status });
}

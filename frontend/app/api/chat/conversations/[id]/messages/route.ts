import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RouteParams = { params: Promise<{ id: string }> };

export async function GET(request: NextRequest, { params }: RouteParams) {
  const accessToken = request.cookies.get("access_token")?.value;
  const { id } = await params;

  if (!accessToken) {
    return NextResponse.json({ detail: "Sessiya muddati tugadi." }, { status: 401 });
  }

  try {
    const backendResponse = await axios.get(
      `${BACKEND_URL}/api/v1/chat/conversations/${id}/messages`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );

    return NextResponse.json(backendResponse.data);
  } catch (error: any) {
    console.error(`GET Messages Proxy Error for conv ${id}:`, error.response?.data || error.message);
    const status = error.response?.status || 500;
    return NextResponse.json(
      { detail: error.response?.data?.detail || "Xabarlarni yuklashda xatolik." },
      { status }
    );
  }
}

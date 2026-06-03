import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RouteParams = { params: Promise<{ id: string }> };

export async function POST(request: NextRequest, { params }: RouteParams) {
  const accessToken = request.cookies.get("access_token")?.value;
  const { id } = await params;

  if (!accessToken) {
    return NextResponse.json({ detail: "Sessiya muddati tugadi." }, { status: 401 });
  }

  try {
    const { feedback } = await request.json();
    const backendResponse = await axios.post(
      `${BACKEND_URL}/api/v1/chat/messages/${id}/feedback`,
      { feedback },
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );

    return NextResponse.json(backendResponse.data);
  } catch (error: any) {
    console.error(`POST Feedback Proxy Error for message ${id}:`, error.response?.data || error.message);
    const status = error.response?.status || 500;
    return NextResponse.json(
      { detail: error.response?.data?.detail || "Fikr-mulohazani saqlashda xatolik." },
      { status }
    );
  }
}

import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const accessToken = request.cookies.get("access_token")?.value;

  if (!accessToken) {
    return NextResponse.json({ detail: "Sessiya muddati tugadi." }, { status: 401 });
  }

  try {
    const backendResponse = await axios.get(`${BACKEND_URL}/api/v1/chat/conversations`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    return NextResponse.json(backendResponse.data);
  } catch (error: any) {
    console.error("GET Conversations Proxy Error:", error.response?.data || error.message);
    const status = error.response?.status || 500;
    return NextResponse.json(
      { detail: error.response?.data?.detail || "Suhbatlar ro'yxatini yuklashda xatolik." },
      { status }
    );
  }
}

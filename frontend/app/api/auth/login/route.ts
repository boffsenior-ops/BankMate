import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const { username, password } = await request.json();

    // Call FastAPI backend /auth/login
    const loginResponse = await axios.post(`${BACKEND_URL}/api/v1/auth/login`, {
      username,
      password,
    });

    const { access_token, refresh_token } = loginResponse.data;

    // Fetch user details immediately using access_token
    const meResponse = await axios.get(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${access_token}`,
      },
    });

    const user = meResponse.data;

    // Set HTTP-Only cookies
    const response = NextResponse.json({ user });
    
    response.cookies.set("access_token", access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 30 * 60, // 30 minutes
      path: "/",
    });

    response.cookies.set("refresh_token", refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 7 * 24 * 60 * 60, // 7 days
      path: "/",
    });

    return response;
  } catch (error: any) {
    console.error("Login Proxy Error:", error.response?.data || error.message);
    const status = error.response?.status || 500;
    const detail = error.response?.data?.detail || "Tizimga kirishda xatolik yuz berdi.";
    return NextResponse.json({ detail }, { status });
  }
}

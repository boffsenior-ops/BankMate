import { NextRequest, NextResponse } from "next/server";
import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  let accessToken = request.cookies.get("access_token")?.value;
  const refreshToken = request.cookies.get("refresh_token")?.value;

  if (!accessToken && !refreshToken) {
    return NextResponse.json({ detail: "Sessiya muddati tugadi." }, { status: 401 });
  }

  const response = NextResponse.next();

  try {
    // If we don't have access token but have refresh token, attempt refresh
    if (!accessToken && refreshToken) {
      const refreshResponse = await axios.post(`${BACKEND_URL}/api/v1/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token: newAccessToken, refresh_token: newRefreshToken } = refreshResponse.data;
      accessToken = newAccessToken;

      // Update response cookies
      response.cookies.set("access_token", newAccessToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 30 * 60,
        path: "/",
      });

      response.cookies.set("refresh_token", newRefreshToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 7 * 24 * 60 * 60,
        path: "/",
      });
    }

    // Call /auth/me with active access token
    const meResponse = await axios.get(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    // Create a JSON response to return to client
    const clientResponse = NextResponse.json({ user: meResponse.data });
    
    // Copy set-cookie headers from our local response if we refreshed the token
    if (!request.cookies.get("access_token")?.value && accessToken) {
      clientResponse.cookies.set("access_token", accessToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 30 * 60,
        path: "/",
      });
      clientResponse.cookies.set("refresh_token", refreshToken!, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 7 * 24 * 60 * 60,
        path: "/",
      });
    }

    return clientResponse;
  } catch (error: any) {
    console.error("Auth Me Proxy Error:", error.response?.data || error.message);
    const status = error.response?.status || 401;
    
    // Clear cookies if backend rejected them
    const errResponse = NextResponse.json({ detail: "Sessiya yaroqsiz." }, { status });
    errResponse.cookies.delete("access_token");
    errResponse.cookies.delete("refresh_token");
    return errResponse;
  }
}

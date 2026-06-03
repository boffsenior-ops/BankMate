import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  const accessToken = request.cookies.get("access_token")?.value;

  if (!accessToken) {
    return NextResponse.json({ detail: "Sessiya muddati tugadi." }, { status: 401 });
  }

  try {
    const body = await request.json();

    // Call the backend streaming endpoint using standard fetch
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(body),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({ detail: "Streaming error" }));
      return NextResponse.json(
        { detail: errorData.detail || "Server streaming xatoligi" },
        { status: backendResponse.status }
      );
    }

    // Set up standard ReadableStream to proxy the SSE bytes
    const stream = new ReadableStream({
      async start(controller) {
        if (!backendResponse.body) {
          controller.close();
          return;
        }

        const reader = backendResponse.body.getReader();
        const decoder = new TextDecoder();
        const encoder = new TextEncoder();

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // Enqueue the chunk directly to forward it
            controller.enqueue(value);
          }
        } catch (error) {
          console.error("Stream Proxy Error during read:", error);
          controller.error(error);
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  } catch (error: any) {
    console.error("Chat Stream Proxy Setup Error:", error.message);
    return NextResponse.json({ detail: "Tarmoq xatoligi yoki server ulanishi xatosi." }, { status: 500 });
  }
}

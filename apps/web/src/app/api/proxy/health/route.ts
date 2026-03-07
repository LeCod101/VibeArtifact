import { NextResponse } from "next/server";

const API_BASE = process.env.API_URL || "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/health`, {
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { status: "error", detail: String(e) },
      { status: 502 },
    );
  }
}

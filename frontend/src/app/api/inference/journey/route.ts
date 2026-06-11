/*
Purpose: Proxy frontend journey inference requests to the backend journey endpoint.
Used by: Inference page in the Next.js app when running a full mobile-app lifecycle simulation.
Main dependencies: NEXT_PUBLIC_API_URL and backend /api/inference/journey endpoint.
Public/main functions: POST handler.
Side effects: Performs an HTTP call to the backend inference API.
*/

import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  const body = await request.json();
  const response = await fetch(`${BACKEND_URL}/api/inference/journey`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}

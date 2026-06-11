/*
Purpose: Proxy frontend registration inference requests to the backend lifecycle endpoint.
Used by: Inference page in the Next.js app when simulating mobile registration.
Main dependencies: NEXT_PUBLIC_API_URL and backend /api/inference/lifecycle endpoint.
Public/main functions: POST handler.
Side effects: Performs an HTTP call to the backend inference API.
*/

import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const readResponse = async (response: Response) => {
 const contentType = response.headers.get('content-type') || '';
 if (contentType.includes('application/json')) {
 return await response.json();
 }
 const text = await response.text();
 return { detail: text || `Backend returned status ${response.status}` };
};

export async function POST(request: Request) {
  const body = await request.json();
  const response = await fetch(`${BACKEND_URL}/api/inference/lifecycle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...body, stage: 'registration' }),
  });
  const data = await readResponse(response);
  return NextResponse.json(data, { status: response.status });
}

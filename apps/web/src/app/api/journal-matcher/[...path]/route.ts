import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.JOURNAL_MATCHER_API_URL ?? 'http://127.0.0.1:8000';
const INVITE_TOKEN = process.env.JOURNAL_MATCHER_INVITE_TOKEN ?? 'local-invite-token';
const WORKSPACE_ID = process.env.JOURNAL_MATCHER_WORKSPACE_ID ?? '11111111-1111-4111-8111-111111111111';

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const upstream = new URL(`/v1/${path.join('/')}`, API_URL);
  upstream.search = request.nextUrl.search;
  const headers = new Headers();
  headers.set('Authorization', `Bearer ${INVITE_TOKEN}`);
  headers.set('X-Workspace-Id', WORKSPACE_ID);
  const contentType = request.headers.get('content-type');
  const documentMediaType = request.headers.get('x-document-media-type');
  if (contentType) headers.set('Content-Type', contentType);
  if (documentMediaType) headers.set('X-Document-Media-Type', documentMediaType);
  const body = request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.arrayBuffer();
  try {
    const response = await fetch(upstream, { method: request.method, headers, body, cache: 'no-store' });
    const forwarded = new Headers();
    for (const name of ['content-type', 'content-disposition']) {
      const value = response.headers.get(name);
      if (value) forwarded.set(name, value);
    }
    return new NextResponse(response.body, { status: response.status, headers: forwarded });
  } catch {
    return NextResponse.json({ detail: 'O serviço de análise não está disponível.' }, { status: 503 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;

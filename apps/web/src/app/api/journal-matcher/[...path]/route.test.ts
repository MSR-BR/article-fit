import { NextRequest } from 'next/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { GET, POST } from './route';

const context = (path: string[]) => ({ params: Promise.resolve({ path }) });

describe('journal matcher server proxy', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('adds server-side authentication and forwards JSON requests', async () => {
    const upstream = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 'project-1' }), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', upstream);
    const request = new NextRequest('http://localhost/api/journal-matcher/projects?source=ui', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ journalCandidate: 'PRL' }),
    });
    const response = await POST(request, context(['projects']));
    const [url, init] = upstream.mock.calls[0];
    expect(String(url)).toBe('http://127.0.0.1:8000/v1/projects?source=ui');
    expect(init.headers.get('Authorization')).toBe('Bearer local-invite-token');
    expect(init.headers.get('X-Workspace-Id')).toBe('11111111-1111-4111-8111-111111111111');
    expect(response.status).toBe(201);
  });

  it('forwards downloads and their filename without a request body', async () => {
    const upstream = vi.fn().mockResolvedValue(
      new Response('pdf', {
        headers: {
          'Content-Type': 'application/pdf',
          'Content-Disposition': 'attachment; filename="report.pdf"',
        },
      }),
    );
    vi.stubGlobal('fetch', upstream);
    const response = await GET(
      new NextRequest('http://localhost/api/journal-matcher/analyses/a/artifacts/report.pdf'),
      context(['analyses', 'a', 'artifacts', 'report.pdf']),
    );
    expect(upstream.mock.calls[0][1].body).toBeUndefined();
    expect(response.headers.get('content-disposition')).toContain('report.pdf');
  });

  it('returns a controlled error when the API is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network')));
    const response = await GET(
      new NextRequest('http://localhost/api/journal-matcher/projects/one'),
      context(['projects', 'one']),
    );
    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ detail: 'O serviço de análise não está disponível.' });
  });
});

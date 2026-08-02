import { NextRequest } from 'next/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { GET, POST } from './route';

const { createSupabaseClient } = vi.hoisted(() => ({
  createSupabaseClient: vi.fn(),
}));
vi.mock('../../../../lib/supabase/server', () => ({
  createClient: createSupabaseClient,
}));

const context = (path: string[]) => ({ params: Promise.resolve({ path }) });

describe('journal matcher server proxy', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    createSupabaseClient.mockReset();
  });

  it('adds server-side authentication and forwards JSON requests', async () => {
    const upstream = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 'project-1' }), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', upstream);
    const request = new NextRequest(
      'http://localhost/api/journal-matcher/projects?source=ui',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ journalCandidate: 'PRL' }),
      },
    );
    const response = await POST(request, context(['projects']));
    const [url, init] = upstream.mock.calls[0];
    expect(String(url)).toBe('http://127.0.0.1:8000/v1/projects?source=ui');
    expect(init.headers.get('Authorization')).toBe('Bearer local-invite-token');
    expect(init.headers.get('X-Workspace-Id')).toBe(
      '11111111-1111-4111-8111-111111111111',
    );
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
      new NextRequest(
        'http://localhost/api/journal-matcher/analyses/a/artifacts/report.pdf',
      ),
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
    await expect(response.json()).resolves.toEqual({
      detail: 'O serviço de análise não está disponível.',
    });
  });

  it('derives hosted authentication from the verified user membership', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://project.supabase.co');
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY', 'publishable');
    const maybeSingle = vi.fn().mockResolvedValue({
      data: { workspace_id: '22222222-2222-4222-8222-222222222222' },
      error: null,
    });
    const query = {
      select: vi.fn(),
      eq: vi.fn(),
      order: vi.fn(),
      limit: vi.fn(),
      maybeSingle,
    };
    query.select.mockReturnValue(query);
    query.eq.mockReturnValue(query);
    query.order.mockReturnValue(query);
    query.limit.mockReturnValue(query);
    createSupabaseClient.mockResolvedValue({
      auth: {
        getUser: vi.fn().mockResolvedValue({
          data: { user: { id: 'user-1', is_anonymous: false } },
          error: null,
        }),
        getSession: vi.fn().mockResolvedValue({
          data: { session: { access_token: 'user-jwt' } },
        }),
      },
      from: vi.fn().mockReturnValue(query),
    });
    const upstream = vi
      .fn()
      .mockResolvedValue(new Response('{}', { status: 201 }));
    vi.stubGlobal('fetch', upstream);
    const response = await POST(
      new NextRequest('http://localhost/api/journal-matcher/projects', {
        method: 'POST',
        body: '{}',
      }),
      context(['projects']),
    );
    expect(response.status).toBe(201);
    const headers = upstream.mock.calls[0][1].headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer user-jwt');
    expect(headers.get('X-Workspace-Id')).toBe(
      '22222222-2222-4222-8222-222222222222',
    );
  });

  it('rejects an unauthenticated hosted request before contacting the API', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://project.supabase.co');
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY', 'publishable');
    createSupabaseClient.mockResolvedValue({
      auth: {
        getUser: vi.fn().mockResolvedValue({
          data: { user: null },
          error: new Error('expired'),
        }),
      },
    });
    const upstream = vi.fn();
    vi.stubGlobal('fetch', upstream);
    const response = await GET(
      new NextRequest('http://localhost/api/journal-matcher/projects/one'),
      context(['projects', 'one']),
    );
    expect(response.status).toBe(401);
    expect(upstream).not.toHaveBeenCalled();
  });
});

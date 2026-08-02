import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { createBrowserClient, createServerClient, cookieStore } = vi.hoisted(
  () => ({
    createBrowserClient: vi.fn(),
    createServerClient: vi.fn(),
    cookieStore: { getAll: vi.fn(), set: vi.fn() },
  }),
);

vi.mock('@supabase/ssr', () => ({ createBrowserClient, createServerClient }));
vi.mock('next/headers', () => ({
  cookies: vi.fn().mockResolvedValue(cookieStore),
}));

describe('Supabase clients', () => {
  beforeEach(() => {
    vi.resetModules();
    createBrowserClient.mockReset();
    createServerClient.mockReset();
    cookieStore.getAll.mockReset();
    cookieStore.set.mockReset();
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://project.supabase.co');
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY', 'publishable-key');
  });

  afterEach(() => vi.unstubAllEnvs());

  it('rejects an incomplete public configuration', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY', '');
    const { publicSupabaseConfig } = await import('./config');
    expect(() => publicSupabaseConfig()).toThrow('não está configurada');
  });

  it('creates and reuses a browser client with public credentials', async () => {
    const browser = { auth: {} };
    createBrowserClient.mockReturnValue(browser);
    const { createClient } = await import('./client');
    expect(createClient()).toBe(browser);
    expect(createClient()).toBe(browser);
    expect(createBrowserClient).toHaveBeenCalledOnce();
    expect(createBrowserClient).toHaveBeenCalledWith(
      'https://project.supabase.co',
      'publishable-key',
    );
  });

  it('connects the server client to the Next.js cookie store', async () => {
    cookieStore.getAll.mockReturnValue([{ name: 'session', value: 'value' }]);
    let cookieOptions:
      | {
          cookies: {
            getAll: () => unknown;
            setAll: (
              values: Array<{ name: string; value: string; options: object }>,
            ) => void;
          };
        }
      | undefined;
    const server = { auth: {} };
    createServerClient.mockImplementation((_url, _key, options) => {
      cookieOptions = options;
      return server;
    });
    const { createClient } = await import('./server');
    await expect(createClient()).resolves.toBe(server);
    expect(cookieOptions?.cookies.getAll()).toEqual([
      { name: 'session', value: 'value' },
    ]);
    cookieOptions?.cookies.setAll([
      { name: 'session', value: 'new', options: { httpOnly: true } },
    ]);
    expect(cookieStore.set).toHaveBeenCalledWith('session', 'new', {
      httpOnly: true,
    });
  });
});
